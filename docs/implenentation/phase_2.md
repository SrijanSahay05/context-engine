# Phase 2: Synchronous A-Mem note construction, linking, and evolution

Build the first memory-writing pipeline on top of the persisted conversation/message foundation:

**Source message → note enrichment → embedding → candidate retrieval → linking → evolution.**

**Status:** planned; no Phase 2 models, migrations, or services are implemented. Phase 1's CLI error handling, interrupted-turn recovery, context limits, and verification remain open in [its checklist](phase_1.md). Starting this work does not mark Phase 1 complete.

## Scope and baseline

- Process messages synchronously with ordinary Python functions and PostgreSQL/pgvector. Database operations are not agent-controlled tools.
- Do not add an admission classifier. Every source message in the agreed ingestion scope enters note construction; source-role selection and atomic-note boundaries must be defined first.
- Reuse the existing Ollama chat client through memory-specific functions and prompts where practical. Reusing a client does not merge generation stages into one inference call or automatically retain chat state.
- Use a text embedding model separately from the generative LLM. Keep one fixed, recorded candidate limit `k` for the baseline.
- Keep classifier experiments and changes to `k` separate from baseline implementation so their effects can be evaluated independently.
- Defer background workers, STM/LTM tiers, multi-process writers, streaming, explicit box tables, and custom provider abstractions. Background consolidation and an STM/LTM split are project extensions, not requirements established by the A-Mem method.
- Candidate retrieval in this phase supports linking/evolution. Query-time memory retrieval and augmentation of chatbot answers remain a separate follow-up; this phase alone is not a complete A-Mem reproduction or evaluation.

## Paper requirements and project decisions

The source is the [A-Mem paper](../reference_research/A-mem_research_paper.pdf), especially §§3.1–3.4, §4.2, Figure 2, and Appendix B.

| Area | Paper basis | Decision for this implementation |
| --- | --- | --- |
| Note construction | §3.1: original interaction content and timestamp, generated keywords, tags, contextual description, embedding, and links; notes are atomic units. | Preserve original evidence and source references separately from generated attributes. Decide whether one message produces one or multiple atomic notes. |
| Embedding | §3.1, Eq. 3: encode concatenated content, keywords, tags, and contextual description. | Record a stable input composition, model identity, and vector dimension. Re-embed when any included attribute changes. |
| Candidate retrieval | §3.2: cosine similarity identifies top-k nearby memories before link decisions. | Search a defined memory scope, exclude the new note itself, and bound LLM input by the selected neighborhood. |
| Linking | §3.2: the LLM determines meaningful connections among candidates. | Similarity does not automatically create an edge. Direction, uniqueness, deletion behavior, and any stored explanation are schema decisions. |
| Evolution | §3.3: retrieved notes may acquire updated context, keywords, and tags. | Permit validated changes to generated attributes while retaining original content, timestamps, and provenance. Keep embeddings consistent with changed attributes. |
| Model and k | §4.2 reports `all-minilm-l6-v2` embeddings and primarily retrieval `k=10`, with category-specific adjustments. | Select and record the local baseline. A candidate `k=10` is a paper-informed starting choice, not a universal requirement; record model or parameter deviations. |

Chat context may help interpret a source message, but that enrichment input is a project choice to document. Preserve the distinction between the original evidence and interpretations inferred from surrounding context. Assistant-generated content must retain its source role rather than being treated as verified user evidence.

Appendix B is a prompt reference, not a ready-to-execute database contract. Reconcile its action examples with the method before choosing supported evolution actions; do not infer a requirement for destructive merge/prune behavior from example action names alone.

## Planned responsibilities

| Location | Responsibility |
| --- | --- |
| `models/memories.py` (proposed) | Memory-note and edge models using the existing shared base. |
| `db/base.py` | Register the new models for Alembic. |
| `services/memory.py` (proposed) | Coordinate ingestion, candidate retrieval, linking, evolution, and persistence. |
| `llm/local_ollama.py` and memory prompt/schema definitions | Reuse client setup; validate memory-specific LLM responses without writing inference prompts/results into conversation history. |
| Embedding integration (location to decide) | Encode note text and validate vector dimensions and values. |
| `migrations/versions/` | Reviewed memory-table revisions following the current conversation/message head. |
| `tests/` | Deterministic service tests with fake inference/embeddings, plus PostgreSQL vector and transaction checks. |

These paths are a proposed layout, not additional files to create before they are needed. Keep the services as ordinary functions; no agent framework or provider hierarchy is required.

## Decisions before schema implementation

