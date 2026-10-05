# Deployment

## Merchant storefront price parity 2026-10-05

- Scope: `google_shopping/tasks.py`, tests and documentation only; no
  migrations, dependency changes or database writes.
- Push branch `fix/merchant-public-prices-20261005`, open a pull request, pass
  CI and deploy the exact reviewed commit to closed staging.
- Keep Merchant writes disabled on staging. Generate payloads in dry-run and
  require zero differences against the storefront's initial regular prices.
- Preserve the production `google_shopping/tasks.py` hash and file backup,
  install the reviewed file, then restart Passenger and Django-Q workers.
- Enable a one-product pilot for 305 BioLavabile. Confirm Merchant offer
  `W03050TR0E` becomes `26.83 EUR` and links to the page whose initial public
  regular price is `26.83 EUR`.
- Only after the pilot passes, run the existing optimized update in batches of
  20. Do not use full-clean upload and do not delete stale offers in this
  release.
- Verify queue failures are zero, compare a full Merchant export with the
  storefront audit, and keep the nightly schedule enabled.

## Transactional email UTF-8 release 2026-08-21

- Scope: code/settings/test-only; no migrations, dependencies, database writes
  or external-service writes.
- Set production `DEFAULT_FROM_EMAIL` to a domain-authenticated mailbox on
  `decopaint.fi`; set `DEFAULT_REPLY_TO_EMAIL=info@decopaint.fi` and
  `EMAIL_FROM_NAME="Deco Paint Finland Oy"` unless already configured.
- Deploy `config/settings.py`, `mail/views.py` and the accompanying tests, then
  restart the application workers and Django-Q workers so queued status emails
  use the new MIME builder.
- Send one shipment-status test message and verify the decoded subject/body
  show `Lähetetty` rather than replacement characters.
- Add a DMARC TXT record for `_dmarc.decopaint.fi`; start with a monitoring
  policy and tighten after confirming SPF/DKIM alignment from real order mail.

## Product-specific Menekkilaskuri production release 2026-08-20

- Scope: code/template/static-only; no migrations, dependencies, database or
  external-service writes.
- Branch: `fix/material-calculator-20260820`.
- Exact pre-release files were preserved on the server with suffix
  `.bak-20260820-before-calculator` for `shop/views.py`, product `detail.html`,
  base `base.html` and the previous mobile JavaScript.
- New helper: `shop/material_calculator.py`.
- New cache-busted asset:
  `assets/js/mobile-modern-20260820-calculator.js`; it was installed in both
  source static and the collected production static root.
- Install order kept imports safe: helper and asset first, templates next,
  `shop/views.py` last, then Passenger restart.
- Post-release browser and 154-product read-only smoke completed without a 5xx
  or invalid configuration.
- Full evidence: `deployments/2026-08-20-material-calculator.md`.

## Product Open Graph and structured-data production release 2026-08-02

- Scope: code/template-only R8 continuation of the approved Finnish SEO P0
  branch lineage.
- Closed candidate:
  `/home/decpai/staging/releases/seo-fi-p0-20260802-r8`.
- Accepted archive:
  `/home/decpai/staging/decopaint-seo-r8-20260802-v4.tar.gz`.
- Archive SHA-256:
  `e20a4de2258b97e8de8774758e3f32ba13d6e3ef55c6d13f98776d17405008a9`.
- Verified backup:
  `/home/decpai/release-backups/seo-product-og-r8-20260802T174800Z/before.tar.gz`.
- Backup SHA-256:
  `9ad16b84fcbb0fa56401488fa655cc4769c153145d36d39b1d9ef782379a5144`.
- Installed paths matched the closed-staging candidate byte-for-byte before
  the final smoke test.
- No migration, dependency install, collectstatic, database write or external
  integration mutation was required.
- Passenger was restarted only after `manage.py check` completed.
- Full evidence: `docs/seo-product-og-r8-production-2026-08-02.md`.

## Finnish SEO P0 closed-staging release 2026-08-02

- Scope: closed staging only; production requires separate explicit approval.
- Branch: `seo/fi-p0-staging-20260802`; final commit `86859ed`.
- Active immutable release:
  `/home/decpai/staging/releases/seo-fi-p0-20260802-r7`.
- Previous release retained:
  `/home/decpai/staging/releases/mobile-info-cards-20260801-r7-equal-height`.
