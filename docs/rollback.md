# Rollback

## Merchant storefront price parity rollback 2026-10-05

No database restore is required.

1. Disable the nightly Merchant schedule before code rollback so incorrect
   prices cannot be republished during the rollback window.
2. Restore the backed-up production `google_shopping/tasks.py` and restart
   Passenger plus Django-Q workers.
3. Do not delete Merchant products. Re-run the last accepted payload only if a
   rollback validation shows a partially processed batch.
4. Confirm the storefront, cart and checkout still return HTTP 200 and that no
   new queue failures or payment errors appeared.

Rollback triggers: the 305 pilot is not `26.83 EUR`, any payload differs from
the initial public regular landing-page price, a Merchant batch reports an
error, or checkout/order smoke changes.

## Transactional email UTF-8 rollback 2026-08-21

No database, order, payment, product, stock, cart or checkout rollback is
required.

1. Restore the previous versions of `config/settings.py` and `mail/views.py`.
2. Restart the application workers and Django-Q workers.
3. Send a non-production test message and confirm email delivery returns to the
   previous behaviour.
4. Do not remove SPF/DKIM/DMARC DNS records during code rollback; DNS mail
   authentication is independent from this application change.

Rollback triggers: email send exceptions, malformed multipart messages,
unexpected sender header rejection by the local MTA or a new traceback in the
mail task path.

## Product-specific Menekkilaskuri rollback 2026-08-20

No database, product-content, price, stock, order, Merchant or Analytics
rollback is required.

1. Restore `shop/views.py`, product `detail.html`, base `base.html` and
   `shop/static/assets/js/mobile-modern.js` from their exact server copies with
   suffix `.bak-20260820-before-calculator`.
2. Remove only `shop/material_calculator.py`,
   `shop/static/assets/js/mobile-modern-20260820-calculator.js` and the matching
   file in `/home/decpai/public_html/static/assets/js/`.
3. Restart Passenger and confirm a product, cart and checkout return HTTP 200.
4. Do not modify the database or product attributes during rollback.

Rollback triggers: product 5xx, malformed calculator JSON, a recommendation
below the required amount, changed product price/variant behaviour or a new
checkout regression.

## Product Open Graph and structured-data R8 rollback 2026-08-02

This release has no migration or external-state rollback. Restore only the
five previous files from the verified archive, then remove the one new helper
path.

Backup:
`/home/decpai/release-backups/seo-product-og-r8-20260802T174800Z/before.tar.gz`

Backup SHA-256:
`9ad16b84fcbb0fa56401488fa655cc4769c153145d36d39b1d9ef782379a5144`

Procedure:

1. Verify the backup SHA-256 and `gzip -t`.
2. Extract it into `/home/decpai/public_html/deco`.
3. Remove only `/home/decpai/public_html/deco/shop/product_schema.py`; the
   marker `product_schema_was_absent` proves it did not exist before R8.
4. Run `manage.py check`, touch `tmp/restart.txt`, and confirm homepage,
   product, checkout and payment-method HTTP status.
5. Confirm the previous file hashes recorded in the R8 evidence document and
   check the `stderr.log` delta.

Rollback triggers: malformed Product JSON-LD, price/availability mismatch,
product 5xx, checkout regression or new traceback. Do not restore the database,
change Merchant items or replay Paytrail operations.

## Finnish SEO P0 staging rollback 2026-08-02

No database restore, migration reversal or static rollback is required. The
candidate is code/template-only.

Current SEO staging release:
`/home/decpai/staging/releases/seo-fi-p0-20260802-r7`.

Rollback target:
`/home/decpai/staging/releases/mobile-info-cards-20260801-r7-equal-height`.

Procedure:

1. Create `/home/decpai/staging/decopaint.next` as a symlink to the rollback
   target and verify it with `readlink -f`.
2. Atomically replace `/home/decpai/staging/decopaint` with the verified link.
3. Touch the staging release `tmp/restart.txt` only.
4. Verify internal homepage/catalog HTTP 200.
5. Verify external staging HTTP 403 plus
   `X-Robots-Tag: noindex, nofollow, noarchive`.
