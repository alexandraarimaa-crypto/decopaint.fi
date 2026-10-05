# AI assistant closed-staging evidence

Date: 2026-08-01
Scope: source-grounded AI assistant research prototype
Production status: unchanged

## Candidate

- Logical branch: `ai/source-grounded-assistant-staging-20260801`.
- Local source:
  `work/decopaint-ai-assistant-staging-20260801`.
- Exact archive:
  `work/decopaint-ai-assistant-staging-20260801.tar.gz`.
- Archive SHA-256:
  `01434a6f325ca9e6418efe9df1d79759ca69e3425b39dad97034fd1f9e677c02`.
- Archive contains only the 17 listed code/data paths plus
  `RELEASE_FILES.txt` and `RELEASE_MANIFEST.sha256`; no AppleDouble,
  `.DS_Store`, `__pycache__` or `.pyc` entries.

## Local test evidence

- Bundled Python syntax compilation: passed.
- `python -m unittest shop.tests_ai_assistant -v`: 5 methods, `OK`.
- `scripts/validate_ai_assistant.py`: static contract passed.
- Knowledge products: 154.
- Acceptance questions: 135 across Finnish, Swedish and English.
- Products without documents: 37.
- Products without usable PDF evidence: 39; the assistant refuses a technical
  answer instead of filling these gaps.
- The browser-visible closed staging hostname currently returns HTTP 403.
- The production homepage remained publicly readable during read-only
  baseline verification; no production file, DB or setting was changed.

## Safety properties

- Route activation requires both `STAGING=True` and
  `AI_ASSISTANT_PROTOTYPE_ENABLED=True`.
- No external language-model or embedding request.
- No API key, chat log, browser storage or Analytics event.
- POST + CSRF, request-size limit, per-session rate limit, `no-store`, CSP and
  `noindex` response headers.
- Required surface/location/humidity/result clarification.
- Source links for supported answers; explicit refusal without PDF evidence.
- High-risk applications are handed to a Deco Paint specialist.
- No access to products/orders/customers databases is required by the engine.

## Pending server gates

Server installation has not been performed because the cPanel session is not
authenticated. After owner login, the following remain mandatory:

1. Record the active staging symlink and hashes of overlapping runtime files.
2. Clone the active staging release to a new immutable release.
3. Verify the uploaded archive and internal manifest before extraction.
4. Enable only the two staging flags; retain isolated SQLite, locmem email,
   Merchant and Analytics kill switches.
5. Run the Django view tests, 135-case validator, isolated full suite and
   `check --deploy` in the staging virtualenv.
6. Run `collectstatic` only for the staging static root.
7. Smoke the prototype internally, then atomically switch the staging symlink.
8. Reconfirm external HTTP 403/noindex and unchanged production health.

Until all eight gates pass, the candidate must not be described as installed
or accepted on staging.

## Rollback

The pre-switch symlink target is the rollback point. Repoint the staging
symlink atomically, restart only staging Passenger, and repeat internal smoke
plus external 403/noindex checks. No database restore or production action is
required.
