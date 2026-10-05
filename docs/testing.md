# Testing strategy

## Merchant storefront price parity 2026-10-05

- Python compilation passed for `google_shopping/tasks.py` and
  `google_shopping/tests.py`.
- The isolated local SQLite suite passed: 8/8 tests, including the exact 305
  variant choice and public regular price calculation.
- `check --deploy` completed with only the six established test-settings
  warnings for HSTS, SSL redirect, secure cookies, clickjacking middleware and
  the intentionally weak test secret.
- Repeat `python manage.py test google_shopping
  --settings=config.test_settings` on closed staging.
- Confirm the 305 fixture keeps offer ID `W03050TR0E` but emits `26.83 EUR`
  from storefront variant `W03050000E`.
- Confirm the automatic planner maps legacy offers by landing-page URL, skips
  offers owned by another data source and schedules existing offers only.
- Confirm each worker batch rechecks source ownership, calls update only, and
  reports zero additions and zero removals.
- Run a read-only catalog audit comparing each Merchant payload price with the
  initial visible regular price on its landing page; mismatches must be zero.
- Production pilot: update only 305, wait for Merchant processing, then verify
  its Merchant price and landing-page price are both `26.83 EUR` before any
  catalog batch is scheduled.

## Transactional email UTF-8 verification 2026-08-21

- Python compilation passed for `config/settings.py`, `config/test_settings.py`,
  `mail/views.py` and `shop/tests_order_email.py`.
- The targeted Django test command
  `python3 manage.py test shop.tests_order_email --settings=config.test_settings`
  was attempted locally, but this workspace Python does not have Django
  installed.
- DNS read-only check found SPF for `decopaint.fi`, a `default._domainkey`
  DKIM record and MX `mail.decopaint.fi`; `_dmarc.decopaint.fi` returned no TXT
  record.
- Added unit coverage for status-email text containing `Lähetetty`, asserting
  UTF-8 message encoding, branded From, Reply-To, plain text body and HTML
  alternative construction.

## Product-specific Menekkilaskuri evidence 2026-08-20

- Pure calculation suite: 7/7 tests `OK` for kg/m², m²/L, decimal commas,
  conservative ranges, explicit coats, totals already covering multiple coats,
  kg/L density conversion and unsafe-value rejection.
- Python compilation: `shop/material_calculator.py` and `shop/views.py` `OK`.
- JavaScript syntax: versioned mobile calculator asset `OK`.
- Browser smoke, Marmorino Naturale Fine at 20 m²: `30 kg`, two coats,
  recommendation `1 × 20 kg + 2 × 5 kg`.
- Browser smoke after changing area to 35 m²: `52.5 kg`, package recommendation
  covers 53 kg and never rounds below the calculated need.
- Browser smoke, 210 Biofondo Coprente: litre result from its own
  `14–18 m²/L`; tool product Efektiharja correctly has no calculator.
- Read-only catalog audit: all 154 product pages returned successfully, no
  legacy generic values and no invalid calculator configurations.

The calculator deliberately rejects concentrations, dilution ratios, malformed
area units and mass/volume mismatches without an explicit density.

## Product Open Graph and structured-data R8 evidence 2026-08-02

- Local static validation and Python compilation: `OK`.
- Closed staging static validator: `OK`; `makemigrations --check --dry-run`:
  `No changes detected`.
- Closed staging Django suite: 17/17 tests, `OK`; includes safe JSON script
  escaping, Product without unresolved Offer, exact PreOrder Offer, template
  blocks and synthetic product render/canonical coverage.
- `manage.py check`: only the established legacy non-unique email warning;
  `check --deploy` also reports the established HSTS warning.
- Production read-only render audit: 154 products, 154 valid, zero errors,
  115 exact Offers and 39 Product-only pages; largest HTML 304,565 bytes.
- Public parity checks: Sterylfix 26.77/InStock, Sterylplus 30.72/PreOrder,
  Ultrasaten 48.00/InStock and Veldecor 52.86/PreOrder exactly matched the
  existing price endpoint and order-product flag.
- Final public smoke: homepage, both product types, empty checkout and payment
  methods HTTP 200. Warm response times were 0.081–0.214 seconds.
- GA4 loader, analytics asset, product payload and default consent marker
  remained present. Merchant/Shopping code was not changed or invoked.
