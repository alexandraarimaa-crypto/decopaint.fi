# Changelog

## 2026-10-05 - Merchant storefront price parity

### Fixed

- Merchant payloads keep their existing stable offer ID while taking price and
  availability from the variant selected on the initial product-page load.
- Merchant prices use the public regular customer price shown in parentheses,
  without product, coupon or dealer discounts.
- The 305 BioLavabile regression is covered explicitly: legacy offer
  `W03050TR0E` resolves to storefront variant `W03050000E` and `26.83 EUR`.

### Safety

- No product, price, order, customer, payment, stock or delivery row changes.
- No Merchant deletion is part of this change. Rollout starts with dry-run and
  one control product before bounded catalog batches.

## 2026-08-21 - Transactional email UTF-8 headers

### Fixed

- Branded transactional emails now build a real plain-text body plus the HTML
  alternative instead of using HTML as the text part.
- Outgoing messages explicitly use UTF-8 MIME encoding, preserving Finnish and
  Swedish letters such as `ä`, `ö` and `å` in subjects and body text.
- Added a branded `From` display name and a stable `Reply-To` address for
  order-status and other site-generated messages.

### Safety

- No order, customer, payment, product, stock, price, cart or checkout data was
  changed.
- Public DNS currently has SPF and a `default` DKIM key, but no DMARC TXT
  record was found; domain-level mail authentication still needs a DNS update
  to reduce Outlook spam marking.

## 2026-08-20 - Google Customer Reviews order-language binding

### Fixed

- The Google Customer Reviews opt-in now receives the active order-confirmation
  language instead of independently choosing the browser or Google-account
  locale.
- Finnish, Swedish and English order confirmations request `fi`, `sv` and `en`
  respectively from the Google module.

### Safety

- Merchant ID, unique order ID, customer email, delivery country, estimated
  delivery date and optional GTIN payload fields are unchanged.
- No order, customer, email, product, price, stock or advertising data changed.

## 2026-08-20 - Country-based initial storefront language

### Changed

- New visitors from Finland default to Finnish, visitors from Sweden default
  to Swedish, and visitors from other countries default to English.
- A customer's explicit language-cookie or session selection always wins.
- Search and Merchant crawlers retain Finnish so the Finnish canonical pages
  are not reinterpreted through a foreign crawler location.

### Safety

- Country lookup uses local CC0 FI/SE IP ranges and optional hosting headers;
  it makes no external request during page loads.
- No product, price, discount, stock, order, cart or advertising data changed.

## 2026-08-20 - Menekkilaskuri on desktop

### Changed

- Made the same product-specific material calculator available on desktop
  product pages with desktop-only responsive styling.
- Kept the existing calculation, source data, units and package optimiser
  unchanged; kg products continue to produce kg results.

### Safety

- No product, price, discount, stock, colour, variant, cart, checkout or other
  storefront behaviour was changed.
- Verified the live desktop page at 1280 px and retained the existing mobile
  layout below 768 px.

## 2026-08-20 - Product-specific Menekkilaskuri

### Fixed

- Removed the global hard-coded `9 m²/L`, two-coat and litre-only calculation
  from product pages.
- The calculator now parses each product's own `Attribute.sufficiency`, uses
  the conservative end of a range, reads an explicitly documented coat count
  and reports kg or L according to the active package unit.
- Added density-based conversion when `Riittoisuus` and sale packages use
  different mass/volume units; conversion is disabled when `Tiheys` is absent
  or ambiguous.
- Added a package optimiser that recommends a combination that covers the
  calculated requirement with the least excess and then the fewest packages.
- Products without a valid area rate or compatible package information no
  longer display a misleading calculator.

### Safety

- No database, product, price, stock, colour, variant, cart, checkout,
  Merchant or Analytics data was changed.
- Seven unit tests and a read-only 154-product production render audit cover
  mass, volume, density conversion, ranges, coats and invalid data.
- Evidence: `deployments/2026-08-20-material-calculator.md`.

## 2026-08-20 - GitHub recovery baseline

### Recovered and added

- Consolidated the sanitized Django source and all locally recoverable code
  releases into a single Git branch.
- Added the previously untracked source-grounded search module, mobile source
  assets, Merchant/analytics follow-ups, and Product Open Graph/JSON-LD R8.
- Added the cart root route, permanent redirects observed in GA4, and social
  footer links recovered from prepared patches.
- Added environment-based settings, a secret-free environment template, CI,
  pull-request controls, project documentation, selected CMS content exports,
  and the mobile prototype.
- Added a GitHub Copilot custom agent and repository-wide GitHub-first
  instructions so website changes use issues, branches, commits, CI, and pull
  requests instead of direct server edits.
- Restored the controlled 154-product search index and overrides required by
  the search release and its CI validator.
