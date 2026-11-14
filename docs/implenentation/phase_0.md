# Phase 0: Local configuration and database connectivity

Establish the infrastructure for the CLI engine. The initial scope covers configuration and database connectivity; extended work introduces the shared database base and migration management. Application tables belong to [Phase 1](phase_1.md). Memory behavior and Pydantic data schemas remain outside this phase.

**Status:** configuration and session infrastructure implemented; local checks passed. Alembic is installed and its migration scaffold initialized. Database configuration, metadata wiring, and migration revisions remain pending. Fresh-volume and application-data persistence checks remain outstanding. See the [Phase 0 log](../logs/phase_0.md).

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

`db/base.py` belongs to this phase. It defines the single SQLAlchemy declarative base and shared metadata with consistent constraint naming. It does not define application tables or open database connections.

### Steps

1. [x] Install Alembic and initialize its migration environment.
2. [ ] Define the shared declarative base and constraint naming convention in `db/base.py`.
3. [ ] Configure Alembic to load database settings when invoked and use `Base.metadata`, without credentials in committed configuration.
4. [ ] Create and review an explicit initial migration for pgvector extension activation.
5. [ ] Apply that migration to a fresh disposable database and verify the extension and Alembic revision state.
6. [ ] Define and verify supported downgrade/re-upgrade behavior on disposable data, including extension ownership.
7. [ ] Add migration application and revision checks to CI, retaining connectivity and configuration tests.
8. [ ] Record verification results and outstanding work in the implementation log.

### Completion criteria

- A fresh database reaches the Phase 0 migration head and has pgvector enabled.
- The shared base and metadata import without loading configuration or connecting to the database.
- Alembic can use the shared metadata even before application models exist.
- Application startup does not create tables or enable extensions.
- Destructive downgrade operations and extension ownership are documented; a potentially shared extension is not dropped automatically.
- Migration checks, lint, type checking, and tests pass in CI.

The Python pgvector integration, embedding dimensions, application models, model registration, and table migrations belong to [Phase 1](phase_1.md). Table revisions must follow the Phase 0 extension revision.

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