- Exact artifact SHA-256:
  `e30f02c2d320d06e057bedff436cbe82b084231af21bf8c4b2681962e98eb760`.
- All 12 manifest entries were verified before the staging symlink switch.
- Activation was an atomic symlink replacement followed by staging Passenger
  restart only.
- No migrations, database writes, `collectstatic`, dependencies, production
  files, Merchant actions or Analytics writes.
- Pre- and post-activation evidence is recorded in
  `docs/seo-fi-p0-staging-2026-08-02.md`.

## Source-grounded AI assistant closed-staging candidate 2026-08-01

- Scope is closed staging only. Production publication requires a separate,
  explicit approval after specialist review of the prototype and evidence.
- Logical branch: `ai/source-grounded-assistant-staging-20260801`.
- Candidate archive:
  `work/decopaint-ai-assistant-staging-20260801.tar.gz`.
- Candidate SHA-256:
  `01434a6f325ca9e6418efe9df1d79759ca69e3425b39dad97034fd1f9e677c02`.
- The release is code/data-only: no migrations or database writes. Keep the
  isolated staging DB and all production integration kill switches.
- Create a new immutable release from the active closed-staging release,
  verify `RELEASE_MANIFEST.sha256`, enable only the two staging flags, run all
  tests, then switch the staging symlink atomically.
- `collectstatic` is staging-only and required for the prototype CSS/JS. Do not
  touch the production static root.
- Preserve the previous staging symlink target as the immediate rollback.
- External staging must remain HTTP 403 with
  `X-Robots-Tag: noindex, nofollow, noarchive` before and after activation.
- Current status: local candidate complete; server deployment is pending an
  authenticated cPanel session and successful staging gates.

## Source-grounded search staging candidate 2026-08-01

- Scope is closed staging only; production requires a separate explicit
  approval after acceptance.
- Create server branch `search/source-grounded-staging-20260801` from the
  current staging baseline and record its commit.
- Create a new versioned release; do not edit the active release in place.
- Verify the artifact SHA-256 manifest before applying these paths:
  `shop/views.py`, `shop/search_engine.py`, `shop/tests_search_engine.py`,
  `scripts/validate_search_engine.py`, `search-data/knowledge-base-draft.json`
  and `search-data/search-overrides.json`.
- There are no migrations or database writes; keep the isolated staging DB,
  locmem email backend, Merchant kill switch and Analytics kill switch.
- Run unit tests, golden-query validator, Django test suite and
  `check --deploy`, then atomically switch the staging release symlink and
  restart staging Passenger.
- Verify external 403/noindex before and after, and keep the previous release
  for immediate rollback.

### Actual closed-staging release

- Branch: `search/source-grounded-staging-20260801`.
- Commit: `5545c16`.
- Clean artifact SHA-256:
  `cb8498edb5b045d4ddda4833c3b63b9b4a30d31b0838c360226673a59071d897`.
- Release: `/home/decpai/staging/releases/search-source-grounded-20260801`.
- Active symlink was switched atomically after all tests passed.
- Backup/previous release:
  `/home/decpai/staging-backups/search-before-20260801T090310Z`.
- No database migration, `collectstatic`, Merchant action, Analytics write or
  production file change was performed.

### Actual production release

- Владелец отдельно подтвердил production deployment после closed-staging
  acceptance.
- Exact artifact SHA-256:
  `cb8498edb5b045d4ddda4833c3b63b9b4a30d31b0838c360226673a59071d897`.
- Candidate распакован вне web root в
  `/home/decpai/release-candidates/search-source-grounded-20260801`; manifest
  и Python compile проверены до production write.
- Проверяемый backup создан вне `public_html`:
  `/home/decpai/release-backups/search-source-grounded-20260801T093927Z`.
- Сначала установлены шесть новых code/data paths, затем последним заменён
  `shop/views.py`; после проверки installed manifest Passenger перезапущен.
- Migrations, collectstatic, dependencies и production DB не затрагивались.
- Post-release smoke, integration safety checks и stderr comparison прошли;
  rollback не потребовался.
- Полное evidence:
  `docs/search-production-2026-08-01.md`.

## Mobile UI code-only candidate 2026-07-30

- Deploy only to a new closed staging release.
- Back up all eleven existing runtime paths before replacing them. Record
  absence for the two new static files so rollback can remove them.
- Verify the candidate manifest before activation.
- Run template compilation, static candidate checks, the existing Django test
  suite and `check --deploy`.
