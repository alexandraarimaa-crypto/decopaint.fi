# Initial audit decopaint.fi

Дата: 30 июля 2026
Статус: исходная диагностика завершена; изменения платёжного, заказного и клиентского контуров не выполнялись. Публичный directory listing пустого staging закрыт обратимым правилом.

## Резюме

Сайт — работающий кастомный Django-магазин на shared hosting с Paytrail, PostNord, Google Merchant Center, GA4/Google Ads и SendGrid. Каталог и контент существуют, HTTPS работает, Consent Mode v2 частично реализован, резервные копии хостинга доступны.

Главный риск сейчас не дизайн, а эксплуатационный и security-долг: production работает с `DEBUG=True`, нет закрытого полноценного staging и Git deployment flow, cPanel без 2FA, в исходниках и логах присутствуют секреты/PII, а несколько endpoint допускают IDOR, GET-мутации или повторную обработку оплаты. Mobile LCP 11,9 с ограничивает продажи. GA4 не получает стандартную ecommerce-воронку.

## Проверенные доступы

Доступно:

- публичный сайт и каталог;
- cPanel, File Manager и Terminal;
- JetBackup 5;
- управление MySQL на уровне cPanel;
- исходники Django-приложения;
- текущие Google-сессии, ранее использовавшиеся для Ads, Analytics и Merchant Center.

Требуется для полного цикла:

- подтверждённый owner/admin доступ к Google Search Console;
- экспорт настроек GA4, Ads и Merchant Center для сопоставления conversion actions;
- Paytrail и PostNord sandbox/test credentials;
- SendGrid dashboard и журнал доставляемости;
- владелец юридических текстов и GDPR-решений;
- правила B2B: роли, цены, лимиты, одобрение и видимость данных;
- подтверждение допустимого набора обезличенных данных для staging.

Секреты из переданного PDF и найденных файлов в отчёте не воспроизводятся.

## Текущая архитектура

- Backend: Django 4.1.13, Python/Passenger, монолит.
- Сервер: LiteSpeed/cPanel shared hosting.
- БД: MySQL, около 282 MB.
- Приложения: shop, cart, order, users, Paytrail, PostNord, Google Shopping, B2B, blog, courses, services, mail.
- Очереди/кэш: django-q2 и Redis-пакеты присутствуют; cPanel cron отсутствует, механизм запуска кластера требует подтверждения.
- Статика/media обслуживаются из `public_html`.
- Production source около 63 MB без учёта полного медиа-архива.
- Git repository и CI/CD отсутствуют.

Подробнее: [architecture.md](architecture.md).

## Резервные копии и staging

- JetBackup хранит 7 ежедневных incremental backup, последний успешный backup — 30 июля 2026 около 03:18.
- Восстановление не тестировалось; наличие backup не равно проверенному rollback.
- `develop.decopaint.fi` не является копией приложения. Обнаруженный публичный directory index с `cgi-bin` закрыт 30 июля 2026; проверены HTTP 403 и `X-Robots-Tag: noindex, nofollow`.
- Закрытый staging, отдельная БД, `noindex`, HTTP auth и обезличивание данных отсутствуют.

## Критические риски

| Приоритет | Риск | Доказательство | Влияние |
|---|---|---|---|
| P0 | IDOR в деталях платежа | endpoint получает заказ только по числовому ID, без login/owner check | раскрытие данных заказа/платежа |
| P0 | Небезопасный success/COD flow | произвольный `order_id`, PII в шаблоне, повторная отправка писем/conversion | утечка PII, неверные конверсии |
| P0 | Оплата помечается успешной без строгой state machine | подпись проверяется, но статус/сумма/валюта/идемпотентность недостаточны | неверный статус заказа |
| P0 | PII в production logs | логируются POST/GET, имя, email, телефон, адрес и callback параметры | GDPR/компрометация данных |
| P0 | `DEBUG=True` | production settings | утечка технической информации |
| P0 | Секреты в source tree/scripts | hardcoded DB credential и OAuth client JSON | компрометация интеграций |
| P1 | Нет реального staging и Git flow | пустой публичный develop-host, 0 Git repos | риск любого релиза |
| P1 | cPanel без 2FA | статус cPanel security | захват хостинга при утечке пароля |
| P1 | GET-мутации Merchant Center | delete/sync endpoints без `require_POST` | CSRF/случайное удаление |
| P1 | Устаревший Django | 4.1.13 вне поддержки | известные уязвимости и несовместимость |
| P1 | Растущий `stderr.log` | 7,13 MB, тысячи traceback в истории | пропущенные ошибки и расход диска |
| P1 | Mobile LCP 11,9 s | PageSpeed Insights | потери SEO и конверсии |
| P1 | Нет ecommerce measurement | отсутствуют `view_item`, `add_to_cart`, `begin_checkout`, `purchase` | оптимизация Ads без данных |
| P2 | Технический SEO-долг | `lang=en`, нет Product JSON-LD/hreflang, duplicate meta | слабее сниппеты/индексация |

## SEO и производительность

Положительное:

- HTTPS и self-canonical на проверенных страницах;
- `robots.txt` и sitemap доступны;
- sitemap содержит 246 URL, явных cart/admin URL не найдено;
- главная имеет релевантный H1;
- каталог показывает 154 товара.

