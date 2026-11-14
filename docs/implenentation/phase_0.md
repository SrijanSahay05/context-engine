# Phase 0: Local configuration and database connectivity

Establish the infrastructure for the CLI engine. This phase excludes database models, data schemas, migrations, and memory behavior.

**Status:** configuration and session infrastructure implemented; local checks passed. Fresh-volume and application-data persistence checks remain outstanding. See the [Phase 0 log](../logs/phase_0.md).

## Steps

1. [x] Confirm Python compatibility and select SQLAlchemy, Psycopg 3, and Pydantic Settings.
2. [x] Define local environment variables and a safe `.env.example`; exclude credentials from version control.
3. [x] Configure Docker Compose with PostgreSQL/pgvector, a named volume, localhost binding, and a health check.
4. [x] Implement `core/config.py` with Pydantic Settings validation and safe connection URL construction.
5. [x] Implement `db/session.py` with a synchronous engine and session factory.
6. [x] Establish transaction ownership, commit, rollback, session closure, and engine disposal.
7. [x] Verify configuration validation, database connectivity, and pgvector availability.
8. [ ] Verify startup with a fresh volume and persistence of application data across restarts.
9. [x] Add Flake8, strict mypy, pytest, and a PR workflow with required checks on `main`.
10. [x] Record implementation decisions, verification results, and outstanding work.

## Configuration decisions

- Use individual `POSTGRES_*` fields; a full URL override is not supported.
- Construct a SQLAlchemy URL object to preserve credentials containing reserved characters.
- Require a nonempty password and a port between 1 and 65535.
- Load `.env` relative to the working directory; launch from the repository root.
- Create settings and the session manager explicitly when the CLI is implemented; imports do not load configuration or create an engine.
- Defer pgvector extension activation to migrations. Phase 0 checks availability only.

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