- `stderr.log` grew only 92 bytes during Passenger restart, then stayed at
  7,483,759 bytes; the delta contains zero error/traceback markers.
- The production test command was additionally attempted but correctly could
  not create `test_decpai_django` because the production DB user lacks CREATE
  permission. It stopped before tests ran and made no DB change; the same exact
  code had already passed 17/17 on isolated staging.

## Finnish SEO P0 closed-staging evidence 2026-08-02

- Final artifact: 12/12 hashes matched locally and on the server.
- Static SEO contract validator: `OK`.
- SEO, search, Analytics and database-backed route smoke suite: 27 tests,
  `OK`.
- Users, Paytrail and Google Shopping regression suite: 23 tests, `OK`.
- Changed template compilation: six templates, `OK`.
- `check --deploy`: only the two established staging warnings (HSTS disabled
  on closed staging and legacy non-unique email login).
- Synthetic database fixtures cover 11 category/landing intents, the tag-backed
  exterior landing page, five product pages, canonical stripping and four 301
  duplicate-tag redirects. No production product records or PII were copied.
- Post-activation internal smoke: homepage, catalog and search HTTP 200;
  Finnish `lang`, canonical and search `noindex,follow` present.
- External staging: HTTP 403 and
  `X-Robots-Tag: noindex, nofollow, noarchive`.
- Production homepage after staging activation: HTTP 200.
- Failed candidates were rejected before activation or immediately rolled back;
  complete evidence is in `docs/seo-fi-p0-staging-2026-08-02.md`.

## Source-grounded AI assistant candidate 2026-08-01

Local automated evidence:

- `python -m unittest -v shop.tests_ai_assistant`: 5 test methods, `OK`;
  the acceptance method validates every generated scenario.
- `scripts/validate_ai_assistant.py`: 154 knowledge products and 135 FI/SV/EN
  questions, `OK`.
- Scenario mix: 75 verified facts, 15 missing-context clarifications,
  15 grounded recommendations, 15 high-risk handoffs, 9 missing-document
  refusals and 6 prompt-injection blocks.
- Static contract confirms staging-only flags, POST + CSRF, no-store/noindex,
  request/rate limits, no external AI call, no chat persistence and visible
  source links.
- Python syntax checks pass for the engine, views, URL wiring, tests, settings
  builder and validator.

Required closed-staging gates:

1. Verify the current staging release and external 403/noindex before work.
2. Create an immutable release from the active staging target and verify the
   exact artifact manifest; do not edit the active release in place.
3. Keep the isolated SQLite DB, locmem email backend, Merchant kill switch and
   Analytics kill switch; do not import production products or PII.
4. Run `shop.tests_ai_assistant_view`, the 135-case validator, the isolated
   full Django suite and `check --deploy` in the staging virtualenv.
5. Smoke GET rendering, CSRF-protected POST, all three languages, source links,
   refusal/handoff behavior, keyboard focus and 360/390/430 px layouts.
6. Confirm the public staging hostname remains 403/noindex and production
   homepage remains healthy and unchanged.

The Django view suite is present but cannot run in the local bundled Python
because Django is not installed there; it is a mandatory staging gate, not an
accepted omission.

## Source-grounded search candidate 2026-08-01

Local automated evidence:

- `python -m unittest -v shop.tests_search_engine`: 8 tests, `OK`.
- `shop.tests_search_view`: 2 Django integration tests for HTML/AJAX result
  contexts and availability filtering.
- `scripts/validate_search_engine.py`: 154 products, 9 golden queries, `OK`.
- `py_compile`: `shop/search_engine.py`, `shop/views.py`, both test modules and
  validator.
- Golden queries cover wooden-floor lacquer, exterior siloxane wall paint,
  nicotine stains, PVC primer, interior mould removal, concrete water
  repellency, `marmoriino`, radiator paint and rust converter.
- Unavailable products are excluded before and during ranking.
- Antiruggine does not receive PVC matches from its mislinked documents.

Required closed-staging gates:

1. Verify HTTP 403 and `X-Robots-Tag: noindex, nofollow, noarchive` externally.
2. Verify artifact manifest before activation and preserve the previous release.
3. Run the isolated Django suite and `check --deploy` with Analytics and
   Merchant mutations disabled.
4. Smoke search rendering and AJAX rendering with synthetic catalog fixtures.
5. Confirm production homepage remains unchanged and healthy.

Closed-staging evidence:

- exact seven-file manifest and clean archive SHA-256 matched on the server;
- no AppleDouble `._*` files in the release;
- targeted search suite: 10 tests, `OK`;
- golden validator: 154 products and 9 queries, `OK`;
- full isolated Django suite with the known staging redirect disabled for the
  test client only: 36 tests, `OK`;
- running the unchanged previous release with its normal staging setting
  reproduces the same 18 legacy `301 != 200` failures caused by
  `SECURE_SSL_REDIRECT=True`, proving they are not a search regression;
- `check --deploy`: only the two established staging warnings (HSTS disabled
  for closed staging and legacy non-unique email login);
- active server-side homepage, HTML search and AJAX search: HTTP `200`;
- index load: 154; Analytics and Merchant sync kill switches: `False`;
- WSGI import: `OK`; external staging: HTTP `403` plus noindex header;
- production homepage remained HTTP `200`.

## Product knowledge/search audit 2026-08-01

- Public catalog registry: 154 unique product URLs across 10 pages.
- Document inventory: 354 linked files, including 352 PDFs; all PDFs opened,
  hashed and classified, with zero extraction errors.
- Two image-only Calce Sostenibile brochures were rendered and visually checked.
- Representative technical sheet, safety sheet and brochure layouts were
  rendered and inspected.
- Knowledge-base validation: 154 unique product URLs, 154 non-empty exact-name
  alias sets and 154 rows in the source matrix.
- Confirmed-document guard: both Aggrappante documents linked to Antiruggine are
  flagged and excluded from technical search filters.
- Public search baselines verified for ten Finnish queries, including zero-result,
  exact-match and over-broad-result cases.
- Final seven-page PDF report rendered to PNG and visually checked on every page.
- No production write, database mutation, external sync or Analytics event was
  performed.

## Mobile UI candidate 2026-07-30

- Static template/CSS/commerce-contract validation:
  `scripts/validate_mobile_ui.py`.
- JavaScript syntax: `node --check shop/static/assets/js/mobile-modern.js`.
- Required staging viewports: 360×800, 390×844 and 430×932.
- Required journeys: homepage/menu, category/search, product variants and
  quantity, material estimate, cart, delivery, payment UI and consent controls.
- Run the existing isolated Django suite and `check --deploy`; no production
  orders, payments, emails, Merchant writes or Analytics requests are allowed.
- Compare staging Lighthouse against Performance 69, Accessibility 73,
  LCP 10.7 s, TBT 90 ms and CLS 0.

Closed-staging evidence:

- all 12 candidate checksums matched;
- mobile UI static validator passed for 11 files;
- 9 changed templates compiled;
- final isolated suite: 26 tests, `OK`;
- home, catalog and empty checkout server-side smoke: HTTP 200;
- Analytics and Merchant writes disabled;
- external staging remained HTTP 403 with
  `X-Robots-Tag: noindex, nofollow, noarchive`;
- the staging database contains no products, so product-detail visual testing
  remains fixture-dependent and no production catalog was copied.

Production release evidence:

- exact artifact SHA matched locally and on the server;
- stale server transport file was rejected before production write;
- nine templates compiled and all 11 installed hashes matched;
- `collectstatic`: two copied, 399 unchanged;
- homepage, catalog, empty checkout, terms, a real product and both mobile
  static assets: HTTP `200`;
- real product contains mobile calculator markup and `view_item`;
- Paytrail creation GET: `405`; unsigned success callback: `403`;
- Merchant import: `OK`, effective sync flag: `True`;
- email backend import: `OK`, no message sent;
- Analytics real-product payload: `view_item`, no customer PII keys;
- final Passenger `stderr.log` delta: zero traceback/Internal Server Error
  markers;
- repeat health-check stayed HTTP `200`, with no further `stderr.log` growth;
- Django-Q process count remained at the established five-process baseline;
- database, migrations, orders, customers and external product/property
  settings were not changed.

## Source-grounded search production evidence 2026-08-01

- Production baseline before write: homepage, catalog, login, checkout and
  `/product/veldecor/` returned HTTP `200`.
- Previous `shop/views.py` SHA-256:
  `016dc46de4973bd76cc816fec535946c164267828d3efb21ad17721857004f28`;
  all six added paths were confirmed absent.
- Server candidate SHA-256 and all seven internal manifest entries matched the
  accepted closed-staging artifact; Python compile completed without error.
