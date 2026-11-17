import os
from collections.abc import Iterator
from datetime import UTC, datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage
from sqlalchemy import Connection, event, func, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Mapper, Session
from sqlalchemy.schema import CreateSchema, DropSchema

from db.base import Base, Conversation, Message
from db.session import DatabaseSessionManager
from services import conversation as service


@pytest.fixture
def model(monkeypatch: pytest.MonkeyPatch) -> Mock:
    model = Mock(spec=["invoke"])
    monkeypatch.setattr(service, "llm", model)
    return model


@pytest.fixture
def db() -> Iterator[DatabaseSessionManager]:
    database_url = os.environ.get("TEST_DATABASE_URL")
    if database_url is None:
        pytest.skip("Set TEST_DATABASE_URL to run conversation integration tests")
    manager = DatabaseSessionManager(make_url(database_url))
    schema = f"test_conversation_{uuid4().hex}"
    try:
        with manager.engine.begin() as connection:
            connection.execute(CreateSchema(schema))
        manager.engine.update_execution_options(schema_translate_map={None: schema})
        Base.metadata.create_all(manager.engine)
        yield manager
    finally:
        try:
            with manager.engine.begin() as connection:
                connection.execute(DropSchema(schema, cascade=True, if_exists=True))
        finally:
            manager.dispose()


def test_create_conversation_persists_system_message(
    db: DatabaseSessionManager, model: Mock
) -> None:
    conversation_id = service.create_conversation(db)

    with db.session() as session:
        conversation = session.get(Conversation, conversation_id)
        assert conversation is not None
        assert len(conversation.messages) == 1
        message = conversation.messages[0]
        assert message.conversation_id == conversation_id
        assert message.role == "system"
        assert message.content == service.SYSTEM_PROMPT
        assert message.created_at.utcoffset() is not None
        assert conversation.last_activity_at == message.created_at
    model.invoke.assert_not_called()


def test_create_conversation_rolls_back_when_system_insert_fails(
    db: DatabaseSessionManager,
) -> None:
    def reject_message(
        mapper: Mapper[Message], connection: Connection, message: Message
    ) -> None:
        raise RuntimeError("system insert failed")

    event.listen(Message, "before_insert", reject_message)
    try:
        with pytest.raises(RuntimeError, match="system insert failed"):
            service.create_conversation(db)
    finally:
        event.remove(Message, "before_insert", reject_message)

    with db.session() as session:
        assert session.scalar(select(func.count()).select_from(Conversation)) == 0
        assert session.scalar(select(func.count()).select_from(Message)) == 0


@pytest.mark.parametrize("content", ["", " ", "\t\n"])
def test_send_message_rejects_blank_input(content: str, model: Mock) -> None:
    db = Mock(spec=DatabaseSessionManager)
    with pytest.raises(ValueError, match="User message cannot be empty"):
        service.send_message(db, 1, content)
    db.session.assert_not_called()
    model.invoke.assert_not_called()


def test_send_message_rejects_unknown_conversation(
    db: DatabaseSessionManager, model: Mock
) -> None:
    with pytest.raises(ValueError, match="Conversation not found"):
        service.send_message(db, -1, "Hello")
    with db.session() as session:
        assert session.scalar(select(func.count()).select_from(Message)) == 0
    model.invoke.assert_not_called()


@pytest.mark.parametrize("with_usage", [False, True])
def test_send_message_preserves_history_and_saves_response(
    db: DatabaseSessionManager, model: Mock, with_usage: bool
) -> None:
    conversation_id = service.create_conversation(db)
    other_id = service.create_conversation(db)
    with db.session() as session:
        session.add_all(
            [
                Message(
                    conversation_id=conversation_id, role="user", content="Earlier"
                ),
                Message(conversation_id=other_id, role="user", content="Unrelated"),
                Message(
                    conversation_id=conversation_id, role="assistant", content="Reply"
                ),
            ]
        )

    assistant_time = datetime(2031, 1, 1, tzinfo=UTC)

    def timestamp_assistant(
        mapper: Mapper[Message], connection: Connection, message: Message
    ) -> None:
        if message.role == "assistant":
            message.created_at = assistant_time

    def respond(context: list[tuple[str, str]]) -> AIMessage:
        assert context == [
            ("system", service.SYSTEM_PROMPT),
            ("user", "Earlier"),
            ("assistant", "Reply"),
            ("user", "New question"),
        ]
        # A separate connection must see the committed user turn before generation.
        with db.session() as session:
            conversation = session.get(Conversation, conversation_id)
            assert conversation is not None
            user_message = conversation.messages[-1]
            assert user_message.content == "New question"
            assert conversation.last_activity_at == user_message.created_at
        return AIMessage(
            content="New reply",
            usage_metadata=(
                {"input_tokens": 10, "output_tokens": 3, "total_tokens": 13}
                if with_usage
                else None
            ),
        )

    model.invoke.side_effect = respond
    event.listen(Message, "before_insert", timestamp_assistant)
    try:
        assert service.send_message(db, conversation_id, "New question") == "New reply"
    finally:
        event.remove(Message, "before_insert", timestamp_assistant)

    model.invoke.assert_called_once()
    with db.session() as session:
        conversation = session.get(Conversation, conversation_id)
        assert conversation is not None
        assert [m.role for m in conversation.messages] == [
            "system",
            "user",
            "assistant",
            "user",
            "assistant",
        ]
        assistant = conversation.messages[-1]
        assert assistant.content == "New reply"
        assert assistant.tokens == (13 if with_usage else None)
        assert conversation.last_activity_at == assistant.created_at == assistant_time


@pytest.mark.parametrize("failure", ["generation", "content"])
def test_send_message_retains_user_message_when_model_response_fails(
    db: DatabaseSessionManager, model: Mock, failure: str
) -> None:
    conversation_id = service.create_conversation(db)
    if failure == "generation":
        model.invoke.side_effect = RuntimeError("Ollama unavailable")
        expected_error: type[Exception] = RuntimeError
    else:
        model.invoke.return_value = AIMessage(
            content=[{"type": "text", "text": "Unsupported blocks"}]
        )
        expected_error = TypeError

    with pytest.raises(expected_error):
        service.send_message(db, conversation_id, "Keep this question")

    with db.session() as session:
        conversation = session.get(Conversation, conversation_id)
        assert conversation is not None
        assert [m.role for m in conversation.messages] == ["system", "user"]
        assert conversation.messages[-1].content == "Keep this question"
        assert conversation.last_activity_at == conversation.messages[-1].created_at


def test_send_message_rolls_back_assistant_when_commit_fails(
    db: DatabaseSessionManager, model: Mock
) -> None:
    conversation_id = service.create_conversation(db)
    model.invoke.return_value = AIMessage(content="Unsaved reply")
    commits = 0

    def fail_assistant_commit(session: Session) -> None:
        nonlocal commits
        commits += 1
        if commits == 2:
            raise RuntimeError("assistant commit failed")

    event.listen(db._session_factory, "before_commit", fail_assistant_commit)
    try:
        with pytest.raises(RuntimeError, match="assistant commit failed"):
            service.send_message(db, conversation_id, "Keep this question")
    finally:
        event.remove(db._session_factory, "before_commit", fail_assistant_commit)

    with db.session() as session:
        conversation = session.get(Conversation, conversation_id)
        assert conversation is not None
        assert [m.role for m in conversation.messages] == ["system", "user"]
        assert conversation.last_activity_at == conversation.messages[-1].created_at
