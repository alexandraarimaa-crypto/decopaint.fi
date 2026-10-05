# DecoPaint repository instructions

- Treat this GitHub repository as the only source of truth for application code, tests, documentation, deployment scripts, and controlled source assets.
- Follow `AGENTS.md` and `docs/github-workflow.md` for every task.
- Start every website change from a GitHub issue or an explicitly recorded GitHub task. Link the work item in the pull request.
- Synchronize with the default branch, create a focused feature or fix branch, and never commit or push directly to `main`.
- Keep commits scoped and open a pull request for every change. CI and review must pass before merge.
- Never edit application code directly on the hosting server. Deploy only the exact reviewed Git commit, first to closed staging and then, after separate owner approval, to production.
- Do not change production databases, orders, customers, prices, stock, delivery, Paytrail behavior, or external services without separate owner approval.
- Never commit secrets, credentials, personal data, production databases, media libraries, backups, or runtime logs.
- Add or update tests for behavior changes and update `docs/changelog.md` plus relevant audit, testing, deployment, and rollback documentation.
- Before the first GitHub-driven production release, complete the read-only source comparison required by `docs/recovery-audit-2026-08-20.md`.
- When blocked by missing access, uncertain production state, or a safety boundary, stop and document the blocker in the issue or pull request instead of bypassing GitHub.
