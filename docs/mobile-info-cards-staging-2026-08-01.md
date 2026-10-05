# Mobile information cards — closed staging release

Date: 2026-08-01
Environment: closed `develop.decopaint.fi` staging
Production: promoted after separate user approval

## Approved design

The mobile homepage now uses the approved headings `Sujuvampi ostokokemus`
and `Laatuominaisuudet`. The service and quality groups remain two-column on a
phone but use shorter cards, larger readable text, improved spacing and a
clearer icon-to-copy hierarchy.

All original assets were retained. The service cards still reference
`#icon-box-01` through `#icon-box-04`. The quality cards still use
`bollo-ecologia-bollo-since1984.svg`, `antibacterial.png`,
`bollo-washability.svg` and `bollo-HACCP.svg`. No replacement or generated
icons were introduced.

## Release identity

- Active release:
  `/home/decpai/staging/releases/mobile-info-cards-20260801-r7-equal-height`
- Branch marker: `ui/mobile-info-cards-equal-height-20260801`
- Artifact:
  `work/mobile-info-cards-staging-20260801.tar.gz`
- Artifact SHA-256:
  `fce1307a56316c0f028ed92c1d41c0098659b081305a9f7bf6056b7f8bb87093`
- Rollback target:
  `/home/decpai/staging/releases/mobile-info-cards-20260801`

R2 adds Finnish automatic hyphenation and safe word wrapping for titles and
captions at the phone breakpoint. It does not change the approved grid,
dimensions, copy or icon assets. R2 artifact SHA-256:
`3970d490c677209862505f439a049101bdea381f2091c36a8b75661b34e8ae45`.

## Verification

- Manifest: all three files `OK` on the server.
- Static mobile contract: 11 files, `MOBILE_UI_STATIC_CHECKS_OK=1`.
- Python compilation: passed.
- Django template compilation: passed.
- Internal homepage: HTTP `200`, all approved headings and original icon
  references present.
- Django deploy check: no release-specific errors; two known staging warnings.
- External staging: HTTP `403`, `noindex, nofollow, noarchive` preserved.
- Production: homepage HTTP `200`; pre-recorded template and mobile CSS hashes
  unchanged.
- R2 post-switch source and collected CSS both match SHA-256
  `b87400ef247ec86f529f2788283fb3568622a74510b94dd65594d193dad9d382`.

## Data and integration impact

This is a presentation-only staging release. It does not change the database,
orders, customer information, prices, VAT, stock, delivery, Paytrail,
Merchant Center or Analytics. No database backup was necessary because there
was no database write or migration; rollback is the immutable prior staging
release.

## Production promotion

After separate user approval, the R6 candidate was promoted through the
production backup, atomic-install, public-static, responsive, checkout,
integration-import and error-monitoring gates. The final stylesheet filename
is `mobile-modern-20260801-final.css`; the active staging site remains closed
with HTTP `403` and the existing noindex header. Production evidence is in
`docs/mobile-info-cards-production-2026-08-01.md`.

R7 adds the equal-height row correction for mobile service cards. Its wrapper
flex and card height contracts passed before activation; external staging
remains HTTP `403` with `noindex, nofollow, noarchive`.
