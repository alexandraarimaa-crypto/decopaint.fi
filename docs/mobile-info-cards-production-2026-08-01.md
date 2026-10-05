# Mobile information cards — production release

Date: 2026-08-01
Site: `https://decopaint.fi/`
Change type: code-only responsive presentation

## Outcome

The approved phone layout is live. `Sujuvampi ostokokemus` presents the four
shopping-service cards in a compact two-column grid with 44 px existing sprite
icons. `Laatuominaisuudet` presents the four quality cards with the original
Oikos Since 1984, Antibacterial, Washability and HACCP marks at 54 px.

The change is scoped to the phone breakpoint. Desktop/tablet rendering and all
existing shop behavior remain unchanged. Finnish long-word wrapping is enabled
for titles and captions.

## Release identity

- Final artifact:
  `work/mobile-info-cards-production-20260801-final.tar.gz`
- Artifact SHA-256:
  `1431298e36955e5d69c90eaa21cc878ee6b23747bba660138968cc33e4955062`
- Closed-staging release:
  `/home/decpai/staging/releases/mobile-info-cards-20260801-r6`
- Production backup:
  `/home/decpai/release-backups/mobile-info-cards-20260801T133226Z`

Installed SHA-256 values:

- `shop/templates/shop/base/base.html`:
  `9eb3897607ec5254cbb04c9bc0001d72edf9d9c5b85c37a5475da20f812dfd79`
- `shop/templates/shop/else/main.html`:
  `60b3372eb02e8757e802289f880682be59a76453707aa656867709d2da78307d`
- source and public `mobile-modern-20260801-final.css`:
  `b87400ef247ec86f529f2788283fb3568622a74510b94dd65594d193dad9d382`
- `scripts/validate_mobile_ui.py`:
  `86c260f07991cf39b7fdd09078d84ab79079d010ac89b88089bdcbedc92653f4`

## Static delivery correction

The existing mobile stylesheet is cached publicly for seven days. A query
parameter did not change the bytes served by LiteSpeed, so the release moved to
a unique filename. During verification, Django reported `STATIC_ROOT` under
the Passenger app, while LiteSpeed's document root serves `/static/` from
`/home/decpai/public_html/static`. The final stylesheet was installed in the
actual public webroot and returned HTTP `200` with the expected SHA-256 before
the base template was switched.

An intermediate link that returned `404` was immediately reverted to the
working legacy link. It was never accepted as the completed release.

## Verification

- Static contract validator: passed, 11 files.
- Django template compile: passed.
- `manage.py check --deploy`: no release-specific error; five known baseline
  warnings remained.
- Homepage, catalog, real product, checkout, terms and final CSS: HTTP `200`.
- Payment-create GET: `405`; unsigned payment success/cancel: `403`.
- Homepage final CSS link count: one; both approved section headings: one each.
- Mobile 390×844: no document or section overflow; service cards 92–99 px high,
  quality cards 104–118 px high.
- Mobile 360×800: no overflow and all eight cards visible.
- Merchant sync flag: enabled; Analytics and mail backend imports: passed.
- Error log delta: 658 bytes; new critical pattern count: zero.
- Temporary `.new` files and AppleDouble files: zero.

## Data and integration impact

No database, migration, order, customer, price, tax, stock, delivery, payment
callback, Merchant Center setting or Analytics configuration changed. No
synthetic order, payment, email or external integration write was performed.

Rollback uses the exact archives and procedure documented in
`docs/rollback.md`.

## Equal-height follow-up

The user-reported upper service-card mismatch was reproduced at 472 px as
`92/99 px`. Mobile grid wrappers now stretch their children and each service
card fills its grid-row height. Production verification after reload measured
the upper pair at `99/99 px` and lower pair at `92/92 px`, without horizontal
overflow.

- Follow-up artifact SHA-256:
  `81219c93954ea054111374e1c86259f9391c3934c0f9ae7d042a5819cc01c684`.
- Backup:
  `/home/decpai/release-backups/mobile-info-cards-equal-height-20260801T142538Z`.
- Active CSS: `mobile-modern-20260801-equal-cards.css`.
- All page/security smoke checks passed; error-log critical-pattern count was
  zero. No database or integration setting changed.