- Execute `collectstatic --noinput` only in staging, then restart staging
  Passenger.
- Confirm noindex/403 isolation before any synthetic commerce tests.
- Production deployment requires a separate explicit approval after visual
  acceptance and staging evidence.

### Фактический production release

- Владелец отдельно подтвердил production deployment после prototype и
  closed-staging acceptance.
- Установлен точный 11-файловый artifact с SHA-256
  `796a31f40a02ab8ac3a448a451674c6907a148300eabb2e3fc45e0b74080d05c`.
- Production backup:
  `/home/decpai/release-backups/mobile-ui-20260730T202101Z`.
- Девять templates существовали и были сохранены; отсутствие двух новых
  source static и двух public static путей записано для точного rollback.
- `collectstatic`: два файла скопированы, 399 не изменились; публичные CSS/JS
  дополнительно установлены в фактически обслуживаемый static root.
- Passenger перезапущен, post-release smoke и integration safety checks
  завершены. Rollback не потребовался.
- Полное evidence:
  `docs/mobile-ui-production-release-evidence-2026-07-30.md`.

Текущий ручной production deployment не соответствует безопасной схеме. Ниже целевой runbook.

## Preconditions

- approved change и связанный test evidence;
- закрытый staging прошёл smoke;
- актуальный проверенный backup;
- maintenance/communication plan;
- rollback owner и monitoring window;
- secrets доступны через environment, не в archive/repo.

## Процедура

1. Зафиксировать commit SHA и release notes.
2. Проверить свободное место и health backup.
3. Снять DB backup только если есть DB/migration change.
4. Включить maintenance mode только при необходимости.
5. Развернуть exact artifact.
6. Установить pinned dependencies в versioned virtualenv.
7. Выполнить migrations после просмотра SQL/lock risk.
8. `collectstatic`.
9. Перезапустить Passenger/worker.
10. Выполнить smoke checklist.
11. Проверить 5xx, payment callbacks, queue, email, Merchant и analytics.
12. Закрыть release или выполнить rollback.

## Запрещено

- редактировать production source через UI без commit;
- загружать полный home/source archive в public web root;
- хранить backup в public_html;
- мигрировать до backup/rollback test;
- одновременно менять payment, pricing и checkout UI в одном релизе.

## Наблюдение

- первые 30 минут: непрерывно;
- 2 и 24 часа: error/order/payment reconciliation;
- 7 дней: SEO/CWV/conversion guardrails.

## P0 release candidate 2026-07-30

Предрелизная проверка и точный список runtime-файлов зафиксированы в
`docs/production-release-p0.md`. Владелец подтвердил выпуск; clean archive
установлен в production, Passenger перезапущен, post-release smoke завершён.
Rollback не потребовался.

## Merchant order sync release 2026-07-30

- Candidate проверен в отдельном закрытом staging release
  `/home/decpai/staging/releases/merchant-sync-20260730`.
- В production развёрнуты только два runtime-файла:
  `google_shopping/tasks.py` и `pk_paytrail/views.py`.
- Passenger перезапущен через `tmp/restart.txt`.
- Штатный Django-Q supervisor автоматически восстановил master; после удаления
  лишнего ручного процесса подтверждён ровно один master и четыре worker.
- Production smoke: imports `OK`, legacy-field normalization `OK`,
  `MERCHANT_SYNC_EFFECTIVE=True`, homepage `200`.
- `MERCHANT_SYNC_ENABLED` явно не задан в settings; текущий код намеренно
  использует `True` по умолчанию. Kill switch можно включить явным
  `MERCHANT_SYNC_ENABLED=False`.
- Не выполнять synthetic production order. Следующий реальный подтверждённый
  заказ проверить по Django-Q task/result и Merchant response без записи PII в
  release-документы.

## GA4 ecommerce release

- Code-only, без migrations.
- Staging обязан использовать `ANALYTICS_ENABLED=False` и synthetic orders.
- После тестов создать backup точного списка изменяемых runtime templates,
  Python и static JS вне `public_html`.
- После установки выполнить `collectstatic --noinput`, Passenger restart,
  homepage/product/checkout smoke и проверить отсутствие новых traceback.
- Затем в GA4 убрать key-event status у `add_to_cart` и legacy
  `conversion_event_purchase`, оставить `purchase`; отключить enhanced Site
  Search после подтверждения custom search event.