Проблемы:

- Finnish pages размечены как `<html lang="en">`;
- нет `hreflang`;
- нет Open Graph и JSON-LD Product/Offer/Breadcrumb/Organization;
- generic/duplicate meta description используется на разных типах страниц;
- каталог page 2 без H1 и с generic title;
- 4 из 16 изображений главной без alt;
- товар сначала server-side отдаёт цену `0,00` и пустую доступность, затем JS подставляет реальные данные;
- PageSpeed mobile: Performance 66, Accessibility 73, SEO 92, LCP 11,9 s;
- PageSpeed desktop: Performance 88, Accessibility 78, SEO 92, LCP 2,1 s.

Подробнее: [seo-audit.md](seo-audit.md).

## Analytics и privacy

- Прямой `gtag`, без GTM.
- GA4 и Google Ads tag присутствуют.
- Consent Mode v2 по умолчанию запрещает analytics/ad storage в EEA и обновляется после выбора.
- Стандартные ecommerce events в исходниках не найдены.
- Страница заказа отправляет Google Ads enhanced conversion `user_data` и conversion event.
- Отправка привязана к просмотру страницы, а не к серверно подтверждённому одноразовому событию.
- Требуется проверка consent gating, дедупликации и запрета PII в analytics payload/logs.

Подробнее: [analytics-measurement-plan.md](analytics-measurement-plan.md) и [privacy-flow.md](privacy-flow.md).

## Топ-20 задач по влиянию

1. Закрыть IDOR `load_payment_details`; добавить auth + owner/admin check.
2. Перестроить Paytrail success/cancel в идемпотентную state machine с проверкой signature, status, amount, currency и transaction ID.
3. Удалить PII/debug payload из логов и настроить rotation/retention.
4. Отключить `DEBUG`, включить безопасные production settings и custom 4xx/5xx.
5. Ротировать найденные DB/OAuth секреты и вынести всё в environment/secrets.
6. Включить 2FA для cPanel и ревизию пользователей/FTP/DB.
7. Создать закрытый staging с отдельной БД, `noindex`, HTTP auth и обезличенными данными.
8. Создать Git-репозиторий, ветки, protected main и deployment checklist.
9. Обновить Django по поддерживаемому пути после тестов зависимостей.
10. Устранить GET-мутации и добавить CSRF/rate limits к чувствительным endpoint.
11. Разобрать свежие traceback и установить error monitoring.
12. Исправить mobile LCP: hero images, responsive WebP/AVIF, preload только LCP, critical CSS.
13. Отдавать корректные цену/stock server-side; убрать initial `0,00`.
14. Реализовать GA4 ecommerce funnel и server-confirmed `purchase`.
15. Сопоставить GA4/Ads/Merchant IDs, conversion actions и attribution.
16. Добавить Product/Offer/Breadcrumb/Organization JSON-LD.
17. Исправить `lang`, hreflang, уникальные title/description и пагинацию.
18. Исправить accessibility: alt, labels, focus, contrast, headings, viewport.
19. Улучшить карточку товара и checkout: доставка, наличие, trust и валидация.
20. Создать наблюдаемость: uptime, 5xx, queue, payment callback, Merchant sync и backup restore drill.

## Рекомендуемая последовательность

### Фаза 0 — немедленно

- сохранить baseline и проверить restore-процедуру;
- закрыть публичный directory index staging;
- 2FA и rotation secrets;
- подготовить security hotfix в закрытом staging.

### Фаза 1 — безопасность транзакций

- IDOR, Paytrail idempotency/state validation, PII logging, POST/CSRF/rate limits;
- regression tests заказов, оплаты, писем и Merchant sync.

### Фаза 2 — платформа

- Git/CI, поддерживаемый Django, централизованные settings/secrets;
- staging с минимизированными данными;
- error monitoring и health checks.

### Фаза 3 — измерение и скорость

- GA4 ecommerce + Ads reconciliation;
- mobile LCP/accessibility;
- server-rendered price/availability.

### Фаза 4 — SEO/CRO/B2B

- structured data, metadata, internal links, content clusters;
- карточка товара, checkout и B2B кабинет по утверждённым KPI.

## Что можно сделать безопасно сейчас

- создать документацию и локальный конфиденциальный audit snapshot;
- закрыть directory listing пустого staging;
- добавить `noindex` и HTTP auth до размещения staging;
- подготовить patch и тесты без выкладки;
- включить 2FA вручную владельцем;
- настроить non-PII error monitoring после выбора провайдера.

## Что требует согласования

- любые production-изменения Paytrail, заказов, клиентов, цен, налогов, остатков и доставки;
- rotation ключей, если интеграции нельзя переключить атомарно;
- обновление Django и миграции БД;
- копирование данных на staging;
- изменение Google Ads conversion actions, Merchant feed или удаление товаров;
- публикация SEO/CRO контента и изменение checkout UX.

## Ограничения аудита

- Production БД не экспортировалась и клиентские записи не читались.
- Полное восстановление backup не выполнялось.
- Paytrail/PostNord sandbox тесты не выполнялись.
- Google Search Console и полные настройки Google-продуктов не экспортировались.
- Найденные секреты не сохранялись в рабочей документации.