- Corrected the incompatible `django-rosetta` pin and restored the missing
  `django-mptt` dependency so the Django 4.1 dependency set can be installed
  in a clean CI environment.
- Documented the boundary between Git-controlled source and external runtime,
  database, media, advertising, analytics, payment, and hosting state.

## 2026-08-02 — Product Open Graph and structured data R8

### Added and changed

- Enabled product Open Graph metadata in the base template: product title,
  description, canonical URL, absolute image, site name and Finnish locale.
- Replaced the hidden legacy Product JSON-LD with escaped, valid JSON generated
  from visible product data and the OIKOS brand.
- Added an Offer only when the storefront resolves one concrete default variant
  with the same selection rules as the visible AJAX price. `order_item` maps to
  `PreOrder`; regular stock maps to `InStock`.
- Kept ambiguous multi-variant pages as Product-only markup instead of
  inventing a price or availability.

### Validation and safety

- Closed staging: static validator, no migrations and 17/17 tests passed.
- Production read-only audit: 154/154 active products valid; 115 exact Offers,
  39 intentionally without Offer; largest rendered product HTML 304,565 bytes.
- Four representative products matched structured-data price and availability
  exactly with the public AJAX endpoint.
- Homepage, stock/order products, checkout and payment methods returned 200;
  GA4, consent and the Merchant implementation remained unchanged.
- No database, order, customer, product, price, stock, delivery, Paytrail,
  Merchant or Analytics configuration write was performed.
- Evidence: `docs/seo-product-og-r8-production-2026-08-02.md`.

## 2026-08-02 — Finnish SEO P0 closed-staging release

### Added and changed

- Activated the approved source-grounded Finnish SEO P0 package only on closed
  staging release `/home/decpai/staging/releases/seo-fi-p0-20260802-r7`.
- Added unique Finnish metadata, heading contracts and canonical handling for
  homepage, catalog, priority category/landing intents and five P0 products.
- Added canonical tag redirects, search `noindex,follow`, a code-only exterior
  landing page, sitemap entry and stronger canonical internal links.
- Added database-backed synthetic SEO route tests so the isolated empty staging
  DB can validate category, landing and product templates without production
  catalog or PII.

### Validation and safety

- 27 SEO/search/analytics tests and 23 users/Paytrail/Shopping tests: `OK`.
- 12 artifact hashes, static SEO validator and six template compiles: `OK`.
- External staging remains HTTP 403 with noindex/noarchive; production homepage
  remained HTTP 200.
- No migrations, DB writes, product/price/stock changes, Merchant or Analytics
  mutations, and no production deployment.
- Full evidence: `docs/seo-fi-p0-staging-2026-08-02.md`.

## 2026-08-02 — Finnish SEO keyword and landing-page research

### Added

- Read-only анализ ассортимента, категорий, on-page SEO и подтверждённой базы
  154 товаров / 352 PDF.
- Карта из 32 финских поисковых кластеров с интентом, единственной основной
  страницей, действием и технической границей.
- Черновики Title, Meta Description и H1 для приоритетных категорий и товаров.
- План устранения tag/category каннибализации, query canonical, `lang`,
  заголовков, alt, внутренних ссылок, FAQ, schema и недостающих landing/guides.

### Safety

- Biomalta не позиционируется как `mikrosementti` без официального PDF.
- Для влажных зон предусмотрена только экспертная decision/handoff page до
  подтверждения систем.
- Production, staging, товары, URL, Merchant Center и Analytics не изменялись.

## 2026-08-01 — Source-grounded AI assistant research candidate

### Added

- Подготовлен подробный risk/architecture/cost/GDPR отчёт для трёхъязычного
  помощника Deco Paint, основанного только на подтверждённых карточках и PDF.
- Создан закрытый staging-кандидат без внешней языковой модели, API-ключей,
  Analytics, browser storage и сохранения чатов.
- Реализованы обязательные уточнения, отказ при отсутствии технического PDF,
  ссылки на источники, high-risk handoff, rate limit, CSRF и защита от базового
  prompt injection.
- Сгенерирован и локально проверен набор из 135 FI/SV/EN acceptance-вопросов.

### Safety

- Кандидат доступен только при одновременных флагах `STAGING=True` и
  `AI_ASSISTANT_PROTOTYPE_ENABLED=True`; production-настройки возвращают 404.
- Нет migrations, изменений БД, заказов, клиентов, цен, остатков, Merchant
  Center, Analytics или платёжных интеграций.
- Production не изменялся. Server-side closed-staging deployment ожидает
  активной cPanel-сессии и завершения всех staging gates.

## 2026-08-01 — Source-grounded search staging candidate

### Changed

- Подготовлен ранжированный финский поиск по контролируемой базе 154 товаров.
- Поиск учитывает официально подтверждённые назначения, основания, область
  применения, способы нанесения, названия, бренды и ограниченные опечатки.
