# Phase 1: Resumable local CLI chatbot

Build a synchronous text chatbot powered by local Ollama models through LangChain. Persist conversations and messages in PostgreSQL and allow a conversation to resume after the CLI exits. Conversation history is the only context mechanism in this milestone; A-Mem nodes, edges, boxes, embeddings, retrieval, and memory evolution are deferred.

**Status:** planned. The shared SQLAlchemy base and metadata wiring are implemented. Alembic database connectivity and migration verification still need completion in [Phase 0](phase_0.md).

## File responsibilities

| Location | Responsibility |
| --- | --- |
| `db/base_class.py` | Existing declarative base and naming conventions. |
| `db/base.py` | Existing base export and registration of table models for Alembic. |
| `models/messages.py` | Conversation and message SQLAlchemy models, following the latest proposed layout. |
| `db/session.py` | Existing session and transaction lifecycle. |
| `llm/ollama.py` | Construct and invoke LangChain's ChatOllama integration. |
| CLI entry point | Select a new or existing conversation, accept input, and display responses. |
| `migrations/versions/` | Reviewed conversation/message table revisions. |
| `tests/` | Constraints, message ordering, migration, failure-path, and resume checks. |

Use the existing shared base; do not introduce a second base under `models/`. LangChain already supplies a common chat-model interface. Defer a custom `llm/base_provider.py` abstraction until a second provider establishes the required contract. Initially select an Ollama model rather than showing a provider menu with only one option.

## Initial database models

| Model | Required responsibilities |
| --- | --- |
| Conversation | Identity, optional title, selected provider/model, creation timestamp, and a persisted `next_message_index` counter. |
| Message | Identity, required conversation foreign key, role, text content, `sequence_number`, and creation timestamp. |

A conversation has many messages. Keep the model selection fixed within a conversation initially. Define explicit conversation-deletion behavior before applying migrations. The selected system prompt is stored as a message so resuming preserves it.

## Message ordering and transaction rules

- Store the counter on each conversation row, not in process memory. It is independent for every conversation and survives restarts.
- Create the conversation and system message at index 0 atomically, leaving `next_message_index` at 1.
- For each append, lock the conversation row, take its next index, insert the message, and increment the counter in one short transaction. Rollback must undo both the insertion and counter change.
- Enforce a unique constraint on `(conversation_id, sequence_number)`, nonnegative indices, and valid roles. Index 0 is reserved for the system message; later messages use user or assistant roles.
- Read history ordered by `sequence_number`; do not derive order from timestamps or use an unlocked maximum-index query.
- The successful sequential flow is system 0, user 1, assistant 2, user 3, assistant 4. Persist the role explicitly; do not infer it from odd/even indices or require gap-free history after future deletion policies.
- Commit the user message before invoking Ollama. Persist a completed assistant response in a separate transaction afterward. Do not hold a database transaction or row lock while waiting for generation.
- Allow one in-flight turn per conversation. Counter locking protects index allocation, not the entire user/assistant exchange. Reject overlapping turns, including attempts from another CLI process, before invoking the model; choose a conversation-ownership mechanism that does not require an open transaction during generation.
- If generation fails or the process exits after saving the user message, retain that message and report the incomplete turn. Resuming must resolve it explicitly, for example by retrying that turn or starting another conversation; do not fabricate an assistant message or silently resend the user input as a second row.
- Decide ownership recovery after a crashed process before claiming concurrent CLI resume support. Do not reserve assistant indices ahead of generation in this first version.

## LangChain and CLI responsibilities

- Use the `langchain-ollama` integration and a direct synchronous model invocation; agents, tools, and LangGraph are outside scope.
- Convert stored system/user/assistant messages into LangChain's message representation when constructing a request. LangChain does not own the database history.
- For a new conversation, choose an available local model and persist the system instruction and model selection.
- For resume, load the selected conversation and its ordered history, reuse its model, and include that history in subsequent requests.
- Define a conservative context budget for the chosen model, reserve output space, and report an over-budget conversation clearly. Do not silently drop saved history; automatic summarization is deferred.
- Handle unavailable Ollama servers, missing models, failed requests, blank input, interruption, and normal exit. Start with complete responses rather than streaming.
- Display successful replies only after their persistence succeeds. If generation succeeds but saving fails, report that the reply was not recorded.

## Implementation steps

1. [ ] Finish Phase 0 Alembic connection configuration and the agreed extension baseline.
2. [ ] Define conversation/message models and decide deletion, ordering, ownership, and incomplete-turn recovery policies.
3. [ ] Register the models with the shared metadata; generate, review, and apply their migration to a disposable database.
4. [ ] Verify foreign keys, roles, system index, uniqueness, atomic counter allocation, rollback, and independent conversation counters against PostgreSQL.
5. [ ] Add LangChain's Ollama integration and configure the local endpoint and model selection.
6. [ ] Verify one successful text request without persistence or CLI orchestration first.
7. [ ] Implement the synchronous new-conversation chat loop with persisted exchanges.
8. [ ] Implement listing/resuming conversations with history replay and incomplete-turn handling.
9. [ ] Verify overlapping-turn rejection, context-limit behavior, request/save failures, and restart persistence.
10. [ ] Extend CI with migration and database behavior checks; use a fake model for deterministic chat tests and keep real Ollama checks explicit.
11. [ ] Record verification evidence and limitations before beginning memory management work.

## Completion criteria

- A fresh database reaches the committed schema using migrations, without startup-time table creation.
- A user can start a local-model conversation, exchange multiple messages, exit, and resume with the same system instruction and ordered context.
- Concurrent index allocations cannot produce duplicates, and failed transactions cannot advance the counter without inserting the corresponding message.
- A conversation cannot run overlapping generations; recovery behavior for interrupted turns is defined and tested.
- Model and database failures preserve an honest record of which messages were saved.
- Context limits are handled explicitly; tests and required CI checks pass.
- Memory-management tables and behavior remain outside this milestone.

## References

- [SQLAlchemy declarative mapping](https://docs.sqlalchemy.org/en/20/orm/declarative_styles.html)
- [SQLAlchemy relationship patterns](https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html)
- [SQLAlchemy foreign keys and constraints](https://docs.sqlalchemy.org/en/20/core/constraints.html)
- [PostgreSQL row-level locks](https://www.postgresql.org/docs/current/explicit-locking.html#LOCKING-ROWS)
- [Alembic autogeneration and review](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)
- [LangChain ChatOllama](https://reference.langchain.com/python/langchain-ollama/chat_models/ChatOllama)
- [LangChain messages](https://reference.langchain.com/python/langchain/messages)
- [Ollama API](https://docs.ollama.com/api)
