# Phase 0: Local configuration and database connectivity

Establish the infrastructure for the CLI engine. The initial scope covers configuration and database connectivity; extended work introduces the shared database base and migration management. Conversation and message tables belong to [Phase 1](phase_1.md). Memory behavior and Pydantic data schemas remain outside this phase.

**Status:** configuration and session infrastructure implemented; local checks passed. The shared base, naming conventions, Alembic scaffold, and target metadata wiring are implemented. Alembic database connectivity and migration revisions remain pending. Fresh-volume and application-data persistence checks remain outstanding. See the [Phase 0 log](../logs/phase_0.md).

## Steps

1. [x] Confirm Python compatibility and select SQLAlchemy, Psycopg 3, and Pydantic Settings.
2. [x] Define local environment variables and a safe `.env.example`; exclude credentials from version control.
3. [x] Configure Docker Compose with PostgreSQL/pgvector, a named volume, localhost binding, and a health check.
4. [x] Implement `core/config.py` with Pydantic Settings validation and safe connection URL construction.
5. [x] Implement `db/session.py` with a synchronous engine and session factory.
6. [x] Establish transaction ownership, commit, rollback, session closure, and engine disposal.
7. [x] Verify configuration validation, database connectivity, and pgvector availability.
8. [ ] Verify database startup with a fresh volume; application-data persistence is verified in Phase 1.
9. [x] Add Flake8, strict mypy, pytest, and a PR workflow with required checks on `main`.
10. [x] Record implementation decisions, verification results, and outstanding work.

## Configuration decisions

- Use individual `POSTGRES_*` fields; a full URL override is not supported.
- Construct a SQLAlchemy URL object to preserve credentials containing reserved characters.
- Require a nonempty password and a port between 1 and 65535.
- Load `.env` relative to the working directory; launch from the repository root.
- Create settings and the session manager explicitly when the CLI is implemented; imports do not load configuration or create an engine.
- The connectivity foundation checks pgvector availability; extended migration work will own extension activation.

## Extended work: shared base and migration foundation

`db/base_class.py` defines the single SQLAlchemy declarative base and shared metadata with consistent constraint naming; `db/base.py` explicitly re-exports it and will register application models. It does not define application tables or open database connections.

The shared convention names indexes and unique constraints using every column, and foreign keys using all local columns plus the referenced table and columns. Check constraints require descriptive explicit names. Partial, expression, and alternate indexes on identical columns require explicit names. SQLAlchemy handles deterministic truncation of convention-generated names for PostgreSQL; keep identifiers short and readable rather than relying on truncation for uniqueness.

### Steps

1. [x] Install Alembic and initialize its migration environment.
2. [x] Define the shared base and naming conventions in `db/base_class.py` and export it through `db/base.py`.
3. [x] Configure Alembic to use the shared `Base.metadata`.
4. [ ] Replace Alembic's placeholder connection with application settings loaded when invoked, without committed credentials.
5. [ ] Create and review an explicit initial migration for pgvector extension activation.
6. [ ] Apply that migration to a fresh disposable database and verify the extension and Alembic revision state.
7. [ ] Define and verify supported downgrade/re-upgrade behavior on disposable data, including extension ownership.
8. [ ] Add migration application and revision checks to CI, retaining connectivity and configuration tests.
9. [ ] Record verification results and outstanding work in the implementation log.

### Verification of current implementation

- The base imports without loading application settings; metadata is empty because there are no table models yet.
- Flake8 and strict mypy pass. Pytest reports 11 passed and one database integration test skipped without its test URL.
- Alembic has no revision heads. Its configured URL is still the generated placeholder.
- `alembic current` fails with a placeholder-driver error; database migration connectivity is not configured.
- CI runs lint, type checks, and tests, but does not yet apply migrations or verify database revisions.

### Completion criteria

- A fresh database reaches the Phase 0 migration head and has pgvector enabled.
- The shared base and metadata import without loading configuration or connecting to the database.
- Alembic can use the shared metadata even before application models exist.
- Application startup does not create tables or enable extensions.
- Destructive downgrade operations and extension ownership are documented; a potentially shared extension is not dropped automatically.
- Migration checks, lint, type checking, and tests pass in CI.

Conversation/message models, their registration, and table migrations belong to [Phase 1](phase_1.md). Memory nodes, edges, boxes, embeddings, and Python pgvector integration are deferred beyond the basic chatbot milestone. If the Phase 0 extension revision is retained, table revisions follow it; the chatbot itself does not require vector storage.

### Migration references

- [Alembic tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Alembic autogeneration and its limitations](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)
- [SQLAlchemy declarative mapping](https://docs.sqlalchemy.org/en/20/orm/declarative_config.html)
- [SQLAlchemy constraint naming](https://docs.sqlalchemy.org/en/20/core/constraints.html#configuring-constraint-naming-conventions)
- [pgvector Python integration](https://github.com/pgvector/pgvector-python)
- [PostgreSQL extension management](https://www.postgresql.org/docs/current/sql-createextension.html)

## References

- [Pydantic Settings: environment configuration and validation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [SQLAlchemy: engine configuration](https://docs.sqlalchemy.org/en/20/core/engines.html)
- [SQLAlchemy: Psycopg 3 dialect](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.psycopg)
- [SQLAlchemy: sessions and transaction lifecycle](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)
- [Docker Compose: getting started](https://docs.docker.com/compose/gettingstarted/)
- [Docker Compose: environment variable interpolation](https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/)
- [Docker Compose: health checks and startup readiness](https://docs.docker.com/compose/how-tos/startup-order/)
- [Docker: persistent volumes](https://docs.docker.com/engine/storage/volumes/)
- [pgvector: installation and Docker images](https://github.com/pgvector/pgvector)
- [Flake8 configuration](https://flake8.pycqa.org/en/latest/user/configuration.html)
- [mypy configuration](https://mypy.readthedocs.io/en/stable/config_file.html)
- [Pydantic mypy integration](https://docs.pydantic.dev/latest/integrations/mypy/)
- [pytest configuration](https://docs.pytest.org/en/stable/reference/customize.html)
- [uv in GitHub Actions](https://docs.astral.sh/uv/guides/integration/github/)
- [GitHub required status checks](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