- Все слова запроса должны подтверждаться одним товаром; сырой HTML описания
  больше не используется как неограниченный технический источник.
- Во всех ветках выдачи применяется `available=True`.

### Source corrections

- Для Duaflex добавлено официально подтверждённое наружное применение.
- У пяти товаров удалено ошибочно извлечённое назначение по старым
  никотиновым/дымовым пятнам; оно не подтверждалось их техпаспортами.
- Antiruggine Ecologico не наследует PVC-совместимость из ошибочно
  прикреплённых PDF Aggrappante.

### Validation and safety

- 8 unit-тестов, 2 Django view-теста и 9 golden-query проверок проходят.
- Проверены 154 уникальных slug, исключение недоступных товаров и защита от
  неверно привязанного PDF.
- Исправлена выборка M2M-категорий через `prefetch_related`; Django view-тесты
  проверяют HTML и AJAX ветки и исключение недоступного товара.
- Кандидат code/data-only: без migrations, production DB, заказов, клиентов,
  цен, остатков, Merchant Center и Analytics.
- Выпуск установлен только на закрытый `noindex` staging release
  `/home/decpai/staging/releases/search-source-grounded-20260801`.
- Отдельная server branch:
  `search/source-grounded-staging-20260801`, commit `5545c16`.
- Production не изменён; homepage после staging release отвечает `200`.

## 2026-08-01 — Read-only product PDF and search audit

### Added

- Инвентарь 154 публичных карточек, 352 PDF и двух вложений других форматов.
- Проверяемый черновик базы знаний с финскими названиями, типами продуктов,
  назначениями, основаниями, областью применения, способами нанесения,
  контролируемыми опечатками, связанными продуктами и PDF-доказательствами.
- Отчёт о полноте источников и контрольные примеры текущей/предлагаемой выдачи.

### Findings

- Подтверждена неправильная привязка документов: у Antiruggine Ecologico
  прикреплены технический паспорт и паспорт безопасности Aggrappante Ecologico.
- Девять материалов не имеют прикреплённого официального документа; девять
  материалов не имеют технического блока карточки; 38 карточек не имеют блока
  свойств.
- Текущий поиск не нормализует финские запросы/опечатки, не ранжирует результаты
  и в двух ветках не ограничивает выдачу `available=True`.

### Safety

- Аудит выполнялся только по публичным страницам и документам; production,
  база данных, карточки, цены, остатки, Merchant Center и Analytics не менялись.
- Общие брошюры и неверно привязанные PDF не используются как источник
  технической совместимости.

## 2026-07-30 — Audit baseline

### Added

- `AGENTS.md` с правилами безопасности и Definition of Done.
- Первичный аудит архитектуры, security, SEO, performance, analytics и privacy.
- Keyword map, data model, retention/privacy drafts.
- CRO, testing, deployment и rollback runbooks.
- Конфиденциальная локальная sanitized-копия части исходников для статического анализа.
- Локальный Git baseline sanitized-копии: commit `2a5b1a7`.

### Verified

- Доступ к cPanel, JetBackup, исходникам и публичному сайту.
- 7 ежедневных hosting backup; restore ещё не тестировался.
- Django monolith на LiteSpeed/Passenger + MySQL.
- Syntax scan: 214 Python files, текущих syntax failures не найдено.
- PageSpeed baseline для mobile/desktop.

### Security note

Найденный локальный archive с неожиданным OAuth secret был немедленно удалён локально и на сервере. Секреты и production PII не включены в документацию.

### Production changes

- На пустом `develop.decopaint.fi` отключён directory listing и добавлен `X-Robots-Tag: noindex, nofollow`.
- Проверка после изменения: HTTP 403.
- Не выполнялись изменения платёжных, заказных, клиентских, ценовых, налоговых, складских или delivery данных.

## 2026-07-30 — P0 staging candidate

### Prepared

- Branch `security/p0-staging`, commit `1425dc7`.
- Закрыт IDOR в payment details: login + owner/superuser check.
- Welcome-email endpoint больше не принимает произвольный адрес.
- Paytrail HMAC охватывает все `checkout-*` параметры.
- Добавлены merchant, amount, transaction и status checks.
- Paid/cancel transitions защищены DB lock и идемпотентностью.
- `pending`/`delayed` не помечают заказ оплаченным.
- COD confirmation привязан к owner/session.
- PII и browser-side enhanced-conversion payload удалены из confirmation template.
- Merchant mutations переведены на POST + CSRF и имеют staging kill switch.
- Добавлено 17 security/regression test scenarios.
- Создан secret-free staging settings builder и закрывающий staging `.htaccess`.

### Validation

