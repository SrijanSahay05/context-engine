# Phase 0: Configuration, database sessions, and CI

## Scope and commits

The infrastructure foundation for the CLI engine is implemented. No application tables, migrations, memory operations, or interactive CLI were introduced.

| Commit | Change |
| --- | --- |
| `ff1a0a7` | Runtime dependencies and lockfile. |
| `c4a78c4` | PostgreSQL/pgvector Compose service, environment template, and local credential ignore rules. |
| `70b0aa6` | Validated settings, synchronous session management, and regression tests. |
| `c5b8f4f` | Flake8, strict mypy, pytest, integration check, and GitHub Actions workflow. |

## Decisions and review fixes

- Retained individual connection settings and removed the unused full-URL override.
- Used SQLAlchemy's URL object directly to preserve reserved characters in passwords.
- Added password and port validation; excluded the password from the settings representation.
- Removed module-level settings and session manager instances so imports have no configuration-loading side effects.
- Bound the database port to localhost and retained its named data volume.
- Kept `.env` ignored and `.env.example` tracked with a placeholder password.
- Retained the session manager's commit/rollback/close behavior and explicit engine disposal.
- Removed unused extension-creation paths; future migrations will own extension activation.
- Kept the existing unittest cases compatible with pytest and added a separate read-only database integration test.

## Verification

- Locked dependency synchronization succeeded.
- Flake8 passed.
- Strict mypy passed across application and test files.
- Default pytest run: five tests passed; one database test skipped without `TEST_DATABASE_URL`.
- With the local database configured: all six tests passed.
- Regression checks covered required and nonempty passwords, reserved-character credential preservation, port boundaries, environment loading, and session cleanup after success, operation failure, and commit failure.
- Live queries confirmed connectivity and pgvector availability.
- Container recreation completed successfully with the existing named volume and a healthy localhost-only binding.
- The workflow's action tags were checked against published GitHub tags.

## Merge requirements

Configured GitHub protection for `main` to require a pull request, an up-to-date branch, and the `Quality gate` status check. Administrators are included; additional reviewer approval is not required. These settings live on GitHub, independently of the repository files.

The workflow runs lint, type checks, and pytest with a separate PostgreSQL/pgvector service. It needs no repository database secrets. Hosted execution has not yet been verified; the workflow must first be pushed and run on a pull request or on `main`.

## Remaining work

- Verify startup using an empty database volume.
- Verify persistence of application data across restarts once tables exist.
- Verify transaction rollback against real database writes; current failure-path checks use session mocks.
- Add migrations and extension activation with the first database models.
- Implement CLI startup that constructs settings and the session manager and disposes the engine on exit.
- Implement the independent A-Mem pipeline and its evaluations.