6. Verify production homepage remains HTTP 200.

Do not delete the SEO release or failed forensic candidates until acceptance is
complete. Production rollback is not applicable because production was not
deployed.

## Source-grounded AI assistant closed-staging rollback

No database restore, migration reversal, Merchant action, Analytics change,
payment action or production change is required.

1. Atomically repoint `/home/decpai/staging/decopaint` to the staging release
   recorded before activation.
2. Touch only the staging `tmp/restart.txt`.
3. Verify the assistant route is absent or disabled on the restored release.
4. Confirm internal homepage/search smoke and external HTTP 403/noindex.
5. Confirm the production homepage remains healthy and unchanged.
6. Preserve the failed release, its manifest and non-PII diagnostic output.

Immediate rollback triggers include any source-free claim, recommendation
without all required context, high-risk auto-answer, missing CSRF/rate limit,
chat persistence, external network call, 5xx, template failure or exposure of
the staging hostname.

## Source-grounded search code/data-only rollback

No database restore, migration reversal, Merchant action or Analytics change
is required.

1. Switch the closed staging symlink back to the recorded previous release.
2. Restart staging Passenger.
3. Confirm external HTTP 403 and the noindex header.
4. Run homepage/import/search smoke inside the server environment.
5. Preserve the failed release and non-PII logs for diagnosis.

Rollback triggers include search 5xx, template failure, missing verified exact
products, unavailable products appearing, or a technically incompatible top
result.

Actual previous-release pointer:

`/home/decpai/staging-backups/search-before-20260801T090310Z/previous-release`

It resolves to `/home/decpai/staging/releases/mobile-ui-20260730`. Atomic
rollback is a staging symlink switch followed by touching `tmp/restart.txt`.

### Production rollback after the 2026-08-01 release

Production backup:

`/home/decpai/release-backups/search-source-grounded-20260801T093927Z`

No database restore, migration reversal, Merchant action or Analytics setting
change is required. The six added paths were absent before the release.

1. Restore `before/shop/views.py` to
   `/home/decpai/public_html/deco/shop/views.py`.
2. Remove only these release-added paths:
   `shop/search_engine.py`, `shop/tests_search_engine.py`,
   `shop/tests_search_view.py`, `scripts/validate_search_engine.py`,
   `search-data/knowledge-base-draft.json` and
   `search-data/search-overrides.json`.
3. Verify restored `shop/views.py` SHA-256 equals
   `016dc46de4973bd76cc816fec535946c164267828d3efb21ad17721857004f28`.
4. Restart Passenger through `tmp/restart.txt`.
5. Recheck homepage, catalog, login, checkout, a real product, legacy search,
   payment creation GET and unsigned Paytrail callbacks.
6. Confirm `stderr.log` has no new traceback or Internal Server Error.

The backup also contains the exact candidate archive and manifest for forensic
comparison. Do not delete or modify products, orders, customers or Merchant
items during rollback.

## Mobile UI code-only rollback

No database restore is required.

1. Restore the nine modified template files and any previously existing mobile
   static files from the server-side pre-install backup.
2. Remove `shop/static/assets/css/mobile-modern.css` and
   `shop/static/assets/js/mobile-modern.js` when they did not exist before the
   release.
3. Repeat `collectstatic --noinput`.
4. Restart Passenger.
5. Smoke-test homepage, menu, category, search, product variants, cart,
   checkout, consent controls and the public Analytics asset.
6. Confirm there is no new traceback and that the prior mobile markup is served.

Local source baseline archive:

`work/decopaint-mobile-ui-baseline-20260730.tar.gz`

SHA-256:

`0ff8188f6b6a5068de405cf435df8d6bcfd676a783fb63f687a2f7155c03d1ae`

Фактический production backup:

`/home/decpai/release-backups/mobile-ui-20260730T202101Z/runtime-before.tar.gz`

SHA-256:

`c7c0e5078537f08f8db4b8b307a78d1f168ef194b0055b96e02926843035c5020`