- Installed manifest verification: seven of seven files `OK` before Passenger
  restart.
- Production validator: `status=ok`, 154 products, 9 golden queries,
  unavailable products excluded and mislinked PDF terms excluded.
- External search smoke:
  `patterimaali`, `marmoriino` and `PVC pohjamaali` returned HTTP `200`;
  results contained Ecosmalto Thermo, Marmorino Naturale and Aggrappante
  Ecologico respectively, while Antiruggine was absent from the PVC page.
- Manual browser smoke showed one `patterimaali` result with a working product
  link, image, price and product name; browser console errors: zero.
- Post-release homepage, catalog, login, checkout and real product: HTTP `200`.
- Payment creation GET: `405`; unsigned success and cancel callbacks: `403`.
- Effective Merchant sync flag: `True`; email backend import:
  `django_q_email.backends.DjangoQBackend`; no sync or email was sent.
- GA4 tag and `view_search_results` were present on the rendered search page.
  A synthetic email-shaped search term was returned as `[redacted]` with only
  `search_term` and `result_count` parameters.
- `manage.py check --deploy` completed with the five established production
  security/legacy warnings and no error.
- Passenger `stderr.log` stayed exactly 7 482 318 bytes throughout the release
  and smoke window.
- No migrations, DB writes, synthetic orders, payments, Merchant mutations or
  Analytics configuration changes were performed.

## Автоматические уровни

### Security

- anonymous/owner/other-user/admin для каждого order endpoint;
- все мутации: POST, CSRF и permission;
- Paytrail invalid/valid/replayed signature;
- amount/currency/status mismatch;
- rate limits регистрации и email.

### Commerce

- цена Variant → cart → OrderItem snapshot → Paytrail amount;
- VAT 25,5%, B2B group tax и rounding;
- coupon percent/fixed/free-shipping;
- pickup, weight-based, PostNord locker/home;
- out-of-stock и order-product;
- duplicate submit/callback;
- cancel/refund state.

### Merchant

- stable offer ID;
- price/availability parity;
- required attributes;
- sync dry-run;
- delete endpoints недоступны через GET.

### SEO/analytics

- canonical/lang/hreflang;
- sitemap URL policy;
- JSON-LD schema validation;
- ecommerce payload schema, отсутствие PII;
- purchase idempotency.

## Ручной release smoke

1. Главная, category, search/filter, product.
2. Variant/quantity/cart.
3. Все методы доставки.
4. Paytrail sandbox success/cancel/timeout/replay.
5. COD только для допустимой доставки.
6. Confirmation email и admin notification.
7. Account order history и запрет чужого заказа.
8. Merchant test item/sync dry-run.
9. Consent reject/accept/revoke.
10. GA4 DebugView и duplicate check.
11. Mobile keyboard/screen reader basics.
12. 404/500 и отсутствие debug details.

## Baseline gates

- `python -m compileall`/AST: без syntax errors.
- `manage.py check --deploy`.
- migrations: `makemigrations --check --dry-run`.
- unit/integration tests зелёные.
- dependency vulnerability scan с утверждённой политикой severity.
- Lighthouse mobile не хуже baseline; LCP target установлен в SEO audit.

## Тестовые данные

Только synthetic customers/orders. Production PII не копируется. Карточные данные — исключительно официальные Paytrail sandbox fixtures.

## P0 staging evidence 2026-07-30

- 17 security/regression tests: `OK`.
- WSGI import: `WSGI_IMPORT_OK`.
- Python syntax: успешно.
- Закрытый staging: HTTP 403 и `X-Robots-Tag: noindex, nofollow, noarchive`.
- Production read-only preflight: HTTPS `200`, HTTP → HTTPS `301`, `DEBUG=False`.
- В кандидате production отсутствуют migrations и test-only settings.

## P0 production smoke 2026-07-30

- Clean archive SHA-256 совпал локально и на сервере.
- Installed SHA-256 всех семи runtime-файлов совпали с candidate.
- Production Python syntax: успешно.
- `manage.py check --deploy`: без новых предупреждений.
- Homepage, catalog, login, checkout и product: `200`.
- Anonymous чужой order endpoint: `302` to login.
- Payment creation GET: `405`.
- Неподписанные success/cancel callback: `403`.
- Dynamic product price loader завершился.
- После стабилизации Passenger повторные запросы не увеличили `stderr.log`.
- Production `._*` files: отсутствуют.

