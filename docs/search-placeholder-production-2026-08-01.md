# Verified mobile search placeholder production release — 2026-08-01

## Goal

Не показывать на mobile homepage пример поискового запроса, который не даёт
результатов. Старый placeholder `Esim. kylpyhuoneen seinä` заменён на
проверенный запрос `Esim. patterimaali`.

## Scope

- One runtime template:
  `shop/templates/shop/else/main.html`.
- One local static guard added to `scripts/validate_mobile_ui.py`.
- No database, migration, order, customer, price, stock, delivery, payment,
  Merchant Center or Analytics change.

## Baseline

- Production homepage: HTTP `200`.
- Previous template SHA-256:
  `b4c8a7d3894a9f4825a6cce9d1f8dfca73a72853cfca11f777d332970ffae7c4`.
- Passenger `stderr.log`: 7 482 318 bytes, mtime
  `2026-08-01 09:06:10.983027974 +0100`.

## Candidate and staging

- Local/server archive SHA-256:
  `6c813082b7eb5db79ad5a4c2023420abbf763f060d03a75e714e5a88f395d20c`.
- Candidate template SHA-256:
  `adb045645c2efbd9804c53d408c2d39c09c5760f057e8a9f6037cb48f017fcd9`.
- Closed staging release:
  `/home/decpai/staging/releases/search-placeholder-verified-20260801`.
- Branch marker: `ui/search-placeholder-verified-20260801`.
- Manifest verification: `shop/templates/shop/else/main.html: OK`.
- Static mobile validator: 11 files, `OK`.
- Source-grounded search validator: 154 products, 9 golden queries, `OK`.
- Search unit tests: 8 tests, `OK`.
- Python compile: `OK`.
- Django deploy check: no errors; two existing staging warnings only.
- Isolated staging homepage over HTTPS: `200`, new placeholder present, old
  placeholder absent.

The isolated staging dataset deliberately does not copy production products.
The checked knowledge index established the `patterimaali` mapping, and the
production read-only smoke then confirmed the actual visible result.

## Production deployment

- Verified backup created before the production write:
  `/home/decpai/release-backups/search-placeholder-20260801T104718Z`.
- Backup template SHA-256 matched the baseline.
- Installed only the candidate template.
- Passenger restarted via `tmp/restart.txt`.
- Installed SHA-256 matched the candidate.

## Production smoke

- Homepage: HTTP `200`.
- Catalog: HTTP `200`.
- `/catalog/search/?q=patterimaali`: HTTP `200`.
- Server-rendered homepage contains `placeholder="Esim. patterimaali"`.
- Search output contains `Patterimaali Ecosmalto Thermo` and reports one
  product.
- Browser viewport `390×844`: new placeholder count `1`; old placeholder
  count `0`; the exact `Ecosmalto Thermo` product link count `1`.
- Browser console error count: `0`.
- Passenger `stderr.log` remained exactly 7 482 318 bytes with unchanged
  mtime after the smoke window.

## Rollback

Restore the one backed-up template, touch production `tmp/restart.txt`, then
repeat homepage, catalog, mobile placeholder and error-log smoke checks. No
database or external integration rollback is required.
