from collections.abc import Sequence
from langchain_core.messages import AIMessage
from llm.local_ollama import llm
from db.session import DatabaseSessionManager
from models.messages import Conversation, Message
from sqlalchemy import select

SYSTEM_PROMPT = (
    "You are a friendly and helpful AI assistant. "
    "Your answers are concise and to the point."
)


def create_conversation(db: DatabaseSessionManager) -> int:
    # 1. Create a conversation obj
    with db.session() as session:
        conversation_obj: Conversation = Conversation()
        session.add(conversation_obj)
        session.flush()
        conversation_obj_id = conversation_obj.id
        system_prompt_message: Message = Message(
            conversation_id=conversation_obj_id,
            role="system",
            content=SYSTEM_PROMPT,
        )
        session.add(system_prompt_message)
        session.flush()
        conversation_obj.last_activity_at = system_prompt_message.created_at

    return conversation_obj_id

def list_conversations(db: DatabaseSessionManager) -> list[tuple[int, str]]:
    with db.session() as session:
        conversations: Sequence[Conversation] = session.execute(
            select(Conversation).order_by(Conversation.last_activity_at.desc())
        ).scalars().all()
    return [(conv.id, str(conv.last_activity_at)) for conv in conversations]

def send_message(
    db: DatabaseSessionManager, conversation_id: int, user_message: str
) -> str:
    if not user_message or user_message.isspace():
        raise ValueError("User message cannot be empty")

    with db.session() as session:

        # 1. Fetch the conversation; report an unknown ID clearly
        conversation: Conversation | None = session.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        ).scalar_one_or_none()
        if not conversation:
            raise ValueError("Conversation not found")

        # 2. Load and Build the context using the messaged in the conversation
        messages: list[Message] = conversation.messages
        context: list[tuple[str, str]] = [
            (message.role, message.content) for message in messages
        ]

        # 3. save the new user message and update last_activity_at in one transaction.
        user_message_obj: Message = Message(
            conversation_id=conversation_id,
            role="user",
            content=user_message,
        )
        session.add(user_message_obj)
        session.flush()
        conversation.last_activity_at = user_message_obj.created_at

    # 4. build the request from the saved history + the user_message,
    # including it exactly once.PendingDeprecationWarning
    context.append(("user", user_message))

    # 5. invoke ollama after closing the database transaction.
    assitant_response: AIMessage = llm.invoke(context)
    if not isinstance(assitant_response.content, str):
        raise TypeError(f"Response not str | got {type(assitant_response.content)}.")

    # 6. Save the assitant response and update last activity in another transaction
    with db.session() as session:
        conversation = session.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        ).scalar_one_or_none()
        if not conversation:
            raise ValueError("Conversation not found")
        assistant_response_obj: Message = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=assitant_response.content,
            tokens=(
                assitant_response.usage_metadata["total_tokens"]
                if assitant_response.usage_metadata
                else None
            ),
        )
        session.add(assistant_response_obj)
        session.flush()
        conversation.last_activity_at = assistant_response_obj.created_at

    # 7. return the response after saving succeeds.
    return assistant_response_obj.content