## Merchant order sync evidence 2026-07-30

- Python compile: успешно.
- Закрытый staging, targeted suite: 16 тестов, `OK`.
- Закрытый staging, full suite: 23 теста, `OK`.
- Покрыты online success, duplicate Paytrail callback, COD и distinct product
  IDs заказа.
- Покрыт upsert-only режим: отсутствие активной вариации не удаляет Merchant
  product в order-triggered flow.
- Покрыты правильные `pickupMethod`/`pickupSla`, отсутствие `storeCode` и
  нормализация legacy-ключей.
- Production import smoke:
  `MERCHANT_ORDER_SYNC_IMPORT_OK=1`.
- Production payload smoke:
  `PAYLOAD_COMPAT_OK=True`.
- Effective production flag:
  `MERCHANT_SYNC_EFFECTIVE=True`.
- Django-Q: один master и четыре worker после clean restart.
- Production homepage: `200`.
- `manage.py check --deploy`: пять известных baseline предупреждений, новых
  release-specific issues нет.
- Реальный production order не создавался. На следующем настоящем заказе нужно
  подтвердить одну completed `sync_order_products` задачу и отсутствие
  повторной задачи при replay callback.

## GA4 ecommerce candidate 2026-07-30

Automated:

- opaque User-ID stable and contains no profile data;
- search term redacts email/phone-like content;
- purchase payload uses order snapshot values and `DP-{order_id}`;
- purchase payload excludes customer PII and provider transaction ID;
- repeated success callback yields one page event per browser session;
- JavaScript syntax, Python compile and six-template compile pass;
- full isolated Django suite: 26 tests, `OK`.

Staging manual matrix:

1. `ANALYTICS_ENABLED=False`: no request to GA/Ads.
2. Reject all: no custom ecommerce event.
3. Analytics only: ecommerce events enabled, ad signals remain denied.
4. Marketing accepted: all four Consent Mode v2 ad signals match the UI.
5. Reopen settings and revoke: future custom events stop.
6. Synthetic product → checkout → signed payment success; inspect payload
   without production PII and confirm refresh dedupe.

## GA4 ecommerce release evidence 2026-07-30

- Artifact SHA-256 совпал локально и на сервере:
  `520af62b635e5f0be39f24cf3d4df45f1f9265dfedff811b915fb2cbdfebb704`.
- Closed staging full suite: 26 тестов, `OK`.
- Staging Python compile: код `0`; Django check: без release-specific issues;
  template compile: `templates-ok`.
- Closed staging: HTTP `403` и
  `X-Robots-Tag: noindex, nofollow, noarchive`.
- Production installed manifest 12 runtime-файлов полностью совпал с
  candidate.
- Production Python compile: успешно.
- `manage.py check --deploy`: пять известных baseline warnings, новых
  release-specific issues нет.
- Homepage, catalog, login, checkout, terms, product и public analytics JS:
  HTTP `200`.
- Product `Veldecor` формирует allowlisted `view_item`:
  `item_id=TV00V0293S`, `currency=EUR`, без PII.
- Авторизованный GA4 config содержит только opaque User-ID `dp_…` и
  `login_status=authenticated`.
- Consent settings повторно открываются и содержат раздельные controls для
  analytics, marketing, ad measurement и ad personalization.
- GA4 Realtime показывает `view_item` после production release.
- `stderr.log` не вырос во время post-release browser smoke.
- Production purchase намеренно не создавался; purchase/value/deduplication
  остаются обязательной проверкой на следующем настоящем заказе.

## Verified search placeholder evidence 2026-08-01

- Candidate manifest and server archive checksums matched before extraction.
- `scripts/validate_mobile_ui.py`: `MOBILE_UI_STATIC_CHECKS_OK=1`, 11 files.
- `scripts/validate_search_engine.py`: status `ok`, 154 products, 9 golden
  queries, unavailable products excluded, mislinked PDF terms excluded.
- `python -m unittest shop.tests_search_engine`: 8 tests, `OK`.
- Candidate Python compilation succeeded.
- `manage.py check --deploy --settings=config.settings_mobile_ui` completed
  without errors; the two existing staging warnings were HSTS configuration
  and the legacy non-unique email username field.
- Isolated staging homepage returned `200`, contained
  `Esim. patterimaali`, and did not contain `kylpyhuoneen seinä`.