В production до выпуска существовали девять templates. Оба source mobile
static файла и оба public mobile static файла отсутствовали, поэтому rollback
должен удалить только эти четыре явно записанных пути после восстановления
templates, затем выполнить `collectstatic`, Passenger restart и smoke.
Database restore не требуется.

## Уровни

### Code-only

- переключить на предыдущий tested artifact/commit;
- восстановить предыдущий virtualenv/static manifest при несовместимости;
- перезапустить Passenger/worker;
- smoke test.

### Database-compatible release

- откатить код без DB restore, если migrations backward-compatible.

### Database migration

- предпочтительны expand/contract migrations;
- destructive migration требует отдельного approved reverse/data restore plan;
- DB restore затрагивает новые заказы после backup и без владельца запрещён.

### Integration incident

- feature flag отключает новый path;
- сохранить подтверждённые callback;
- не повторять payment/merchant mutations вслепую;
- reconciliation по transaction/order IDs.

## Решение об откате

Откатывать при:

- росте 5xx/payment errors;
- неверной цене, VAT, delivery или availability;
- duplicate/missing paid orders;
- утечке PII;
- checkout regression;
- critical SEO deindexing signal.

## После отката

- подтвердить checkout и callback;
- сверить заказы/оплаты;
- зафиксировать incident timeline;
- сохранить только non-PII evidence;
- root-cause review до следующего релиза.

## P0 code-only rollback 2026-07-30

Для кандидата `work/decopaint-p0-production-candidate-clean.tar.gz` схема БД не
меняется. Перед выпуском создаётся закрытая timestamped копия только семи
runtime-путей вне `public_html`. Точный baseline и порядок восстановления
зафиксированы в `docs/production-release-p0.md`.

Фактический backup выпуска:
`/home/decpai/release-backups/p0-20260730T152547Z/production-files-before.tar.gz`,
SHA-256
`347baae5a49074aac73167eb347ff58ca85b676266db142a5908102849d574dd`.

## Merchant order sync code-only rollback 2026-07-30

Схема БД не менялась. Backup двух исходных production-файлов:

`/home/decpai/release-backups/merchant-order-sync-20260730`

Порядок отката:

1. Скопировать backup `google_shopping/tasks.py` и `pk_paytrail/views.py`
   обратно в `/home/decpai/public_html/deco/`.
2. Выполнить `py_compile` для обоих файлов.
3. Перезапустить Passenger через `tmp/restart.txt`.
4. Послать `TERM` текущему Django-Q master и дождаться автоматического
   восстановления штатным supervisor.
5. Подтвердить один master, четыре worker, homepage `200` и отсутствие свежего
   traceback.

Исходные SHA-256:

- `google_shopping/tasks.py`:
  `6aa3740c68ac121a7851c51837de34da22de0251fabd16ee332ab95b31b1d651`
- `pk_paytrail/views.py`:
  `ab3c67f69b1ca83806bf1b0218c8761fc7c7ec6b4379aae70ece1e3bf891f8fd`

## GA4 ecommerce code-only rollback

Фактический backup:

`/home/decpai/release-backups/ga4-ecommerce-20260730-2135/runtime-before.tar.gz`

SHA-256:

`095ff91db68b5923f3162a5e91fa080f071b68faaad3ccdcf744e574ac42815a`

Порядок:

1. Восстановить девять существовавших Python/templates файлов из
   `runtime-before.tar.gz` в `/home/decpai/public_html/deco`.
2. Удалить три добавленных source-файла:
   `shop/analytics.py`, `shop/templatetags/analytics_tags.py` и
   `shop/static/assets/js/analytics.js`.
3. Удалить добавленный публичный
   `/home/decpai/public_html/static/assets/js/analytics.js`.
4. Повторно выполнить `collectstatic --noinput`.
5. Выполнить Python compile и перезапустить Passenger через
   `tmp/restart.txt`.
6. Подтвердить homepage/product/checkout, отсутствие ссылки на новый JS и
   отсутствие нового traceback.
7. Если GA4 key events/enhanced measurement были изменены позднее, вернуть их
   к сохранённому pre-release state. В текущем release эти настройки не
   менялись.

