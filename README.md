# Context Engine

A CLI-first research project for reproducing and evaluating agent memory approaches. The first phase implements **A-Mem** and **AgeMem** independently, with a choice of memory approach when starting the CLI engine. A later phase will investigate a hybrid approach after establishing independent baselines.

**Current status:** project scaffold only. Implementation starts with A-Mem; the CLI, database integration, backend selection, and evaluations are planned, not yet available.

## Research references

| Approach | Paper | Main idea |
| --- | --- | --- |
| A-Mem | [A-Mem: Agentic Memory for LLM Agents](docs/reference_research/A-mem_research_paper.pdf) | Atomic memory notes enriched with context, keywords, tags, and embeddings; LLM-driven linking and evolution of related memories. |
| AgeMem | [Agentic Memory: Learning Unified Long-Term and Short-Term Memory Management for Large Language Model Agents](docs/reference_research/AgeMem_research_paper.pdf) | Unified long-term and short-term memory management through agent-controlled tools, learned using progressive reinforcement learning and step-wise GRPO. |

## Phase 1: Independent reproductions through a CLI

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

## Phase 2: Hybrid experiments

After establishing the independent baselines, investigate combining A-Mem's linked, evolving notes with AgeMem's unified memory management. Evaluate whether the hybrid improves on those baselines; its design is intentionally undecided until the independent implementations provide evidence.

## Planned stack

- **Python CLI:** initially using `argparse`.
- **Memory logic:** ordinary Python functions independent of the CLI.
- **Persistence:** SQLAlchemy with synchronous sessions, Psycopg 3, and `pgvector-python`.
- **Database:** PostgreSQL with pgvector, running through Docker Compose with persistent storage.
- **Migrations:** Alembic.

The CLI will call the memory logic directly. FastAPI can be added later when HTTP access is needed, reusing the same functions. An HTTP server and web UI are outside the initial scope.

## Running the current scaffold

The project currently declares Python 3.15 or newer in `pyproject.toml` and has no dependencies configured.

```sh
python main.py
```

This prints a greeting only. Memory commands, Docker configuration, and setup instructions will be added with the implementation.
