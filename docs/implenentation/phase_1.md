# Phase 1: Resumable local CLI chatbot

Build a synchronous text chatbot powered by local Ollama models through LangChain. Persist conversations and messages in PostgreSQL and allow a conversation to resume after the CLI exits. Conversation history is the only context mechanism in this milestone; A-Mem nodes, edges, boxes, embeddings, retrieval, and memory evolution are deferred.

**Status:** basic chatbot implemented; Phase 1 hardening and verification remain pending. Models, table migrations, Ollama setup, conversation services, and an interactive CLI are committed. Service tests passed against disposable PostgreSQL before the CLI was added. The latest CLI still needs error handling and updated tests.

The current scope is a single-user CLI with one active writer. Message IDs provide ordering; the earlier per-conversation sequence counter and concurrent-writer coordination are deferred. This is a project simplification, not a claim of concurrent conversation safety.

## File responsibilities

| Location | Responsibility |
| --- | --- |
| `db/base_class.py` | Existing declarative base and naming conventions. |
| `db/base.py` | Existing base export and registration of table models for Alembic. |
| `models/messages.py` | Implemented conversation/message models, constraints, relationships, and deletion behavior. |
| `db/session.py` | Existing session and transaction lifecycle. |
| `llm/local_ollama.py` | Construct the synchronous `ChatOllama` client. |
| `services/conversation.py` | Create/list conversations, build ordered context, invoke the model, and persist exchanges. |
| `main.py` | Interactive new/resume menu, input loop, reply display, and database-manager disposal. |
| `migrations/versions/` | pgvector baseline and conversation/message table revisions. |
| `tests/test_conversation.py` | Input validation and PostgreSQL service persistence/failure checks with Ollama mocked. |
| CLI tests (pending) | The old greeting smoke test was removed in `c904ae7`; interactive CLI coverage has not been added. |

Use the existing shared base. LangChain supplies the chat-model interface; a custom provider base remains deferred. The initial interface uses `input()` and `print()` rather than argparse or a TUI framework. CLI presentation stays in `main.py`; persistence and context construction stay in the service.

## Implemented database models

| Model | Current fields and behavior |
| --- | --- |
| Conversation | Auto-generated integer ID, timezone-aware `created_at`, and `last_activity_at`. |
| Message | Auto-generated integer ID, required conversation foreign key, string role, text content, nullable token count, and timezone-aware `created_at`. |

A conversation has many messages, loaded in ascending message-ID order. Role values are constrained to `system`, `user`, `assistant`, and `tool`; non-null token counts must be nonnegative. A composite index covers `(conversation_id, id)`. Database `ON DELETE CASCADE` removes history when a conversation is deleted; ORM `delete-orphan` also removes messages detached from its collection.

Conversation creation saves the system message atomically with the conversation. Each saved message updates last activity in the same transaction. Titles, per-conversation sequence counters, and persisted provider/model selection are not implemented. The model is currently fixed to `gemma3:1b` with temperature 0 in the Ollama module; changing that configuration also changes the model used for resumed conversations.

## Message ordering and transaction behavior

- Create the conversation and its system message in one transaction.
- Read history by ascending message ID. IDs are global and may have gaps; roles are stored explicitly, not inferred from IDs.
- Save the user message and last activity before invoking Ollama. Build a structured role/content list containing the stored history and new input exactly once.
- Invoke Ollama outside the database session, then save the assistant response and last activity in a separate transaction. Reload the conversation in that second session.
- Return the reply only after its transaction commits. The session manager owns commit, rollback, and closure.
- Reject blank input and unknown conversation IDs. Reject non-string assistant content before opening the response-save transaction.
- Generation or response-save failures retain the committed user message without an assistant row. Explicit recovery when resuming an unanswered turn is still required; currently the CLI does not detect that state.
- Assume one active CLI writer. There is no database ownership lock or overlapping-turn rejection; multi-process coordination and crash-recovery ownership are deferred.

## LangChain and CLI responsibilities