- AST syntax check: 9 Python files успешно.
- Static security assertions успешно.
- Создан отдельный серверный release `/home/decpai/staging/releases/1425dc7`.
- Создан отдельный staging `SECRET_KEY` вне web root с правами `0600`.
- Создана отдельная SQLite-БД `/home/decpai/staging-data/decopaint.sqlite3`; production MySQL не подключался.
- Все staging migrations применены успешно.
- `manage.py check --deploy` проходит; остаются два ожидаемых предупреждения: отключённый HSTS для закрытого staging и legacy non-unique email login.
- Полный Django regression suite: 17 тестов, результат `OK`.
- WSGI import smoke-check: `WSGI_IMPORT_OK`.
- `develop.decopaint.fi` подключён к staging release, но закрыт через `Require all denied`.
- Внешняя проверка: HTTP 403 и `X-Robots-Tag: noindex, nofollow, noarchive`.
- Финальный воспроизводимый archive: `work/decopaint-p0-staging-final.tar.gz`.
- SHA-256 финального archive: `b898148d489cdbc51bee60e1be4218414cfd2882e894cab113c6d389f5237d84`.

### Production

Production code, DB, Paytrail, Merchant Center, orders и customer records не изменялись. Контрольная HTTP-проверка production после staging deployment: `200 OK`.

## 2026-07-30 — P0 production preflight

### Prepared

- Создан runtime-only production candidate:
  `work/decopaint-p0-production-candidate.tar.gz`.
- SHA-256:
  `2afa8df5277bc436cc32a9d9e8a806c58fca87682ac8d7522ba5247a85cc0a5f`.
- Зафиксированы исходные SHA-256 шести существующих production-файлов.
- Подтверждено отсутствие migrations и DB schema changes.
- Подготовлен точный code-only rollback plan.

### Verified

- Production HTTPS: `200 OK`.
- HTTP → HTTPS: `301`.
- `DEBUG=False`.
- Production source: 63 MB; свободно 222 GB.
- Passenger restart path существует.
- `manage.py check --deploy` выполнен в режиме чтения; пять известных
  конфигурационных/legacy предупреждений внесены в release review.

### Production

Production code, DB, Paytrail, Merchant Center, orders и customer records не
изменялись. Выпуск ожидает отдельного подтверждения владельца.

## 2026-07-30 — P0 production release

### Deployed

- Владелец отдельно подтвердил изменения Paytrail callback и order status.
- Установлен clean runtime archive
  `work/decopaint-p0-production-candidate-clean.tar.gz`.
- SHA-256:
  `b473544cad8f4487cabe0801ebbfe0ed89dac334fb89277a0934f5980fbdcc80`.
- Семь production-файлов совпали с candidate по SHA-256.
- Passenger перезапущен.

### Safety

- Создан и проверен закрытый code-only backup вне `public_html`.
- Backup SHA-256:
  `347baae5a49074aac73167eb347ff58ca85b676266db142a5908102849d574dd`.
- Миграции и изменения production DB, orders, customers, prices, VAT, stock,
  delivery и Merchant products не выполнялись.
- Первый archive со служебными macOS entries был отклонён до распаковки;
  production он не изменил.

### Verified

- Python syntax и Django check выполнены.
- Homepage, catalog, login, checkout и product отвечают `200`.
- Protected order endpoint требует login.
- Payment creation отклоняет GET.
- Неподписанные Paytrail callbacks отклоняются.
- После стабилизации новые smoke-запросы не добавили ошибок в `stderr.log`.
- Rollback не потребовался.

## 2026-07-30 — Merchant sync read-only dry-run

### Verified

- Выполнено сравнение набора товаров Merchant Center с текущей логикой выбора
  одной лучшей вариации сайта без изменений товаров.
- Merchant Center: 141 уникальный offer ID.
- Сайт: 154 допустимых уникальных offer ID.
- Полное совпадение: 121.
- Только на сайте: 33; только в Merchant Center: 20.
- Дубликаты offer ID и отсутствующие item code не найдены.
- Полный отчёт:
  `docs/merchant-sync-dry-run-2026-07-30.md`.

### Safety

- Не вызывались Merchant insert, update, delete или фоновая очередь.
- Существующие sync-процессы не запускались, поскольку они изменяют данные и не
  являются dry-run.

### Reconciliation

- 19 Merchant-only ID точно сопоставлены по названию и product URL с 19
  каноническими ID сайта.
- 14 website-only товаров не имеют старого Merchant-соответствия и являются
  кандидатами на добавление.
- Для Biomalta подтверждено: текущий ID сайта `1050N`, старый ID `1052FINE`;
  оба одобрены Google, поэтому старый ID отмечен только как кандидат на удаление.
- Создан проверенный Excel-отчёт с исходными данными, сопоставлениями, безопасной
  последовательностью и отдельной колонкой решения владельца.

## 2026-07-30 — Merchant additions-only execution

### Added

- После отдельного подтверждения владельца добавлены 14 новых товаров и 19
  канонических offer ID, всего 33 позиции.