- Production synthetic order запрещён; `purchase` проверяется на следующем
  реальном заказе по non-PII `DP-{order_id}`.

### Фактический release 2026-07-30

- Closed staging release:
  `/home/decpai/staging/releases/ga4-ecommerce-20260730`.
- Staging: 26 тестов `OK`, Python/template compile `OK`,
  `ANALYTICS_ENABLED=False`, внешний HTTP `403` с noindex header.
- Production backup:
  `/home/decpai/release-backups/ga4-ecommerce-20260730-2135/`.
- В production установлены только runtime Python/templates/static JS; database
  и migrations не затронуты.
- 12 installed runtime-файлов совпали с candidate manifest по SHA-256.
- Для текущей hosting-схемы `collectstatic` пишет в
  `/home/decpai/public_html/deco/static`, тогда как публичный `/static/`
  обслуживается из `/home/decpai/public_html/static`. Поэтому новый
  `analytics.js` дополнительно скопирован в публичный static root и проверен
  HTTP-запросом.
- Post-release smoke: основные страницы `200`, `view_item` виден в GA4
  Realtime, `stderr.log` без роста.
- Key-event status и enhanced measurement пока не изменять до первого
  подтверждённого production `purchase`.

## Verified search placeholder release 2026-08-01

- Scope: one template-only change in
  `shop/templates/shop/else/main.html`; no DB, migrations, collectstatic,
  dependencies or integration configuration.
- Closed staging release:
  `/home/decpai/staging/releases/search-placeholder-verified-20260801`.
- Logical branch marker: `ui/search-placeholder-verified-20260801`.
- Candidate archive SHA-256:
  `6c813082b7eb5db79ad5a4c2023420abbf763f060d03a75e714e5a88f395d20c`.
- Production backup was verified before the write at
  `/home/decpai/release-backups/search-placeholder-20260801T104718Z`.
- Only after manifest, static, golden-query, unit and Django checks passed,
  the single template was installed and Passenger restarted through
  `tmp/restart.txt`.
- Installed SHA-256:
  `adb045645c2efbd9804c53d408c2d39c09c5760f057e8a9f6037cb48f017fcd9`.
- Post-release mobile and search smoke passed; rollback was not required.
- Full evidence: `docs/search-placeholder-production-2026-08-01.md`.

## Mobile information cards closed-staging release 2026-08-01

- Scope: one homepage template, one mobile stylesheet and one contract
  validator; no database, migrations, dependencies or integration settings.
- Source release:
  `/home/decpai/staging/releases/search-placeholder-verified-20260801`.
- New immutable release:
  `/home/decpai/staging/releases/mobile-info-cards-20260801`.
- Logical branch marker: `ui/mobile-info-cards-staging-20260801`.
- The candidate was manifest-verified and tested before the symlink change.
- Staging was switched atomically through `/home/decpai/staging/decopaint.next`
  and Passenger was restarted with `tmp/restart.txt`.
- External staging access remains denied with HTTP `403` and the existing
  noindex header. Production was not deployed or restarted.
- Production release requires separate approval followed by a fresh exact-file
  backup, mobile visual smoke, checkout/integration smoke and monitoring.
- Full evidence: `docs/mobile-info-cards-staging-2026-08-01.md`.

### Responsive hardening R2

- Active closed-staging release:
  `/home/decpai/staging/releases/mobile-info-cards-20260801-r2`.
- Logical branch marker: `ui/mobile-info-cards-staging-20260801-r2`.
- Scope: CSS overflow protection plus its static validation contract; no
  template, database, migration, dependency or integration changes.
- R2 was cloned from the tested R1 immutable release, overlaid from a
  checksum-verified two-file artifact, tested before activation and switched
  atomically through `decopaint.next`.
- Immediate rollback target is the preserved R1 release
  `/home/decpai/staging/releases/mobile-info-cards-20260801`.

## Mobile information cards production release 2026-08-01

- User approval was received after the mobile model and closed-staging review.
- Final closed-staging release:
  `/home/decpai/staging/releases/mobile-info-cards-20260801-r6` with logical
  branch marker `ui/mobile-info-cards-staging-20260801-r6`.
- Final artifact:
  `work/mobile-info-cards-production-20260801-final.tar.gz`, SHA-256
  `1431298e36955e5d69c90eaa21cc878ee6b23747bba660138968cc33e4955062`.