- Implemented: direct synchronous `ChatOllama.invoke()` with complete responses. Agents, tool execution, streaming, and LangGraph remain outside this milestone.
- Implemented: persisted system instructions and ordered role/content history supplied on each request; LangChain does not own database history.
- Implemented: list conversations by descending last activity; select new/resume, accept messages, display saved replies, and exit with `/exit`. The database manager is disposed in `finally`.
- Pending: validate resume selections and handle blank input, unavailable servers, missing models, request/save failures, Ctrl+C, and EOF with clear CLI messages rather than uncaught exceptions.
- Pending: define a conservative input context budget, reserve output space, and explicitly report over-budget history. No sliding window, automatic trimming, or summarization is implemented or required for this milestone.
- Pending: decide how model configuration is preserved across resume. Persisted model selection is absent; the fixed module configuration is the current limitation.

## Implementation steps

1. [x] Configure Alembic connections, the pgvector baseline, and shared model metadata. See [Phase 0](phase_0.md) for remaining infrastructure verification.
2. [x] Define conversation/message models, ID-based ordering, constraints, and cascading deletion for the single-writer scope.
3. [x] Generate and commit the conversation/message migration; local review and application were reported by the owner.
4. [x] Add the fixed-model Ollama client and conversation creation, listing, and send services.
5. [x] Implement the basic new/resume menu and synchronous chat loop.
6. [x] Add focused service tests with mocked Ollama; verify persistence, context ordering/isolation, timestamps, and failure rollback against disposable PostgreSQL.
7. [x] Configure CI to apply migrations, check the revision head, and run lint, type checks, and database tests.
8. [ ] Add direct PostgreSQL constraint and database-cascade checks, and verify fresh-database migration behavior for this branch.
9. [ ] Add CLI validation and error/exit handling, and define/test recovery for unanswered user turns.
10. [ ] Define and test context-budget enforcement and resolve the model-configuration limitation for resume.
11. [ ] Add interactive CLI and conversation-listing tests to replace the removed greeting smoke test, and pass all required checks.
12. [ ] Verify a real Ollama/PostgreSQL create, multi-turn chat, exit, and resume flow across process restarts; record evidence before beginning memory management.

## Verification evidence and limits

- Commit `a2b6ed5` added 11 service test cases: three blank-input unit cases and eight PostgreSQL integration cases with Ollama mocked. Each database case uses an isolated temporary schema and requires `TEST_DATABASE_URL`.
- At that commit, the full suite passed against disposable PostgreSQL: 23 tests passed, with eight unittest subtests. Flake8 and mypy passed. The disposable container was removed afterward; the development database was not used.
- The service tests build tables from model metadata in temporary schemas. They do not verify Alembic migrations, direct database deletion cascading, or every database constraint.
- Subsequent commits added conversation listing and the CLI. Commit `c904ae7` removed the obsolete greeting smoke test without adding CLI coverage; `95e5ea3` applied formatting fixes. Latest local checks pass Flake8 and mypy, with 13 pytest cases passed, nine database cases skipped without `TEST_DATABASE_URL`, and eight unittest subtests passed. This does not replace the earlier database-enabled verification or establish end-to-end CLI behavior.
- Automated service checks do not invoke real Ollama. End-to-end CLI resume, context limits, and incomplete-turn recovery remain unverified.

## Completion criteria

- A fresh database reaches the committed schema using migrations, without startup-time table creation.
- A user can start a local-model conversation, exchange multiple messages, exit, and resume with the same stored system instruction and ID-ordered context.
- The supported execution scope is one active CLI writer; concurrent-process safety is not claimed.
- Recovery behavior for interrupted or failed turns is explicit and tested, without duplicating user messages or inventing replies.
- Model and database failures preserve an honest record of saved messages and are reported clearly in the CLI.
- Model configuration on resume is either preserved or explicitly constrained and documented.
- Context limits are handled explicitly; tests and required CI checks pass.
- Memory-management tables and behavior remain outside this milestone.

## References

- [SQLAlchemy declarative mapping](https://docs.sqlalchemy.org/en/20/orm/declarative_styles.html)
- [SQLAlchemy relationship patterns](https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html)
- [SQLAlchemy foreign keys and constraints](https://docs.sqlalchemy.org/en/20/core/constraints.html)
- [Alembic autogeneration and review](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)
- [LangChain ChatOllama](https://reference.langchain.com/python/langchain-ollama/chat_models/ChatOllama)
- [LangChain messages](https://reference.langchain.com/python/langchain/messages)
- [Ollama API](https://docs.ollama.com/api)
