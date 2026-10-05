# Source-grounded Finnish search production release — 2026-08-01

## Scope

Install the separately approved closed-staging search candidate in production
without changing the database, catalog content, orders, customers, commerce
rules or external integration settings.

## Baseline

- Homepage, catalog, login, checkout and a real product: HTTP `200`.
- Previous `shop/views.py` SHA-256:
  `016dc46de4973bd76cc816fec535946c164267828d3efb21ad17721857004f28`.
- The six release-added paths did not exist.
- `stderr.log`: 7 482 318 bytes, mtime `1785571570`.

## Candidate and backup

- Accepted archive SHA-256:
  `cb8498edb5b045d4ddda4833c3b63b9b4a30d31b0838c360226673a59071d897`.
- Candidate extracted outside the web root:
  `/home/decpai/release-candidates/search-source-grounded-20260801`.
- All seven manifest entries passed `sha256sum -c`; Python compile succeeded.
- Production backup:
  `/home/decpai/release-backups/search-source-grounded-20260801T093927Z`.
- Backup contains the previous `shop/views.py`, exact candidate archive and
  manifest. Both backup hashes were independently verified.

No DB backup was required because the release contains no migration or DB
write. Existing orders and customer data were not read or copied.

## Deployment

The six new module/test/data files were installed first. `shop/views.py` was
installed last, the production seven-file manifest was checked, and Passenger
was restarted through `tmp/restart.txt`. No dependency install, migration or
collectstatic operation was performed.

## Verification

- Production golden validator: 154 products, 9 queries, unavailable exclusion
  and mislinked-PDF exclusion all `OK`.
- `patterimaali` → Ecosmalto Thermo; `marmoriino` → Marmorino Naturale;
  `PVC pohjamaali` → Aggrappante Ecologico. Antiruggine was absent from the PVC
  response.
- The three search pages and all core pages returned HTTP `200`.
- Manual browser smoke verified the result card, product link, image and price;
  no browser console error appeared.
- Payment creation GET: `405`; unsigned Paytrail success/cancel: `403`/`403`.
- Merchant sync effective flag: `True`; no Merchant request was sent.
- Email backend loaded as `django_q_email.backends.DjangoQBackend`; no message
  was sent.
- GA4 tag and `view_search_results` are present. The search event emits only a
  redacted search term and non-negative result count; synthetic contact data
  became `[redacted]`.
- `manage.py check --deploy` returned no error and the same five established
  production security/legacy warnings.
- `stderr.log` remained exactly 7 482 318 bytes after all checks.

## Rollback

Restore the backed-up `shop/views.py`, remove only the six paths confirmed
absent at baseline, restart Passenger and repeat core-page/search/payment smoke.
No DB, Merchant or Analytics rollback is needed.

## Outcome

Release accepted. Rollback was not triggered. No production DB, order,
customer, price, tax, stock, delivery, payment, Merchant product or GA4 setting
was changed.