DB restore не требуется: кандидат не содержит migrations и не меняет заказы,
клиентов, цены, налоги, остатки или доставку.

## Verified search placeholder code-only rollback 2026-08-01

Фактический backup:

`/home/decpai/release-backups/search-placeholder-20260801T104718Z`

Предыдущий template SHA-256:

`b4c8a7d3894a9f4825a6cce9d1f8dfca73a72853cfca11f777d332970ffae7c4`

Порядок точного отката:

1. Сверить SHA-256 backup-файла
   `shop/templates/shop/else/main.html` с указанным baseline.
2. Восстановить этот один файл в
   `/home/decpai/public_html/deco/shop/templates/shop/else/main.html`.
3. Перезапустить Passenger через
   `/home/decpai/public_html/deco/tmp/restart.txt`.
4. Подтвердить homepage и catalog HTTP `200`, старый placeholder на mobile и
   отсутствие нового роста `stderr.log`.

DB, orders, customers, payments, Merchant Center и Analytics не требуют
отката, поскольку release их не изменял.

## Mobile information cards closed-staging rollback 2026-08-01

The pre-release staging target is preserved as the immutable rollback point:

`/home/decpai/staging/releases/search-source-grounded-20260801`

Exact rollback:

1. Confirm the target exists and that
   `/home/decpai/staging/decopaint` currently points to
   `/home/decpai/staging/releases/mobile-info-cards-20260801`.
2. Create `/home/decpai/staging/decopaint.next` as a symlink to the rollback
   target and atomically replace `/home/decpai/staging/decopaint` with it.
3. Touch `/home/decpai/staging/decopaint/tmp/restart.txt`.
4. Re-run the internal homepage smoke, then confirm external HTTP `403` and
   `X-Robots-Tag: noindex, nofollow, noarchive`.

No database restore or integration rollback is required. Production was not
changed by this staging release.

### R2 immediate rollback

The R2 pre-switch target is preserved at:

`/home/decpai/staging/releases/mobile-info-cards-20260801`

To undo only the Finnish word-wrapping hardening, atomically repoint
`/home/decpai/staging/decopaint` to that R1 directory via `decopaint.next`,
touch `tmp/restart.txt`, then repeat the internal homepage contract and the
external 403/noindex checks. No database or production rollback is involved.

## Mobile information cards production rollback 2026-08-01

Backup root:

`/home/decpai/release-backups/mobile-info-cards-20260801T133226Z`

Verified backup archives:

- initial three-file runtime backup:
  `runtime-before.tar.gz`, SHA-256
  `ec5b6fc371bf9cb2ddade386853cf32eb8ca6aac9fec49670cbbd9e7bd87ce88`;
- original base template backup:
  `base-before.tar.gz`, SHA-256
  `334b3dbe0b863c6729898d414a90325a13726f78751a78c81c5490baeec78a0e`;
- recovered pre-release validator from immutable staging R3:
  `validator-before-recovered.tar.gz`, SHA-256
  `3a22899c80e9ea943a02fdd17a7ab19f0c39d3c47cc4d9f6dbed7eee38355fc2`.

Exact rollback:

1. Verify all three archive hashes and their internal manifests.
2. Restore `shop/templates/shop/else/main.html`, the source legacy
   `mobile-modern.css` and the app-root collected legacy CSS from
   `runtime-before.tar.gz`.
3. Restore `shop/templates/shop/base/base.html` from `base-before.tar.gz`.
4. Restore `scripts/validate_mobile_ui.py` from
   `validator-before-recovered.tar.gz`; its pre-release SHA-256 is
   `167972f7193e0552e2f429bbc6870556a724471472a91fb21405d77b28e559f7`.
5. Remove only the release-added files
   `shop/static/assets/css/mobile-modern-20260801-final.css` and
   `/home/decpai/public_html/static/assets/css/mobile-modern-20260801-final.css`.
6. Touch `/home/decpai/public_html/deco/tmp/restart.txt` and confirm homepage,
   catalog, a real product, checkout and terms return `200`.
