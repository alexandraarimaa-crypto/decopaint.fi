# Source-grounded search staging candidate — 2026-08-01

## Scope

Implement the approved Finnish search model on closed staging only. No product
content, price, stock, order, customer, Merchant Center, Analytics or
production state is changed.

## Baseline

- Public catalog: 154 unique product cards.
- Sources: 352 PDF files and two other linked files.
- Current code searches raw name, attributes and HTML description with
  `icontains`, has no relevance ranking or typo normalization, and omits the
  availability filter in two query branches.
- Closed staging uses an isolated SQLite database and remains externally
  blocked with `noindex`.

## Candidate design

- Standard-library ranking engine loaded from a versioned JSON index.
- AND semantics across customer concepts, field-weighted relevance within each
  concept and deterministic name tie-breaking.
- Conservative normalization for Finnish diacritics, compound phrases and a
  small allowlist of common misspellings.
- Technical compatibility comes only from the official product card and linked
  technical sheet. Raw descriptions are not queried at runtime.
- System protectives can rank after primary finishes; unavailable products are
  always excluded.

## Corrections found during implementation

- Duaflex official data sheet states exterior and interior walls, so its
  extracted scope is corrected to include `ulkokäyttö`.
- The automated draft assigned nicotine/smoke stain use to several washable or
  stain-resistant paints even though their official sheets do not support
  covering existing nicotine stains. Those terms are removed by a traceable
  override.
- Flexigrap and Flexigrap Liscio remain valid results for `PVC pohjamaali`
  because their official technical sheet explicitly names PVC and primer use.
- Antiruggine retains only metal/rust-protection concepts despite its currently
  mislinked Aggrappante PDFs.

## Acceptance criteria

- 154 unique products load from the index.
- The nine golden queries return verified technically relevant leading results.
- Exact known searches remain correct.
- Unavailable products never appear.
- No query returns Antiruggine for PVC.
- Django/AJAX rendering, isolated tests and `check --deploy` pass.
- Closed staging remains HTTP 403/noindex and production remains unchanged.

## Local artifact

- Clean archive: `work/decopaint-search-staging-20260801-v2-clean.tar.gz`
- SHA-256: `cb8498edb5b045d4ddda4833c3b63b9b4a30d31b0838c360226673a59071d897`
- Internal seven-file manifest: verified successfully before upload.
- macOS AppleDouble entries are absent from the clean archive.

## Closed-staging result

- Branch/commit: `search/source-grounded-staging-20260801` / `5545c16`.
- Active release:
  `/home/decpai/staging/releases/search-source-grounded-20260801`.
- Targeted search tests: 10/10; full normalized isolated suite: 36/36.
- HTML and AJAX search smoke: HTTP `200`; active index: 154 products.
- Analytics and Merchant writes remain disabled.
- External staging remains HTTP `403` with
  `X-Robots-Tag: noindex, nofollow, noarchive`.
- Production remained unchanged and returned HTTP `200`.

## Production result

- Владелец отдельно подтвердил production release после принятия модели и
  closed-staging result.
- Exact accepted artifact установлен 2026-08-01; семь installed SHA-256
  совпали с manifest.
- Backup:
  `/home/decpai/release-backups/search-source-grounded-20260801T093927Z`.
- Production validator подтвердил 154 товара и 9 golden queries; unavailable
  товары исключаются, ошибочная Antiruggine/PVC связь не используется.
- Homepage, catalog, login, checkout, real product и production search smoke:
  HTTP `200`; платежные защиты остались `405`/`403`/`403`.
- Merchant sync, email backend и GA4 search event загружаются без внешней
  записи; synthetic contact data редактируется в `[redacted]`.
- `stderr.log` не вырос; DB, заказы, клиенты и внешние настройки не менялись.
- Подробное evidence: `docs/search-production-2026-08-01.md`.
