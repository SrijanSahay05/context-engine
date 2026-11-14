# Phase 1: A-Mem persistence and message history

Define and migrate the first application tables for A-Mem and conversation history. This is the persistence milestone within the broader Phase 1 research roadmap. LLM-driven extraction, linking, evolution, retrieval orchestration, CLI behavior, and AgeMem implementation are later milestones.

**Status:** planned. Complete the [Phase 0 migration foundation](phase_0.md) first. `db/base.py` and the pgvector extension migration belong to Phase 0; this phase reuses them.

## File responsibilities

| Location | Responsibility |
| --- | --- |
| `db/base.py` | Shared declarative base and naming conventions, established in Phase 0. |
| `db/memory.py` | A-Mem memory nodes, edges, and agreed grouping/provenance tables. |
| `db/messages.py` | Conversation and message table models. |
| `db/session.py` | Existing connection and transaction lifecycle. |
| `migrations/env.py` | Import application models so their tables are registered in the shared metadata. |
| `migrations/versions/` | Reviewed table migrations following the Phase 0 extension revision. |
| `tests/` | Real database constraint, relationship, transaction, and migration checks. |

These are SQLAlchemy table models. Pydantic input/output schemas are separate work and do not create database tables.

## Decisions before defining tables

1. Choose the initial scope boundary: memories may span conversations, so a conversation ID is not automatically the memory scope.
2. Select the embedding model and dimensions; decide whether a newly stored memory can temporarily have no embedding.
3. Define message roles, required content, timestamps, and stable ordering within a conversation.
4. Decide whether a memory may derive from one or several messages and represent that provenance explicitly.
5. Choose whether generic semantic edges are directed or undirected; define duplicate and self-link rules accordingly.
6. Confirm inclusion of explicit boxes and many-to-many memberships from the earlier design, or record their deferral.
7. Define deletion behavior for conversations, messages, source references, memories, and links before choosing cascade rules.

## Planned tables and relationships

| Table | Purpose and relationship |
| --- | --- |
| `conversations` | Identity and metadata for a conversation. |
| `messages` | History entries with a required foreign key to their conversation; ordering is unique within that conversation. |
| `memories` | Atomic notes with original evidence, generated context, keywords, tags, timestamps, and embeddings. |
| `memory_links` | Edges whose two endpoints reference existing memories; preserve the reason for the connection. |
| Source association, if needed | Connect memories to multiple source messages when extraction spans several messages. |
| `boxes`, if included | Explicit groups of related memories. |
| `memory_box_memberships`, if included | Many-to-many membership without automatically linking every pair of members. |

The conversation-to-message relationship is one-to-many. Preserve original message evidence separately from generated memory attributes that may evolve. Avoid making each memory belong to only one conversation if the intended scope spans sessions.

## Implementation steps

1. [ ] Confirm the decisions above and document the agreed initial schema.
2. [ ] Add the Python pgvector integration for SQLAlchemy vector columns.
3. [ ] Define conversations and messages in `db/messages.py`, using the Phase 0 base.
4. [ ] Define memories and links in `db/memory.py`, using that same base.
5. [ ] Define the agreed provenance and optional grouping relationships without additional speculative tables.
6. [ ] Add required foreign keys, uniqueness and check constraints, and indexes for conversation history and edge traversal.
7. [ ] Register every model with Alembic's shared metadata.
8. [ ] Generate and review the table migration after the Phase 0 extension revision, including vector imports and deletion behavior.
9. [ ] Apply the complete migration chain to a fresh disposable database and verify it matches model metadata.
10. [ ] Test valid relationships, rejected invalid references, ordering, duplicate/self-link rules, deletion behavior, and scope boundaries where applicable.
11. [ ] Verify real database commit/rollback behavior and persistence across container restarts using disposable test data.
12. [ ] Verify supported downgrade/re-upgrade behavior, extend CI, and record evidence in the implementation log.

Start with the indexes needed for relational access. Defer approximate vector indexes until retrieval measurements justify them.

## Completion criteria

- A fresh database migrates from the Phase 0 foundation to the application schema without startup-time table creation.
- Messages cannot reference nonexistent conversations, and history has deterministic ordering.
- Edges cannot reference nonexistent memories or violate the chosen duplicate, direction, or self-link rules.
- Provenance and deletion behavior preserve evidence according to the agreed policy.
- Scope boundaries are enforced by database constraints where applicable, not only by ORM relationships.
- Model metadata and migrated schema agree; constraint checks run against PostgreSQL in CI.
- Lint, strict type checking, and all required tests pass.

## References

- [A-Mem paper: note construction, linking, and evolution](../reference_research/A-mem_research_paper.pdf)
- [SQLAlchemy declarative mapping](https://docs.sqlalchemy.org/en/20/orm/declarative_styles.html)
- [SQLAlchemy one-to-many and many-to-many relationships](https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html)
- [SQLAlchemy foreign keys, constraints, and indexes](https://docs.sqlalchemy.org/en/20/core/constraints.html)
- [SQLAlchemy self-referential relationships](https://docs.sqlalchemy.org/en/20/orm/self_referential.html)
- [pgvector Python integration](https://github.com/pgvector/pgvector-python)
- [Alembic autogeneration and review](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)
