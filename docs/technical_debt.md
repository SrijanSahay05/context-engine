# Technical debt

## CI-001: Avoid full CI for documentation-only changes

**Status:** deferred.

**Current behavior:** `.github/workflows/ci.yml` filters pull requests and pushes by branch only. Changes limited to `docs/**` or `README.md` still run the full `Quality gate`, including PostgreSQL startup, dependency installation, lint, type checks, migrations, and tests.

**Impact:** unnecessary runner time and slower feedback for documentation edits.

**Follow-up:** detect documentation-only changes and skip expensive checks while still reporting the required `Quality gate` result. Mixed documentation/code changes must retain full CI, and manual dispatch should remain able to run all checks.

**Constraint:** adding workflow-level `paths-ignore` alone can leave the required check pending and block merges. Preserve a reliable required-check result when implementing filtering.

**Acceptance criteria:** documentation-only PRs and pushes avoid the expensive checks, mixed changes run full validation, and documentation-only PRs remain mergeable under the existing protection rules.

Reference: [GitHub workflow filtering and pending required checks](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow).