- Финальная read-only сверка: Merchant Center содержит 174 уникальных offer ID;
  все 33 целевых ID присутствуют, отсутствующих нет.
- Первичная обработка Google: 18 одобрены, 15 ожидают проверки, отклонённых нет.

### Compatibility finding

- Production builder формирует устаревшие поля `pickup_SLA`,
  `pickup_method` и недопустимый top-level `storeCode`.
- Google отклонил первые запросы для 29 in-stock товаров без создания записей.
- Для подтверждённой additions-only операции ключи были нормализованы только в
  исходящем запросе: `pickupSla`, `pickupMethod`, без top-level `storeCode`.
- Постоянное исправление production sync-кода не выполнялось и требует staging,
  тестов и отдельного выпуска.

### Safety

- Merchant update и delete не выполнялись.
- Все 20 старых Merchant-only ID сохранены.
- Цены, остатки, availability, production DB, orders и customer data не
  изменялись.
- Четыре товара переданы с текущей website availability `out of stock`:
  `1059RETE`, `IAA000000J`, `TD103TR00D`, `TT0N10000E`.
- Полный отчёт обновлён:
  `docs/merchant-sync-dry-run-2026-07-30.md`.

## 2026-07-30 — Automatic Merchant sync after confirmed orders

### Changed

- Product payload теперь использует поддерживаемые Google Content API поля
  `pickupMethod` и `pickupSla`.
- Удалён недопустимый top-level `storeCode`; legacy payload дополнительно
  нормализуется перед отправкой.
- После подтверждённого online-платежа или создания COD-заказа в Django-Q
  ставится точечное обновление только товаров из этого заказа.
- Повторный Paytrail callback не создаёт повторную задачу.
- Order-triggered sync работает только в режиме upsert и не запускает удаление
  Merchant-позиций или полный catalog sync.

### Validation

- Отдельный закрытый staging release:
  `/home/decpai/staging/releases/merchant-sync-20260730`.
- Целевой набор: 16 тестов, `OK`.
- Полный Django suite: 23 теста, `OK`.
- Python compile, production import и payload compatibility smoke: успешно.
- Production homepage: `200`.
- После перезапуска работает один Django-Q master и четыре worker-процесса.
- Последний журнал очереди подтверждает clean restart и готовность процессов.
- `manage.py check --deploy` не выявил новых проблем; остаются пять известных
  security/legacy предупреждений из production baseline.

### Deployment and safety

- В production заменены только:
  `google_shopping/tasks.py` и `pk_paytrail/views.py`.
- Installed SHA-256 совпали со staging candidate:
  `dd1a87a6c265fb4cd4b512fa093556d09ac4ff438d0eb9a75ed9a3075ac6fac`
  и
  `db20b0969d109f7718ed8454cae14a2c06782824649e5ea8c9b85052c4280882`.
- Rollback backup:
  `/home/decpai/release-backups/merchant-order-sync-20260730`.
- Миграции, production DB, существующие заказы, клиенты, цены, остатки и
  Merchant products не изменялись.
- Тестовый production-заказ намеренно не создавался; end-to-end подтверждение
  должно быть выполнено на следующем реальном заказе по non-PII task evidence.

## 2026-07-30 — GA4 ecommerce and customer identity staging candidate

### Added

- Privacy-safe GA4 payload builders and client event dispatcher.
- Opaque HMAC User-ID for authenticated customers, consent-gated.
- Ecommerce events for product, cart addition, checkout, shipping, payment and
  confirmed purchase.
- Search event with contact-data redaction.
- Session and GA4 transaction-ID purchase deduplication.
- Unit/regression coverage for PII exclusion, stable User-ID and callback
  deduplication.

### Changed

- Direct `gtag` remains the only tag source; empty GTM container is not used.
- `page_location` no longer copies query parameters into Analytics.
- Google Signals is allowed only through Consent Mode choices.
- Consent settings include separate `ad_personalization`, no longer update on
  unsaved checkbox changes, and can be reopened from the footer.
- Privacy page documents GA4 and pseudonymous User-ID.

### Safety

- No migrations or production DB/customer/order changes.
- No raw or hashed email, name, phone, address, notes or Paytrail transaction
  ID is sent to GA4.
- Local Python/JavaScript syntax and six-template compile checks pass.
- Isolated synthetic Django suite: 26 tests, `OK`.
- Branch/commit: `analytics/ga4-ecommerce-staging` / `feea2a2`.
- Staging patch:
  `work/decopaint-ga4-staging-patch.tar.gz`;
  SHA-256 `520af62b635e5f0be39f24cf3d4df45f1f9265dfedff811b915fb2cbdfebb704`.

## 2026-07-30 — GA4 ecommerce production release

### Staging

