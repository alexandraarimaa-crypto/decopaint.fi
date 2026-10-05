# Finnish SEO P0 closed-staging release — 2026-08-02

## Result

The approved first Finnish SEO package is active only on the closed staging
application. Production was not deployed or modified.

- Active staging release:
  `/home/decpai/staging/releases/seo-fi-p0-20260802-r7`
- Previous stable staging release retained for immediate rollback:
  `/home/decpai/staging/releases/mobile-info-cards-20260801-r7-equal-height`
- Branch: `seo/fi-p0-staging-20260802`
- Final commit: `86859ed`
- No migrations, database writes, product changes, price/stock changes,
  Merchant mutations, Analytics configuration writes or production restart.

## Baseline and scope

Before implementation, production homepage and catalog returned HTTP 200. The
five selected P0 product URLs and four existing category URLs also returned
HTTP 200. `/catalog/ulkomaalit/` returned 404 and is therefore supplied as a
code-only tag-backed landing page in the candidate. The staging database is
intentionally empty; no production products or PII were copied into it.

The previous staging release was recorded before every switch. External
staging remained closed and non-indexable throughout the work.

## Implemented P0 changes

- Central Finnish SEO metadata for homepage, catalog, 11 priority category or
  landing-page intents and five source-grounded product pages.
- Correct Finnish document language, unique title/description fields and
  page-specific H1 contracts.
- Clean self-canonical URLs that remove tracking, filter and product-option
  parameters while preserving approved pagination.
- `noindex,follow` for internal search results.
- Canonical 301 redirects from four duplicate tag URLs to the stronger category
  or landing-page URLs.
- Code-only `/catalog/ulkomaalit/` landing page backed by the existing verified
  `ulkomaalit` tag; no category row or other database change.
- Virtual landing page included in the sitemap.
- Homepage internal links updated to the canonical category URLs.
- Product Open Graph URL and metadata aligned with the canonical URL; duplicate
  invalid Open Graph markup removed.
- Heading hierarchy corrected in the affected catalog templates.
- No unverified technical properties were added.

## Artifact integrity

- Archive:
  `work/decopaint-seo-fi-p0-20260802-r7.tar.gz`
- Archive SHA-256:
  `e30f02c2d320d06e057bedff436cbe82b084231af21bf8c4b2681962e98eb760`
- Manifest:
  `work/decopaint-seo-fi-p0-20260802-r7.manifest.sha256`
- Manifest SHA-256:
  `2957b04a4c0dceaac8ef45d907df8c9b28101cb13b9f5b759e79e5f99daf715b`

The archive was unpacked locally and on the server. All 12 internal file hashes
matched the manifest in both places before activation.

## Validation evidence

- Static SEO validator: `OK`.
- SEO/search/analytics suite: 27 tests, `OK`.
- Users/Paytrail/Google Shopping suite: 23 tests, `OK`.
- Six changed templates compiled: `TEMPLATE_COMPILE_OK 6`.
- `check --deploy`: only the two established closed-staging warnings remain:
  HSTS is disabled on staging and the legacy email username field is not unique.
- Database-backed SEO tests use synthetic non-personal fixtures and cover the
  catalog, all P0 category routes, the virtual exterior route, five products,
  clean product canonicals and four duplicate-tag redirects.
- Active staging server-side smoke: homepage, catalog and search HTTP 200;
  Finnish language and canonical present; search contains `noindex,follow`.
- External staging: HTTP 403 and
  `X-Robots-Tag: noindex, nofollow, noarchive`.
- Production homepage after staging activation: HTTP 200.

## Release safety record

Earlier candidates were deliberately rejected or rolled back when a gate
failed:

- The first active candidate exposed a missing catalog context value and was
  immediately rolled back.
- R2 was never activated because its server-side manifest rejected four
  transport-corrupted templates.
- R3 exposed an eager Django template-filter lookup with `category=None` and
  was immediately rolled back.
- R4 rendered correctly but the old smoke assumed product data existed in the
  isolated empty staging database; it was rolled back while that gap was
  replaced with synthetic database-backed tests.
- R5 and R6 were never activated because the new redirect tests exposed
  test-client URL/HTTPS expectation errors.
- R7 passed every pre-activation and post-activation gate.

No failed candidate reached production, and the previous closed-staging release
remained available throughout.

## Production decision

Production release is intentionally pending. It requires separate explicit
approval, a fresh production code-only backup, final manifest verification,
small-batch installation and the production SEO/commerce smoke checks defined
in `docs/testing.md`.
