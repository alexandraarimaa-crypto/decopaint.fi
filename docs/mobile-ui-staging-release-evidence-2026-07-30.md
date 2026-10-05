# Mobile UI closed-staging release evidence — 2026-07-30

## Outcome

The approved mobile UI candidate is active only on the closed staging release:

`/home/decpai/staging/releases/mobile-ui-20260730`

The staging pointer resolves to that release. Production remains separate at:

`/home/decpai/public_html/deco`

No production file, database, customer/order data, payment configuration,
Merchant Center setting or Analytics configuration was changed.

## Backup and rollback

Previous staging release:

`/home/decpai/staging/releases/ga4-ecommerce-20260730`

Server-side template backup:

`/home/decpai/staging-backups/mobile-ui-20260730/runtime-before.tar.gz`

Backup SHA-256:

`f748376507e50b88a5dcaa7234700a3dbf3e14e5951f260e858ecd3ff4cecbfd5`

Previous staging settings backup:

`/home/decpai/staging-backups/mobile-ui-20260730/settings-before-mobile-static.py`

Rollback:

1. point `/home/decpai/staging/decopaint` back to
   `/home/decpai/staging/releases/ga4-ecommerce-20260730`;
2. touch `/home/decpai/staging/decopaint/tmp/restart.txt`;
3. confirm HTTP 403 and `X-Robots-Tag` on the closed staging domain.

## Artifact integrity

Uploaded mobile candidate SHA-256:

`4d755907b52a7f6ea54fb3b8d8e899eec709b02316176a959a0e1806c2268aed`

All 12 manifest entries matched on the server. macOS metadata sidecars found
in the uploaded transport archive were enumerated and removed from the new
release before activation.

Clean production-ready runtime archive:

`work/decopaint-mobile-ui-production-ready-20260730.tar.gz`

Clean archive SHA-256:

`796a31f40a02ab8ac3a448a451674c6907a148300eabb2e3fc45e0b74080d05c`

The clean archive contains only the 11 runtime template/CSS/JS files and no
`._*` metadata files. A fresh extraction was verified against all 11 runtime
checksums.

Staging configuration patch v4 SHA-256:

`2456e094bb32f153b1532ed9cc163bae6f4bdfd21fcffeb6754f63cbba9b39e4`

## Staging isolation

- external response before activation: HTTP 403;
- external response after activation: HTTP 403;
- `X-Robots-Tag: noindex, nofollow, noarchive` remained present;
- staging database remained
  `/home/decpai/staging-data/decopaint.sqlite3`;
- email backend remained in-memory;
- Merchant sync remained disabled;
- Analytics remained disabled with an empty GA4 measurement ID;
- Paytrail remained configured with disabled staging credentials;
- static files are versioned inside the release at `static/`;
- media remains read-only from the production media origin;
- no production PII was copied to staging.

## Verification

- mobile UI static contract: `MOBILE_UI_STATIC_CHECKS_OK=1`, 11 files;
- manifest verification: 12/12 `OK`;
- Python compile: passed after removal of transport metadata sidecars;
- changed Django templates compiled: 9/9;
- Django staging check: two known baseline warnings only
  (`security.W004` and `auth.W004`);
- isolated test suite: 26 tests, `OK`, run again after final configuration;
- collectstatic: 401 files copied to the versioned release;
- home server-side smoke: HTTP 200;
- home contains the new mobile CSS and JavaScript;
- staging home contains no Google tag loader;
- catalog server-side smoke: HTTP 200;
- checkout server-side smoke with signed-cookie synthetic session: HTTP 200;
- mobile catalog toolbar rendered.

The isolated staging database contains no product records. Product-detail
template compilation passed, but an end-to-end product/cart visual journey
cannot be run against staging without adding synthetic catalog fixtures.
Production catalog data was intentionally not copied.

## Production gate

Production installation is not authorized by this staging approval. A separate,
explicit production approval is required before using the clean runtime archive
on `/home/decpai/public_html/deco`.