- Загруженный archive повторно сверен по SHA-256; устаревшая серверная копия
  была отклонена до распаковки и заменена точным candidate.
- Создан отдельный release
  `/home/decpai/staging/releases/ga4-ecommerce-20260730` на базе последнего
  Merchant sync release.
- Удалены только служебные macOS `._*` entries внутри нового staging release;
  повторный Python compile завершился с кодом `0`.
- `ANALYTICS_ENABLED=False` подтверждён в isolated settings.
- Полный server-side Django suite: 26 тестов, `OK`.
- Django system check и компиляция изменённых templates: успешно.
- Staging symlink атомарно переключён на новый release.
- Внешний staging остался закрыт: HTTP `403`,
  `X-Robots-Tag: noindex, nofollow, noarchive`.

### Production

- Выполнен code-only release 12 runtime-файлов; migrations и изменения БД
  отсутствуют.
- Installed SHA-256 manifest полностью совпал с staging candidate.
- Новый static JS опубликован по фактическому URL
  `/static/assets/js/analytics.js`; HTTP `200`, checksum совпадает с source.
- `collectstatic --noinput`: 399 файлов; Passenger перезапущен.
- Homepage, catalog, login, checkout, terms, product и analytics JS отвечают
  `200`.
- Реальный product page формирует allowlisted `view_item` с EUR, SKU, названием,
  брендом, ценой и категорией.
- Авторизованный HTML содержит только opaque `dp_…` User-ID и login status;
  имени, email, телефона и адреса в GA4 config нет.
- Consent UI подтверждает отдельные controls для analytics, ad storage,
  ad user data и ad personalization и поддерживает повторное открытие.
- GA4 Realtime показывает `view_item` после release.
- До и после post-release smoke размер и timestamp `stderr.log` не изменились.

### Safety and rollback

- Backup существующих девяти production-файлов:
  `/home/decpai/release-backups/ga4-ecommerce-20260730-2135/runtime-before.tar.gz`.
- Backup SHA-256:
  `095ff91db68b5923f3162a5e91fa080f071b68faaad3ccdcf744e574ac42815a`.
- Manifest candidate и installed checksums сохранены рядом с backup.
- Production DB, orders, customers, Paytrail data, prices, VAT, stock,
  delivery и Merchant products не изменялись.
- Synthetic production order не создавался. `purchase` и deduplication должны
  быть подтверждены на следующем реальном заказе по non-PII
  `transaction_id=DP-{order_id}`.
- GA4 key-event configuration намеренно не менялась до подтверждения первого
  production `purchase`.

## 2026-07-30 — Mobile UI production release

### Deployed

- После отдельного подтверждения владельца в production установлен
  11-файловый mobile UI artifact.
- Artifact SHA-256:
  `796a31f40a02ab8ac3a448a451674c6907a148300eabb2e3fc45e0b74080d05c`.
- Обновлены mobile homepage, menu, catalog cards, product material calculator,
  sticky CTA, cart/checkout presentation и consent choice, не меняя
  commerce-контракты.
- `collectstatic`: два новых файла скопированы, 399 не изменились; public
  mobile CSS/JS опубликованы и сверены по checksum.

### Safety

- Первый запуск отклонил старый server-side archive до production write.
- Фактический backup:
  `/home/decpai/release-backups/mobile-ui-20260730T202101Z`.
- Runtime backup SHA-256:
  `c7c0e5078537f08f8db4b8b307a78d1f168ef194b0055b96e02926843035c5020`.
- Database, migrations, orders, customers, prices, VAT, stock, delivery,
  Paytrail callback, Merchant products и GA4 settings не изменялись.

### Verified

- Все 11 candidate и installed checksums совпали.
- Девять templates compiled; пять известных Django warnings не изменились.
- Homepage, catalog, empty checkout, terms, real product, CSS и JS: HTTP `200`.
- Payment creation GET: `405`; unsigned callback: `403`.
- Merchant sync import/effective flag, Analytics import/config и email backend
  import проверены без внешней записи или отправки.
- Реальный `view_item` не содержит customer PII keys.
- В финальном `stderr.log` delta нет traceback или Internal Server Error.
- Rollback не потребовался.
# 2026-07-30 — Mobile UI staging candidate

- Converted the approved mobile prototype into a code-only Django staging candidate.
- Added a task-based mobile homepage, modern offcanvas menu, catalog tools,
  product-card hierarchy, material estimator, sticky add-to-cart CTA, improved
  cart/checkout presentation and accessible consent choice.
- Added explicit hero image dimensions/fetch priority and reduced font variants.
- Preserved existing cart, price, delivery, payment, Merchant and GA4 contracts.
- Production remains unchanged pending staging acceptance and separate approval.

## 2026-08-01 — Source-grounded Finnish search production release

### Deployed

- После отдельного подтверждения владельца exact closed-staging candidate
  установлен в production без migrations и без изменения базы данных.
