# Finnish SEO P0 production release — 2026-08-02

## Outcome

The separately approved R7 Finnish SEO package is live in production. The
release is code-only: no migration, database write, catalog record, order,
customer, price, tax, stock, delivery, Paytrail, Merchant Center or Analytics
configuration was changed. Rollback was not required.

Production root:

`/home/decpai/public_html/deco`

## Release identity

- Closed-staging source:
  `/home/decpai/staging/releases/seo-fi-p0-20260802-r7`.
- Logical branch: `seo/fi-p0-staging-20260802`.
- Source commit: `86859ed`.
- Candidate archive SHA-256:
  `e30f02c2d320d06e057bedff436cbe82b084231af21bf8c4b2681962e98eb760`.
- Manifest SHA-256:
  `2957b04a4c0dceaac8ef45d907df8c9b28101cb13b9f5b759e79e5f99daf715b`.
- Isolated production candidate:
  `/home/decpai/release-candidates/seo-fi-p0-20260802-r7-production`.
- Verified production backup:
  `/home/decpai/release-backups/seo-fi-p0-20260802T171107Z`.
- Previous-files archive SHA-256:
  `5f50a82871e8ffec627b14a4b7b2cb201adf5ad2285d51bfac831dcf9fc79c03`.

The backup directory is mode `0700`; its archive, manifest, baseline hashes
and absent-path record are mode `0600`. The archive passed `gzip -t` and
contains exactly the nine paths that existed before the release. The three
new paths are recorded separately.

## Baseline

- Production source size: 75 MB; free disk space: 221 GB.
- Homepage, catalog, search, a real product, empty checkout and login returned
  HTTP `200`.
- `/catalog/ulkomaalit/` returned HTTP `404` before the release.
- Active `stderr.log`: 7,483,391 bytes.
- The three new paths `shop/seo.py`, `shop/tests_seo.py` and
  `scripts/validate_seo_p0.py` were absent.
- The nine previous runtime/template hashes were saved in
  `production-before.sha256` and rechecked immediately before installation.

## Preflight

The production tree was cloned outside the webroot and overlaid with the R7
archive. Before any production file was changed:

- all 12 candidate manifest entries passed;
- no AppleDouble path was present;
- changed Python modules compiled;
- the static SEO validator returned `SEO P0 static validation: OK`;
- ten metadata/template unit tests passed without database setup;
- six changed templates compiled;
- real-catalog read-only renders returned `200` for homepage, catalog, search,
  the virtual exterior category and Marmorino Naturale;
- `manage.py check --deploy` reported only the five established production
  warnings: HSTS, application-level SSL redirect, secure session cookie,
  secure CSRF cookie and legacy non-unique email username.

The production clone intentionally does not contain the staging-only
`config.test_settings` module. The first runner invocation therefore stopped
before tests started. The SimpleTestCase suite was rerun directly with the
normal production settings and an in-memory `testserver` ALLOWED_HOSTS
override; all ten tests passed and no test database was created.

## Deployment

The 12 files were installed in small batches: support/test files, sitemap and
URL routing, six templates, then `shop/views.py` last. Every batch was checked
against its accepted SHA-256 values. The complete 12-file manifest passed
before Passenger was restarted through `tmp/restart.txt`.

All installed paths are owned by `decpai:decpai` with mode `0644`. No
dependency install, migration or `collectstatic` operation was required.

## Production verification

- Homepage, catalog, search, `/catalog/ulkomaalit/`, Marmorino Naturale,
  checkout, login and sitemap: HTTP `200`.
- Four duplicate tag URLs: permanent `301` to their canonical category URLs.
- Homepage, catalog, exterior category and product expose Finnish language,
  page-specific title, description, H1, `index,follow` and clean self-canonical.
- Product canonical removes tracking, pagination and option parameters.
- Internal search exposes `noindex,follow`, clean canonical and the verified
  `Patterimaali Ecosmalto Thermo` result.
- Sitemap contains 247 URLs, includes `/catalog/ulkomaalit/` and excludes
  internal search.
- Browser console errors: zero.
- Payment-create GET: `405`; unsigned Paytrail success/cancel: `403`/`403`.
- Merchant task and Analytics modules import; effective
  `MERCHANT_SYNC_ENABLED=True`; no Merchant request was sent.
- Mail backend initializes as `django_q_email.backends.DjangoQBackend`; no
  message was sent.
- The real product page contains one GA4 `view_item`, one gtag loader,
  `currency=EUR` and none of the forbidden keys `email`, `phone`, `address`,
  `first_name` or `last_name`.
- `stderr.log` changed from 7,483,391 to 7,483,667 bytes during restart and
  stayed stable on the repeat health check. The 276-byte delta contains zero
  `Traceback`, `Internal Server Error`, syntax/module error or PII marker.
- Repeat homepage, catalog, product and checkout smoke remained HTTP `200`.

No synthetic production order, payment, email or external synchronization was
created.

## Known follow-up

The visible SEO metadata and canonicals are complete. Browser verification
also confirmed that the existing child-template Open Graph and Product
JSON-LD blocks are not emitted by the base template. This was already listed
in the SEO audit and was not repaired directly in production because it needs
its own closed-staging patch and verification that the Offer price and
availability match the visible page and Merchant feed. The R7 release did not
remove or regress any previously rendered Open Graph or JSON-LD output.

## Rollback

Restore the nine previous files from
`production-files-before.tar.gz`, remove only the three paths recorded in
`new-paths-absent.txt`, verify the saved pre-release hashes, touch
`tmp/restart.txt`, and repeat homepage/catalog/search/product/checkout,
Paytrail and error-log smoke. A database or external-integration rollback must
not be performed because the release did not change those systems.
