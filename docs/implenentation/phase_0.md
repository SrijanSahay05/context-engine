# Phase 0: Local configuration and database connectivity

Establish the infrastructure for the CLI engine. This phase excludes database models, data schemas, migrations, and memory behavior.

## Steps

1. Confirm Python compatibility and select the required dependencies: SQLAlchemy, Psycopg 3, and Pydantic Settings.
2. Define the local environment variables and a safe `.env.example`; exclude local credentials from version control.
3. Set up `docker-compose.yml` for PostgreSQL with pgvector, persistent storage, a local port binding, and a health check.
4. Set up `core/config.py` with Pydantic Settings to load and validate database configuration.
5. Set up `db/session.py` with a synchronous SQLAlchemy engine and session factory.
6. Establish session ownership, transaction boundaries, rollback behavior, and connection cleanup for CLI operations.
7. Verify database connectivity, pgvector availability, configuration validation, and persistence across container restarts.
8. Record the setup requirements and verification results before moving to models and migrations.

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