1. [ ] Define the source-message roles, ingestion point, atomic-note boundary, and amount of surrounding context supplied to enrichment. System instructions are not automatically memory facts.
2. [ ] Define source references, original-content retention, source deletion behavior, and how processing the same source again avoids duplicate notes or repeated side effects.
3. [ ] Select the embedding model, dimension, and input composition; record the enrichment model and prompt versions. Do not mix incompatible embedding spaces.
4. [ ] Define candidate memory scope, including whether links may cross conversations; choose a fixed positive `k` and deterministic handling of similarity ties.
5. [ ] Define edge direction, pair uniqueness, self-link policy, valid endpoints, and deletion behavior. Store link explanations only as a documented project choice.
6. [ ] Define which generated attributes evolution may change and the supported actions. Original evidence remains unchanged.
7. [ ] Define failure, rollback, and retry behavior for one ingestion, including reprocessing an already-ingested source. Retain the original chat message even if memory processing fails.

## Implementation steps

1. [ ] Define note and edge models with provenance, generated attributes, embeddings, timestamps, and agreed constraints; register them with the shared metadata.
2. [ ] Add the necessary pgvector Python integration, verify compatibility with the current Python environment, and generate/review/apply migrations against a disposable database.
3. [ ] Define and validate structured enrichment, linking, and evolution outputs using the paper's prompts as references. Reject unsupported actions and invalid target IDs before persistence.
4. [ ] Implement note enrichment from the persisted source and agreed context, without altering existing conversation/message rows.
5. [ ] Implement embeddings over the agreed textual attributes. Reject wrong dimensions, non-finite values, and vectors unsuitable for the chosen similarity operation.
6. [ ] Implement cosine-based candidate retrieval. Verify an empty store, fewer than k notes, self-exclusion, scope isolation, and stable ordering. Exact search is sufficient initially; approximate indexes require a measured need.
7. [ ] Implement LLM-selected links from the candidate set, allowing no links when none are justified. Enforce endpoint and duplicate-edge rules independently of the LLM.
8. [ ] Implement bounded neighbor evolution, including a no-change result. Preserve evidence and recompute embeddings whenever their input changes.
9. [ ] Coordinate the synchronous pipeline with short database transactions and inference outside them. Publish a new note, its links, and neighbor/embedding changes consistently; a failed ingestion must not leave a half-applied graph. Choose the exact commit boundary before wiring the stages together.
10. [ ] Expose a callable ingestion path for persisted messages and a way to inspect notes, edges, and changed attributes. Agree how it connects to the chat flow without presenting memory-processing failures as lost chat messages.
11. [ ] Add unit and PostgreSQL integration tests, then run one explicit real-model smoke check. Record output validity, inference-call counts, stage latency, selected k, model identities, and deviations.
12. [ ] Update implementation status and evidence after the checks pass; leave admission-classifier and k-tuning experiments for the next iteration.

## Verification checklist

- [ ] A fresh migrated database supports note/edge persistence, provenance references, vector storage, uniqueness, deletion, and endpoint constraints.
- [ ] The first note is saved with no candidates; linking and neighbor evolution have no work and do not fail.
- [ ] Candidate ranking is verified with known vectors in PostgreSQL, including fewer-than-k results, self-exclusion, and the agreed conversation scope.
- [ ] LLM decisions can create a valid link or leave the note unlinked; invented IDs, duplicates, self-links, malformed output, and unsupported changes are rejected according to policy.
- [ ] Evolution changes only permitted generated attributes; affected embeddings are refreshed and unchanged notes are not rewritten unnecessarily.
- [ ] Original content, source timestamps, source roles/references, and conversation history survive enrichment and evolution unchanged.
- [ ] Repeating ingestion of the same source follows the agreed retry policy without duplicating graph state.
- [ ] Enrichment, embedding, linking, evolution, and database failures leave the source message intact and no partially committed memory update.
- [ ] Deterministic tests use fake model/encoder outputs; real Ollama and embedding checks are explicit and their configuration is recorded.
- [ ] Lint, type checks, migrations, and relevant tests pass; remaining Phase 1 gaps are still tracked separately.

## Completion criteria

- A persisted source message can pass through the full synchronous pipeline and produce an inspectable enriched note, embedding, valid optional links, and justified optional neighbor changes.
- A later related message demonstrates linking and evolution without overwriting original evidence or leaving stale embeddings.
- Empty-store, no-link, no-evolution, duplicate-ingestion, invalid-output, and rollback paths have verified behavior.
- Inference is separated from database transaction lifetimes, and memory inference does not pollute the saved chat transcript.
- Baseline configuration, prompt choices, deviations from the paper, and verification evidence are recorded. No paper-result reproduction is claimed from a pipeline smoke test.

## References

- [A-Mem paper: §§3.1–3.4, §4.2, Figure 2, and Appendix B](../reference_research/A-mem_research_paper.pdf)
- [Phase 1: conversation persistence and remaining hardening](phase_1.md)
- [SQLAlchemy relationship patterns](https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html)
- [SQLAlchemy constraints](https://docs.sqlalchemy.org/en/20/core/constraints.html)
- [pgvector: querying and vector distances](https://github.com/pgvector/pgvector#querying)
- [pgvector Python: SQLAlchemy integration](https://github.com/pgvector/pgvector-python#sqlalchemy)
- [LangChain ChatOllama integration](https://docs.langchain.com/oss/python/integrations/chat/ollama)
