# Contributing

1. Start from the current default branch and create a focused feature branch.
2. Keep secrets, production data, media exports, logs, and backups out of Git.
3. Add or update tests for behavioral changes.
4. Update `docs/changelog.md` and the relevant release or audit document.
5. Open a pull request and complete the security, privacy, checkout, Merchant,
   analytics, staging, backup, and rollback checks that apply.
6. Merge only after review and green CI.
7. Deploy the merged commit to closed staging before any production release.

Production database, Paytrail, order-state, delivery, price, stock, or customer
changes require explicit approval under `AGENTS.md`.
