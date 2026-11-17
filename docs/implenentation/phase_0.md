# Phase 0: Local configuration and database connectivity

Establish the infrastructure for the CLI engine. The initial scope covers configuration and database connectivity; extended work introduces the shared database base and migration management. Conversation and message tables belong to [Phase 1](phase_1.md). Memory behavior and Pydantic data schemas remain outside this phase.

**Status:** configuration, sessions, shared metadata, Alembic database connectivity, and the pgvector baseline are implemented. CI applies migrations and checks the revision head. Fresh-volume lifecycle and downgrade/re-upgrade verification remain outstanding; application-data persistence across restarts belongs to Phase 1. See the [Phase 0 log](../logs/phase_0.md).

## Steps

1. [x] Confirm Python compatibility and select SQLAlchemy, Psycopg 3, and Pydantic Settings.
2. [x] Define local environment variables and a safe `.env.example`; exclude credentials from version control.
3. [x] Configure Docker Compose with PostgreSQL/pgvector, a named volume, localhost binding, and a health check.
4. [x] Implement `core/config.py` with Pydantic Settings validation and safe connection URL construction.
5. [x] Implement `db/session.py` with a synchronous engine and session factory.
6. [x] Establish transaction ownership, commit, rollback, session closure, and engine disposal.
7. [x] Verify configuration validation, database connectivity, and pgvector availability.
8. [ ] Verify database startup with a fresh volume; application-data persistence checks are tracked in Phase 1.
9. [x] Add Flake8, strict mypy, pytest, and a PR workflow with required checks on `main`.
10. [x] Record implementation decisions, verification results, and outstanding work.

## Configuration decisions

- Use individual `POSTGRES_*` fields; a full URL override is not supported.
- Construct a SQLAlchemy URL object to preserve credentials containing reserved characters.
- Require a nonempty password and a port between 1 and 65535.
- Load `.env` relative to the working directory; launch from the repository root.
- The CLI creates settings and the session manager explicitly and disposes the manager on exit. Importing the shared base and models does not load database settings or create an engine.
- The connectivity test checks pgvector availability; the baseline migration owns extension activation.

## Extended work: shared base and migration foundation

`db/base_class.py` defines the single SQLAlchemy declarative base and shared metadata with consistent constraint naming. `db/base.py` re-exports it and registers the Phase 1 conversation/message models for Alembic. The base module does not open database connections.

The shared convention names indexes and unique constraints using every column, and foreign keys using all local columns plus the referenced table and columns. Check constraints require descriptive explicit names. Partial, expression, and alternate indexes on identical columns require explicit names. SQLAlchemy handles deterministic truncation of convention-generated names for PostgreSQL; keep identifiers short and readable rather than relying on truncation for uniqueness.

### Steps

1. [x] Install Alembic and initialize its migration environment.
2. [x] Define the shared base and naming conventions in `db/base_class.py` and export it through `db/base.py`.
3. [x] Configure Alembic to use the shared `Base.metadata`.
4. [x] Replace Alembic's placeholder connection with application settings loaded when invoked, without committed credentials.
5. [x] Create an explicit initial migration for pgvector extension activation.
6. [ ] Apply that migration to a fresh disposable database and verify the extension and Alembic revision state.
7. [ ] Define and verify supported downgrade/re-upgrade behavior on disposable data, including extension ownership.
8. [x] Add migration application and revision checks to CI, retaining connectivity and configuration tests.
9. [x] Record verification results and outstanding work in the implementation log.

### Verification of current implementation

- Shared metadata registers the conversation and message tables without loading database settings or connecting to PostgreSQL.
- Alembic loads `Settings().database_url`; the generated URL placeholder in `alembic.ini` is not used by the migration environment.
- Baseline revision `b8b64b6ebec5` enables pgvector. Phase 1 table revision `efb111231d7a` follows it and is the current head.
- CI applies migrations, checks the revision head, and runs lint, type checks, and tests. Configuration of those checks is not evidence of a particular hosted run passing.
- Latest local checks report Flake8 and mypy passing, with 13 pytest cases passed and nine database cases skipped without `TEST_DATABASE_URL`. Earlier service integration checks against disposable PostgreSQL are recorded in [Phase 1](phase_1.md).
- Fresh-volume lifecycle, migration downgrade/re-upgrade, and application-data restart checks have not been verified in this documentation refresh.

The baseline downgrade intentionally leaves pgvector installed to avoid removing a potentially shared extension. The Phase 1 table downgrade drops conversation/message data; supported downgrade/re-upgrade behavior still needs verification on disposable data.

### Completion criteria

- A fresh database reaches the Phase 0 migration head and has pgvector enabled.
- The shared base and metadata import without loading configuration or connecting to the database.
- Alembic can use the shared metadata even before application models exist.
- Application startup does not create tables or enable extensions.
- Destructive downgrade operations and extension ownership are documented; a potentially shared extension is not dropped automatically.
- Migration checks, lint, type checking, and tests pass in CI.

Conversation/message models, their registration, and table migrations are implemented in [Phase 1](phase_1.md). Memory nodes, edges, boxes, embeddings, and Python pgvector integration remain deferred. The chatbot itself does not require vector storage, though its table migration follows the pgvector baseline.

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