7. Confirm the legacy CSS URL returns `200`, payment endpoints retain
   `405/403`, and no new critical error-log pattern appears.

No database or integration rollback is required because the release did not
change migrations, orders, customers, prices, stock, delivery, Paytrail,
Merchant Center or Analytics configuration.

### Equal-height correction rollback

Backup:

`/home/decpai/release-backups/mobile-info-cards-equal-height-20260801T142538Z`

- `runtime-before.tar.gz` SHA-256:
  `615e4cf43a62118b09b40bcaab2ab81dd407fbf264eab7ed5c3a562d88a8fb2c`.
- Pre-release base SHA-256:
  `9eb3897607ec5254cbb04c9bc0001d72edf9d9c5b85c37a5475da20f812dfd79`.
- Pre-release validator SHA-256:
  `86c260f07991cf39b7fdd09078d84ab79079d010ac89b88089bdcbedc92653f4`.

Exact rollback:

1. Verify the archive and its internal manifest.
2. Restore the base template and validator from `runtime-before.tar.gz`.
3. Remove only the release-added source and public files named
   `mobile-modern-20260801-equal-cards.css`.
4. Touch the production `tmp/restart.txt` and verify the prior
   `mobile-modern-20260801-final.css` link and HTTP `200` response.
5. Repeat homepage/catalog/product/checkout/terms, payment URL protection and
   error-log smoke checks.

The prior CSS and all data/integration state were not modified, so no database
or external integration rollback is required.

## Finnish SEO P0 production rollback 2026-08-02

Backup root:

`/home/decpai/release-backups/seo-fi-p0-20260802T171107Z`

Verified previous-files archive SHA-256:

`5f50a82871e8ffec627b14a4b7b2cb201adf5ad2285d51bfac831dcf9fc79c03`

Exact rollback:

1. Verify `production-files-before.tar.gz` against the hash above and inspect
   its nine-path listing.
2. Restore the archive into `/home/decpai/public_html/deco`.
3. Remove only the three release-added paths listed in
   `new-paths-absent.txt`: `shop/seo.py`, `shop/tests_seo.py` and
   `scripts/validate_seo_p0.py`.
4. Run the saved `production-before.sha256` check.
5. Touch `/home/decpai/public_html/deco/tmp/restart.txt`.
6. Confirm homepage, catalog, search, a real product and checkout return
   `200`; `/catalog/ulkomaalit/` returns the pre-release `404`.
7. Confirm Paytrail endpoints remain `405/403/403` and no new critical error
   appears in `stderr.log`.

Do not restore a database or change Merchant Center/Analytics settings: this
release contains no migration or external-system write.

## Menekkilaskuri desktop rollback 2026-08-20

1. Restore
   `/home/decpai/public_html/deco/shop/templates/shop/product/detail.html.bak-20260820-before-desktop-calculator`
   over `shop/templates/shop/product/detail.html`.
2. Refresh Passenger with `/home/decpai/public_html/deco/tmp/restart.txt`.
3. Confirm the product page returns `200`, the desktop calculator is hidden as
   before, and mobile calculation still works.

No database, static asset or external integration rollback is required.

## Country default language rollback 2026-08-20

1. Restore
   `/home/decpai/public_html/deco/config/settings.py.bak-20260820-before-country-language`
   over `/home/decpai/public_html/deco/config/settings.py`.
2. Refresh Passenger through `/home/decpai/public_html/deco/tmp/restart.txt`.
3. Confirm the homepage returns `200` with the prior language behaviour.

The unreferenced middleware and CIDR files may remain safely in place. No
database, catalog or external-system rollback is required.

## Google Customer Reviews language rollback 2026-08-20

1. Restore
   `/home/decpai/public_html/deco/order/templates/order/created.html.bak-20260820-before-gcr-language`
   over `/home/decpai/public_html/deco/order/templates/order/created.html`.
2. Refresh Passenger through `/home/decpai/public_html/deco/tmp/restart.txt`.
3. Confirm homepage, catalog and a real product return `200`.

No database, order, customer, email, payment or Merchant rollback is required.