- The isolated staging database intentionally contains no production product
  copy; suitability of `patterimaali` was therefore gated by the checked
  source-grounded index and then confirmed by the production read-only smoke.
- Production read-only smoke: homepage, catalog and
  `/catalog/search/?q=patterimaali` returned `200`; the search page reported
  one result and linked to `Patterimaali Ecosmalto Thermo`.
- Browser at `390×844`: new placeholder count `1`, old placeholder count `0`,
  search result link count `1`, console error count `0`.
- Server error log remained 7 482 318 bytes with unchanged mtime.

## Mobile information cards staging evidence 2026-08-01

- Candidate manifest verified on the server:
  - template SHA-256
    `60b3372eb02e8757e802289f880682be59a76453707aa656867709d2da78307d`;
  - source and collected mobile CSS SHA-256
    `6828f6c69d5a64b090480ee907977a06122a5533457ae483b1b152e9610e4501`;
  - validator SHA-256
    `3de5c8af0808b3df35757c8efd01d3ac342914324d3f8e8d65e5b31cbfafb056`.
- `python -m py_compile scripts/validate_mobile_ui.py`: passed.
- `scripts/validate_mobile_ui.py`: `MOBILE_UI_STATIC_CHECKS_OK=1`, 11 files.
- Django template loader compiled `shop/else/main.html` successfully.
- Internal Django homepage render: HTTP `200` and
  `INTERNAL_MOBILE_CONTRACT_OK=1` for both headings, all four existing benefit
  sprite IDs and all four original Oikos image filenames.
- `manage.py check --deploy --settings=config.settings_mobile_ui`: no errors;
  only the two known staging warnings (HSTS and non-unique email username).
- Post-switch release symlink points to
  `/home/decpai/staging/releases/mobile-info-cards-20260801`.
- External isolation check: HTTP `403` plus
  `X-Robots-Tag: noindex, nofollow, noarchive`.
- Production guard: homepage HTTP `200`; recorded template baseline
  `adb045645c2efbd9804c53d408c2d39c09c5760f057e8a9f6037cb48f017fcd9`
  and source/public CSS baseline
  `b1d600b10b8e64339fcfebf8ca289acee34b419fbb95c9770c8809e365d161d5`
  remained unchanged.

### Mobile card R2 narrow-screen protection

- The two-column card text column was reviewed at the 390 px phone breakpoint;
  long Finnish compounds were identified as the principal overflow risk.
- Added `hyphens: auto`, `overflow-wrap: break-word` and `min-width: 0` to
  service titles, quality titles and compact captions without changing the
  approved card dimensions or icon assets.
- R2 manifest verified on the server:
  - CSS SHA-256
    `b87400ef247ec86f529f2788283fb3568622a74510b94dd65594d193dad9d382`;
  - validator SHA-256
    `167972f7193e0552e2f429bbc6870556a724471472a91fb21405d77b28e559f7`.
- Before activation: Python compile passed, 11-file static validator passed and
  Django deploy check had only the same two known staging warnings.
- After activation: active static validator passed; internal homepage returned
  `200`; both headings and all eight original icon references were present;
  source and collected CSS hashes matched R2.
- External staging remained `403` with
  `X-Robots-Tag: noindex, nofollow, noarchive`; production remained `200` and
  all recorded production template/CSS baselines stayed unchanged.

## Mobile information cards production evidence 2026-08-01

- Final candidate manifest verified on staging and production:
  - base template SHA-256
    `9eb3897607ec5254cbb04c9bc0001d72edf9d9c5b85c37a5475da20f812dfd79`;
  - homepage template SHA-256
    `60b3372eb02e8757e802289f880682be59a76453707aa656867709d2da78307d`;
  - final mobile CSS SHA-256
    `b87400ef247ec86f529f2788283fb3568622a74510b94dd65594d193dad9d382`;
  - validator SHA-256
    `86c260f07991cf39b7fdd09078d84ab79079d010ac89b88089bdcbedc92653f4`.
- Static mobile contract: `MOBILE_UI_STATIC_CHECKS_OK=1`, 11 checked files.
- Django template loader compiled the base and homepage templates.
- Production `manage.py check --deploy` reported only the five documented
  baseline warnings and no release-specific error.