- Backup root:
  `/home/decpai/release-backups/mobile-info-cards-20260801T133226Z`.
- Files were staged beside their targets, byte-compared and atomically moved;
  the base template was switched last, followed by a Passenger restart.
- Hosting note: Passenger app root is `/home/decpai/public_html/deco`, but
  LiteSpeed serves `/static/` from `/home/decpai/public_html/static`. The final
  CSS was therefore installed in both source static and the actual public
  webroot, and the public URL was required to return `200` with the candidate
  hash before the base template was switched.
- A query-string cache-bust was rejected because LiteSpeed continued to serve
  the old seven-day-cached CSS. An intermediate new URL in the non-public
  Django `STATIC_ROOT` returned `404`; its base-template change was immediately
  reverted before the final public-webroot release.
- Final smoke, responsive checks, integration imports and error-log monitoring
  passed. Full evidence:
  `docs/mobile-info-cards-production-2026-08-01.md`.

### Equal-height correction release

- Artifact:
  `work/mobile-info-cards-equal-height-20260801.tar.gz`, SHA-256
  `81219c93954ea054111374e1c86259f9391c3934c0f9ae7d042a5819cc01c684`.
- Closed staging release:
  `/home/decpai/staging/releases/mobile-info-cards-20260801-r7-equal-height`,
  branch marker `ui/mobile-info-cards-equal-height-20260801`.
- Production backup:
  `/home/decpai/release-backups/mobile-info-cards-equal-height-20260801T142538Z`.
- The unique CSS was installed in source static and the real LiteSpeed public
  webroot, then verified publicly before the validator and base template were
  atomically replaced. The base template was switched last.
- Installed hashes:
  - base template
    `c396cf31defcd15308f7ae432461c50a14c9e7c2a46ef4df3e33daeacb36b5a7`;
  - source/public CSS
    `761a64754cab57ba1d1c380e281dc56c00fa01afc07903fab38b51a626ad23cc`;
  - validator
    `41da4fd2b280022e467d1d216b13c24bd9c42fb1646ef67140009017b15c6fdf`.

## Finnish SEO P0 production release 2026-08-02

- Approved source: closed staging
  `/home/decpai/staging/releases/seo-fi-p0-20260802-r7`.
- Production candidate was cloned outside the webroot at
  `/home/decpai/release-candidates/seo-fi-p0-20260802-r7-production` and tested
  against the real catalog in read-only mode.
- Exact code-only backup:
  `/home/decpai/release-backups/seo-fi-p0-20260802T171107Z`.
- Install order was support files, sitemap/URL routing, templates, then
  `shop/views.py`; the complete manifest was required to pass before touching
  `tmp/restart.txt`.
- No dependency, migration, database, static-collection or external-setting
  operation was part of the release.
- Production SEO, checkout, Paytrail, Merchant/Analytics/email import and
  error-log smoke passed. Evidence:
  `docs/seo-fi-p0-production-2026-08-02.md`.

## Menekkilaskuri desktop template release 2026-08-20

- Scope: `shop/templates/shop/product/detail.html` only.
- Exact pre-release production copy:
  `/home/decpai/public_html/deco/shop/templates/shop/product/detail.html.bak-20260820-before-desktop-calculator`.
- Passenger template cache was refreshed through the existing
  `/home/decpai/public_html/deco/tmp/restart.txt` mechanism.
- No database, static asset, product data, price, stock, cart, checkout or
  external integration write was part of this release.

## Country default language release 2026-08-20

- Added one middleware, four local FI/SE CIDR data files and one middleware
  entry immediately after Django's `LocaleMiddleware`.
- Exact settings backup:
  `/home/decpai/public_html/deco/config/settings.py.bak-20260820-before-country-language`.
- The middleware and CIDR data were installed first; `config/settings.py` was
  installed last, followed by the standard Passenger restart marker.
- No external lookup is made during page requests and no database or catalog
  content was modified.

## Google Customer Reviews order-language release 2026-08-20

- Scope: `order/templates/order/created.html` only.
- Exact pre-release template copy:
  `/home/decpai/public_html/deco/order/templates/order/created.html.bak-20260820-before-gcr-language`.
- The candidate was compiled before upload, read back byte-for-byte and then
  activated with the standard Passenger restart marker.
- No Python, database, order-processing, email, payment or Merchant payload
  logic changed.