- Search runtime теперь ранжирует 154 товара по подтверждённым карточкам и
  официальным PDF, учитывает финские синонимы и ограниченный список опечаток,
  использует AND-семантику понятий и исключает недоступные товары.
- Установлены только семь файлов: `shop/views.py`, поисковый модуль, два теста,
  валидатор и два versioned JSON-файла данных.

### Safety and verification

- Candidate SHA-256:
  `cb8498edb5b045d4ddda4833c3b63b9b4a30d31b0838c360226673a59071d897`;
  все installed checksums совпали с семифайловым manifest.
- Production backup:
  `/home/decpai/release-backups/search-source-grounded-20260801T093927Z`.
- Backup исходного `shop/views.py` имеет SHA-256
  `016dc46de4973bd76cc816fec535946c164267828d3efb21ad17721857004f28`;
  копия candidate в backup повторно совпала с release SHA-256.
- Golden validator: 154 товара, 9 запросов, unavailable exclusion и защита от
  ошибочной PVC-привязки Antiruggine — `OK`.
- Homepage, catalog, login, checkout, product и три production search запроса:
  HTTP `200`; визуальный smoke подтверждает `Patterimaali Ecosmalto Thermo`.
- Payment creation GET остался `405`; неподписанные success/cancel callback —
  `403`. Merchant sync effective flag — `True`; email backend импортируется;
  GA4 search event присутствует и редактирует контактные данные.
- `stderr.log` не изменился: 7 482 318 байт до и после smoke.
- Production DB, orders, customers, prices, VAT, stock, delivery, Paytrail,
  Merchant products и GA4 settings не изменялись.

## 2026-08-01 — Verified mobile search placeholder release

### Deployed

- На mobile homepage заменён только placeholder поисковой формы:
  `Esim. kylpyhuoneen seinä` → `Esim. patterimaali`.
- Новый пример выбран по source-grounded search index и подтверждён реальной
  production-выдачей: ровно один товар, `Patterimaali Ecosmalto Thermo`.
- Изменён один runtime-файл:
  `shop/templates/shop/else/main.html`; migrations, static assets и
  зависимости не затрагивались.

### Safety and verification

- Closed staging release:
  `/home/decpai/staging/releases/search-placeholder-verified-20260801`;
  branch marker: `ui/search-placeholder-verified-20260801`.
- Release archive SHA-256:
  `6c813082b7eb5db79ad5a4c2023420abbf763f060d03a75e714e5a88f395d20c`;
  installed template SHA-256:
  `adb045645c2efbd9804c53d408c2d39c09c5760f057e8a9f6037cb48f017fcd9`.
- Production backup:
  `/home/decpai/release-backups/search-placeholder-20260801T104718Z`;
  backed-up template SHA-256:
  `b4c8a7d3894a9f4825a6cce9d1f8dfca73a72853cfca11f777d332970ffae7c4`.
- Static mobile validation: 11 files; search validator: 154 products and 9
  golden queries; search unit suite: 8 tests, `OK`.
- Production homepage, catalog and `patterimaali` search: HTTP `200`.
  Mobile viewport `390×844` shows the new placeholder exactly once and the
  old placeholder zero times; browser console errors: zero.
- Passenger `stderr.log` stayed exactly 7 482 318 bytes before and after the
  release and smoke window.
- Database, orders, customers, prices, stock, delivery, Paytrail, Merchant
  Center and Analytics configuration were not changed.

## 2026-08-01 — Mobile information cards on closed staging

### Staged

- Added the approved mobile-only headings `Sujuvampi ostokokemus` and
  `Laatuominaisuudet` to the homepage.
- Reworked the four service cards and four quality cards into compact,
  readable two-column mobile layouts with larger type, tighter spacing and
  short supporting captions.
- Preserved the four existing benefit sprite symbols and the four original
  Oikos assets: Since 1984, Antibacterial, Washability and HACCP.
- Desktop and tablet presentation is unchanged; the new layout is scoped to
  the existing phone breakpoint.

### Safety and verification

- Closed staging release:
  `/home/decpai/staging/releases/mobile-info-cards-20260801`;
  logical branch marker: `ui/mobile-info-cards-staging-20260801`.
- Candidate archive SHA-256:
  `fce1307a56316c0f028ed92c1d41c0098659b081305a9f7bf6056b7f8bb87093`;
  all three manifest entries matched on the server.
- Static contract validator passed for 11 files; Django template compilation
  and an internal homepage render passed with HTTP `200` and all ten required
  headings/icon references present.
- `manage.py check --deploy` reported only the two known staging warnings:
  HSTS disabled on isolated staging and the legacy non-unique email username.
- Closed staging remains HTTP `403` externally with
  `X-Robots-Tag: noindex, nofollow, noarchive`.