- HTTP smoke: homepage, catalog, `/product/210-biofondo-coprente/`, checkout,
  terms and final CSS all returned `200`.
- Security smoke: `/order/create_payment/` GET returned `405`; unsigned
  payment-success and payment-cancel returned `403`.
- Homepage contained exactly one final CSS link and both approved mobile
  headings. The public CSS bytes matched the candidate SHA-256.
- At 390 px, service cards measured 92–99 px high with 44 px icons and quality
  cards 104–118 px high with 54 px original marks. Titles were 14–15 px and
  supporting captions 12 px.
- At both 390 px and 360 px, document, service section and quality section
  `scrollWidth` equalled `clientWidth`; all eight cards were visible.
- `MERCHANT_SYNC_ENABLED=1`, `shop.analytics` imported and the configured mail
  backend initialized without sending mail. No synthetic order or payment was
  created.
- Error log baseline/current: 7,482,412 / 7,483,070 bytes; zero new critical
  patterns after release and browser smoke.

### Equal-height regression check 2026-08-01

- User-reported viewport reproduced at 472 px before the change:
  `Nopea toimitus=92 px`, `Ympäristöystävälliset maalit=99 px`.
- The mobile CSS contract now requires flex-stretched column wrappers and
  `height: 100%` on service cards.
- Closed staging R7: manifest passed, 11-file static validator passed, internal
  homepage returned `200`, and Django deploy check showed only the two known
  staging warnings.
- Production after reload at 472 px: upper pair `99/99 px`, lower pair
  `92/92 px`; document `scrollWidth=clientWidth=472`.
- Homepage, catalog, real product, checkout, terms and the new CSS returned
  `200`; payment-create GET stayed `405`, unsigned success/cancel stayed `403`.
- Error log baseline/current: 7,483,070 / 7,483,164 bytes; zero new critical
  patterns and zero temporary `.new` files.

## Finnish SEO P0 production evidence 2026-08-02

- Production baseline before write: homepage, catalog, search, a real product,
  empty checkout and login returned `200`; `/catalog/ulkomaalit/` returned
  `404`.
- R7 archive and manifest matched the accepted staging hashes; all 12 internal
  hashes passed on the isolated production clone and after installation.
- Preflight: Python compile, static SEO validator, ten metadata/template unit
  tests, six-template compile and read-only real-catalog renders passed.
- `manage.py check --deploy`: five established production warnings and no new
  release-specific error.
- Post-release homepage, catalog, search, exterior landing page, Marmorino
  Naturale, checkout, login and sitemap: `200`.
- Duplicate tag redirects: four permanent `301` responses to the canonical
  category URLs.
- Browser metadata: Finnish `lang`, page-specific title/description/H1,
  `index,follow` and clean canonical on indexable pages; search is
  `noindex,follow` with canonical query removal.
- Sitemap: 247 URLs; exterior landing present; internal search absent.
- Search result: `Patterimaali Ecosmalto Thermo`; browser console errors: zero.
- Paytrail: payment-create GET `405`; unsigned success/cancel `403/403`.
- Merchant sync flag `True`; Analytics/Merchant/mail imports passed without an
  external write or email.
- Product page: one `view_item`, one gtag loader, EUR currency and zero
  customer PII keys.
- Error log: 7,483,391 → 7,483,667 bytes; delta critical markers `0`, PII
  markers `0`; stable after repeated homepage/catalog/product/checkout `200`.
- No production DB, order, payment, email, Merchant sync or Analytics setting
  was created or changed.

## Menekkilaskuri desktop verification 2026-08-20

- Live product page checked at a 1280 px desktop viewport: calculator is
  visible, styled and interactive.
- Marmorino Naturale Fine at 20 m² reports 30 kg and recommends
  `1 × 20 kg + 2 × 5 kg`.
- Changing the area to 35 m² reports 52.5 kg and recommends packages totalling
  53 kg.
- The desktop rules apply only from 768 px; the existing mobile layout and
  calculator behaviour remain unchanged.

## Country default language verification 2026-08-20

- Finnish IP: `fi`; Swedish IP: `sv`; public IP outside FI/SE: `en`.
- LiteSpeed/GeoIP country-header precedence is covered.
- Manual cookie precedence and Finnish crawler behaviour are covered.

## Google Customer Reviews language verification 2026-08-20

- The production order-confirmation template compiles successfully.
- The GCR locale expression renders `fi`, `sv` an