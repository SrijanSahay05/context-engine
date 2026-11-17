# Context Engine

A CLI-first research project for reproducing and evaluating agent memory approaches. First establish a resumable local chatbot, then implement **A-Mem** and **AgeMem** independently with a choice of memory approach. Later work will investigate a hybrid approach after establishing independent baselines.

**Current status:** database configuration, sessions, shared metadata, Alembic migrations, conversation/message models, Ollama integration, and the basic interactive chatbot are implemented. Phase 1 still needs CLI error handling, interrupted-turn recovery, context-budget enforcement, and further verification. Memory management is not implemented yet.

See the [Phase 0 infrastructure and migration checklist](docs/implenentation/phase_0.md), [Phase 1 chatbot plan](docs/implenentation/phase_1.md), and [implementation logs](docs/logs/README.md) for scope, decisions, and verification results.

## Research references

| Approach | Paper | Main idea |
| --- | --- | --- |
| A-Mem | [A-Mem: Agentic Memory for LLM Agents](docs/reference_research/A-mem_research_paper.pdf) | Atomic memory notes enriched with context, keywords, tags, and embeddings; LLM-driven linking and evolution of related memories. |
| AgeMem | [Agentic Memory: Learning Unified Long-Term and Short-Term Memory Management for Large Language Model Agents](docs/reference_research/AgeMem_research_paper.pdf) | Unified long-term and short-term memory management through agent-controlled tools, learned using progressive reinforcement learning and step-wise GRPO. |

## Phase 1: Resumable local CLI chatbot

The synchronous chatbot uses local Ollama models through LangChain. It supports new conversations and listing/resuming existing ones, storing the system instruction and messages in PostgreSQL. History is ordered by auto-generated message ID; there is no per-conversation sequence counter. Model calls run outside database transactions, and each saved message updates conversation activity.

The supported scope is one active CLI writer. Interrupted-turn recovery and context limits remain pending; concurrent writers are not coordinated. A-Mem nodes, edges, boxes, embeddings, and custom provider abstractions are deferred.

## Subsequent work: Independent memory reproductions

Implement and evaluate each paper's approach separately. At CLI startup, users will choose the memory approach for that session. Initially, only A-Mem will be available; AgeMem becomes selectable once implemented.

### First: A-Mem

- Construct atomic notes from interactions, retaining the source content and timestamp alongside generated context, keywords, and tags.
- Embed the notes and retrieve candidate neighbors by semantic similarity.
- Use an LLM to establish meaningful links and evolve related notes as new information arrives.
- Retrieve relevant notes and linked context for subsequent interactions.
- Expose ingestion, querying, and inspection of notes, links, and groups through the CLI.

The planned PostgreSQL model contains:

| Table | Purpose |
| --- | --- |
| `memories` | Memory nodes, source references, generated attributes, timestamps, and embeddings. |
| `memory_links` | Connections between individual notes, with the reason for each connection. |
| `boxes` | Named groups of related memories. |
| `memory_box_memberships` | Many-to-many membership: a note may belong to several boxes. |

Explicit box records are a project implementation choice for the paper's conceptual grouping. Membership does not automatically create links between every pair of notes. Preserve original evidence when evolving generated interpretations, and recompute embeddings when their input attributes change.

### Next: AgeMem

Implement AgeMem independently, including its long-term memory operations and short-term context management. Its learned memory policy and training procedure are part of the reproduction scope: implementing memory tools alone does not reproduce its reported findings.

### Evaluation

Reproduce each paper's findings using its documented datasets, metrics, model configurations, and experimental procedures where feasible. Record deviations, resource constraints, and results explicitly. Keep independent memory stores and configurations for the two approaches so their behavior can be inspected and evaluated separately.

Any cross-approach comparison should also use a shared evaluation setup with controlled model choices, inputs, and budgets. No reproduction results are available yet.

## Later work: Hybrid experiments

After establishing the independent baselines, investigate combining A-Mem's linked, evolving notes with AgeMem's unified memory management. Evaluate whether the hybrid improves on those baselines; its design is intentionally undecided until the independent implementations provide evidence.

## Planned stack

- **Python CLI:** interactive `input()`/`print()` menu and chat loop.
- **Memory logic:** ordinary Python functions independent of the CLI.
- **Persistence:** SQLAlchemy with synchronous sessions and Psycopg 3; `pgvector-python` is planned for memory work.
- **Database:** PostgreSQL with pgvector, running through Docker Compose with persistent storage.
- **Migrations:** Alembic.

The CLI will call the memory logic directly. FastAPI can be added later when HTTP access is needed, reusing the same functions. An HTTP server and web UI are outside the initial scope.

## Running the chatbot

The project requires Python 3.15 or newer and uses uv with a committed dependency lockfile. Runtime dependencies include LangChain with Ollama support, SQLAlchemy, Psycopg 3, and Pydantic Settings. Development dependencies include Alembic, Black, Flake8, mypy, and pytest.

From the repository root, copy `.env.example` to `.env` and set a local database password. Configuration uses the individual `POSTGRES_*` values; a `DATABASE_URL` override is not supported. Local `.env` files are ignored. Install Ollama and start its local server, then prepare the database and model:

```sh
uv sync --locked
docker compose up -d
uv run --no-sync alembic upgrade head
ollama pull gemma3:1b
uv run --no-sync main.py
```

The menu offers a new conversation or a list of conversations to resume. Enter `/exit` to leave the chat. The model is currently fixed to `gemma3:1b` with temperature 0 in `llm/local_ollama.py`; its selection is not stored per conversation. Invalid input and model/database failures can still terminate the CLI with an exception.

The database uses `docker-compose.yml`, is published on localhost, and retains data in a named volume. Alembic activates pgvector and creates application tables; application startup does not create the schema. Dropping a conversation deletes its history through a database cascade.

## Development checks

```sh
uv sync --locked
uv run --no-sync flake8 .
uv run --no-sync mypy
uv run --no-sync pytest
```

Database integration tests require `TEST_DATABASE_URL` pointing to a test PostgreSQL database with pgvector available. The connectivity test uses read-only queries; conversation service tests create and remove isolated temporary schemas and require schema-creation privileges. Ollama is mocked in service tests. Database cases skip when the variable is absent; unit tests do not require a running database. CLI and conversation-listing tests remain pending.

[CI](.github/workflows/ci.yml) runs on pull requests targeting `main`, pushes to `main`, and manual dispatch. Its `Quality gate` job runs lint, strict type checking, migration application and revision checks, and tests with a separate PostgreSQL/pgvector service and test credentials.

GitHub branch protection requires pull requests, an up-to-date branch, and a passing `Quality gate` before merging to `main`, including for administrators. No approving review is required. This repository setting is managed on GitHub separately from the workflow file. The workflow must be pushed with the branch before its check can run.
