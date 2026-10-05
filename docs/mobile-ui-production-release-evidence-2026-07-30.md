# Mobile UI production release evidence — 2026-07-30

## Outcome

The owner explicitly approved the production release after accepting the
prototype and the closed-staging result. The code-only mobile UI candidate was
installed in:

`/home/decpai/public_html/deco`

Release completed at `2026-07-30T20:21:25Z`. No database, migration, order,
customer, price, VAT, stock, delivery, Paytrail callback, Merchant product or
GA4 property setting was changed.

## Artifact integrity

Production artifact:

`work/decopaint-mobile-ui-production-ready-20260730.tar.gz`

SHA-256:

`796a31f40a02ab8ac3a448a451674c6907a148300eabb2e3fc45e0b74080d05c`

The artifact contained exactly the approved 11 runtime files. All 11 candidate
checksums passed before installation and all 11 installed checksums passed
after installation. No `._*` macOS metadata files were present.

An older server-side transport file with the same name initially failed the
artifact SHA check. The first attempt stopped in the pre-install phase and did
not touch production. It was replaced with the exact local artifact, rechecked
on the server, and only then deployed.

## Backup and rollback

Production pre-install backup:

`/home/decpai/release-backups/mobile-ui-20260730T202101Z`

Runtime backup:

`runtime-before.tar.gz`

SHA-256:

`c7c0e5078537f08f8db4b8b307a78d1f168ef194b0055b96e02926843035c5020`

The backup contains the nine templates that existed before the release.
Absence was recorded for both new source static files and both new public
static files. Rollback therefore restores the nine templates, removes those
four newly added static paths, repeats `collectstatic`, and restarts Passenger.
No database restore is required.

## Verification

- pre-release homepage, catalog, empty checkout and terms: HTTP `200`;
- nine changed templates compiled successfully;
- `manage.py check --deploy`: the same five known baseline warnings, no new
  release-specific issue;
- `collectstatic --noinput`: two files copied, 399 unchanged;
- Passenger restarted through `tmp/restart.txt`;
- homepage, catalog, empty checkout, terms and a real product: HTTP `200`;
- public mobile CSS and JavaScript: HTTP `200`, checksums match source;
- homepage references both new public mobile assets;
- real product `/product/210-biofondo-coprente/` contains the new material
  calculator markup and the existing `view_item` event;
- production source contains zero `._*` files in the changed app trees;
- Paytrail payment creation still rejects GET with HTTP `405`;
- unsigned Paytrail success callback still returns HTTP `403`;
- email backend initializes successfully without sending a message;
- Merchant task imports successfully and
  `MERCHANT_SYNC_EFFECTIVE=True`;
- Analytics imports successfully, `ANALYTICS_ENABLED=True`, and a real
  `view_item` payload contains none of the forbidden customer keys
  `email`, `phone`, `address`, `first_name` or `last_name`;
- `stderr.log` grew only during Passenger restart from `7480542` to `7480636`
  bytes and the complete delta contains zero traceback/Internal Server Error
  markers;
- repeat health-check: homepage, catalog, product and empty checkout remained
  HTTP `200`; `stderr.log` stayed at `7480636` bytes;
- Django-Q still exposes five qcluster processes, matching the established one
  master plus four workers baseline.

The production browser smoke confirmed the released homepage and product
render without a server error. The complete phone-specific journeys remain
covered by the approved prototype, the mobile static validator, template
compilation and closed-staging test suite.

## Deferred observation

- Do not create a synthetic production order or payment.
- Confirm the next real order's checkout, email, Paytrail completion,
  `purchase` event and one Merchant sync task using non-PII evidence.
- Check mobile conversion and Core Web Vitals after enough real traffic is
  available; the release does not promise an immediate sales increase.