- Production remained unchanged: homepage HTTP `200`; template and both
  source/public mobile CSS checksums matched the recorded baseline.
- No database, orders, customers, prices, stock, delivery, Paytrail, Merchant
  Center or Analytics data/configuration was changed.

### Responsive hardening R2

- Promoted the closed staging release to
  `/home/decpai/staging/releases/mobile-info-cards-20260801-r2`.
- Added Finnish automatic hyphenation and safe word wrapping to the compact
  service titles, quality titles and mobile captions. This prevents long
  compounds such as `Ympäristöystävälliset` from overflowing the narrow text
  column while preserving the approved two-column layout and original icons.
- R2 archive SHA-256:
  `3970d490c677209862505f439a049101bdea381f2091c36a8b75661b34e8ae45`.
- R2 source/public CSS SHA-256:
  `b87400ef247ec86f529f2788283fb3568622a74510b94dd65594d193dad9d382`.
- Post-switch static validator and internal homepage contract passed; staging
  isolation and the unchanged production baselines were reconfirmed.

## 2026-08-01 — Mobile information cards promoted to production

### Released

- Published the approved mobile-only sections `Sujuvampi ostokokemus` and
  `Laatuominaisuudet` on the production homepage.
- Service and quality cards use compact two-column phone layouts with larger
  type, larger icons, shorter supporting captions and Finnish word-wrapping
  protection.
- Preserved the existing benefit sprite icons and all four original Oikos
  quality marks. Desktop and tablet presentation remains unchanged.
- Published a unique stylesheet URL,
  `/static/assets/css/mobile-modern-20260801-final.css`, so clients cannot
  retain the previous seven-day cached stylesheet.

### Safety and verification

- Final artifact SHA-256:
  `1431298e36955e5d69c90eaa21cc878ee6b23747bba660138968cc33e4955062`.
- Closed staging active release:
  `/home/decpai/staging/releases/mobile-info-cards-20260801-r6`; external
  access remains `403` with `noindex, nofollow, noarchive`.
- Exact production backup root:
  `/home/decpai/release-backups/mobile-info-cards-20260801T133226Z`.
- Production homepage, catalog, real product, checkout, terms and final CSS
  returned `200`; payment-create GET stayed `405`, unsigned success/cancel
  stayed `403`.
- Mobile visual smoke passed at `390×844` and `360×800`; document and both
  card sections had equal client/scroll widths and no horizontal overflow.
- Merchant order sync remained enabled; Analytics and mail backend imports
  succeeded. No database, order, customer, price, stock, delivery, Paytrail,
  Merchant Center or Analytics configuration was changed.
- The release window added 658 bytes of normal restart output to `stderr.log`
  and zero new `Traceback`, `Internal Server Error` or `ERROR` patterns.

### Equal-height service card correction

- Made the two service cards in each mobile grid row stretch to the same
  height. At the user-reported 472 px viewport, the upper pair changed from
  `92/99 px` to `99/99 px`; the lower pair remains `92/92 px`.
- Published a new cache-safe stylesheet,
  `/static/assets/css/mobile-modern-20260801-equal-cards.css`.
- Closed staging, production page smoke, payment URL protection, responsive
  measurement and error-log monitoring all passed. No data or integration
  configuration changed.

## 2026-08-02 — Finnish SEO P0 promoted to production

### Released

- Published the approved R7 Finnish metadata, H1, canonical, search-robots,
  canonical redirects, internal links and virtual exterior-category package.
- `/catalog/ulkomaalit/` is now a code-only tag-backed canonical landing page
  and is included in the sitemap; no category or product row was created.
- Four duplicate tag URLs now return permanent `301` redirects to their
  canonical category URLs.

### Safety and verification

- Candidate SHA-256:
  `e30f02c2d320d06e057bedff436cbe82b084231af21bf8c4b2681962e98eb760`.
- Verified production backup:
  `/home/decpai/release-backups/seo-fi-p0-20260802T171107Z`;
  previous-files archive SHA-256:
  `5f50a82871e8ffec627b14a4b7b2cb201adf5ad2285d51bfac831dcf9fc79c03`.
- All 12 installed manifest entries passed; Python, static validation, ten
  unit tests, six-template compile and read-only real-catalog renders passed.
- Homepage, catalog, search, exterior category, real product, checkout, login
  and sitemap returned `200`; Paytrail security endpoints stayed `405/403/403`.
- Merchant sync remains enabled; Analytics and mail imports passed without an
  external write. The GA4 product payload contains no customer PII keys.
- The error-log delta was 276 bytes, with zero critical or PII markers, and
  remained stable on the repeat health check.
- No database, order, customer, price, tax, stock, delivery, payment,
  Merchant Center or Analytics configuration changed.
- Full evidence: `docs/seo-fi-p0-production-2026-08-02.md`.
