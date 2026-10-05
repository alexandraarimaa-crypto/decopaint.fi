# GitHub-first workflow

## Source of truth

GitHub is the source of truth for application code, source assets, tests,
deployment scripts, controlled content exports, and documentation. The hosting
server must not receive an uncommitted code edit. Production databases, media,
secrets, and runtime logs stay outside GitHub.

The repository includes a GitHub Copilot custom agent at
`.github/agents/decopaint-github.agent.md`. Repository-wide automation also
reads `.github/copilot-instructions.md` and `AGENTS.md`, so the GitHub-first
rules apply even when the custom agent is not selected explicitly.

## Change flow

1. Create an issue describing the problem, expected result, and risk.
2. Create a branch such as `fix/cart-route` or `feat/merchant-sync`.
3. Implement the smallest coherent change with tests and documentation.
4. Push the branch and open a pull request.
5. Pass CI, review the diff, and complete the pull-request checklist.
6. Merge the reviewed pull request.
7. Deploy that exact merge commit to closed staging.
8. Record staging evidence, backup identity, rollback command, and approval.
9. Deploy the same commit to production and perform smoke checks.
10. Tag the release and update the changelog.

## Content and external systems

CMS content should be exported to `content/` before or immediately after an
approved publication. Google Ads, Merchant Center, Analytics, Paytrail, and
hosting changes must be recorded in the relevant dated document because those
systems are not fully represented by Git commits.

## Repository protections

- Keep the repository private.
- Require a pull request before merging to the default branch.
- Require the CI workflow to pass.
- Block force pushes and branch deletion on the default branch.
- Enable secret scanning and push protection.
- Use repository/environment secrets only for CI; never commit credentials.
- Do not configure automatic production deployment until staging and rollback
  are reproducible from GitHub.
