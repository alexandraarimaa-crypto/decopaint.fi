# SEO audit

## Finnish keyword/landing-page plan 2026-08-02

Полная read-only карта запросов, целевых страниц, метаданных, новых landing
pages и source-grounding ограничений:

- `docs/seo-fi-keyword-plan-2026-08-02.md`;
- `outputs/seo-fi-keyword-map-20260802.csv`.

Первая утверждённая P0-партия сначала была проверена на закрытом staging:

- release `/home/decpai/staging/releases/seo-fi-p0-20260802-r7`;
- evidence `docs/seo-fi-p0-staging-2026-08-02.md`;
- 27 SEO/search/analytics и 23 commerce/Shopping теста: `OK`;
- staging остаётся 403/noindex; этот этап не менял production.

После отдельного подтверждения был выполнен production code-only preflight,
backup и малый SEO release с production smoke и возможностью мгновенного
отката; фактический статус зафиксирован ниже.

## Production status 2026-08-02

Утверждённая P0-партия опубликована в production как code-only release:

- `/catalog/ulkomaalit/` теперь отвечает `200`, находится в sitemap и не
  требует новой записи БД;
- четыре дублирующих tag URL перенаправляются `301` на canonical-категории;
- главная, каталог, приоритетные категории и пять P0-товаров используют
  финские уникальные title/description/H1 и очищенные canonical;
- внутренний поиск имеет `noindex,follow`;
- checkout, Paytrail, Merchant sync и GA4 smoke прошли без внешних записей.

Open Graph и Product JSON-LD закрыты отдельным R8 release. Product-разметка
валидна на 154/154 активных карточках. Offer публикуется только для 115 страниц,
где сервер однозначно воспроизводит выбранный вариант и ту же цену/доступность,
что AJAX; 39 неоднозначных карточек остаются без Offer, а не получают ложную
цену. Это сохраняет компактный HTML даже у товаров с десятками тысяч вариантов.

Evidence: `docs/seo-fi-p0-production-2026-08-02.md` and
`docs/seo-product-og-r8-production-2026-08-02.md`.

Дата baseline: 30 июля 2026

## Техническое состояние

| Проверка | Статус | Действие |
|---|---|---|
| HTTPS | работает | добавить HSTS после проверки всех subdomain |
| robots.txt | работает | сохранить запрет admin/user; проверить staging |
| sitemap.xml | 246 URL | разделить по типам при росте, добавить lastmod |
| canonical | есть на проверенных URL | автоматические тесты для filters/pagination |
| language | ошибочно `en` на Finnish content | установить `fi`, затем добавить реальные локали |
| hreflang | отсутствует | добавлять только для эквивалентных переводов |
| Product JSON-LD | Product на всех карточках; точный Offer на 115/154 | добавить GTIN/MPN только после подтверждения и нормализации исходных кодов |
| Breadcrumb JSON-LD | отсутствует | добавить на category/product/content |
| Open Graph | включён на product pages | расширять на category/content отдельными проверенными шаблонами |
| metadata | generic/duplicate | шаблоны по page type |

## Индексация и архитектура URL

- Sitemap содержит 246 URL; явных admin/cart/checkout/search URL не найдено.
- Каталог page 2 имеет self-canonical, но generic title/description и не имеет H1.
- Нужна карта всех query parameters и правила `index/follow`, canonical и internal linking.
- Staging всегда должен возвращать `X-Robots-Tag: noindex, nofollow` и быть закрыт HTTP auth.

## Карточка товара

Критичный технический дефект: initial HTML отдаёт `0,00` и пустую доступность, а JavaScript заменяет их после загрузки. Это может расходиться с Merchant Center и ухудшать crawl/structured data.

Целевое состояние:

- цена и наличие рендерятся сервером;
- Offer JSON-LD совпадает с видимым HTML и feed;
- варианты имеют устойчивые SKU/GTIN/MPN/brand;
- delivery/return policy видны рядом с CTA;
- уникальные title, meta description и product copy;
- изображения имеют descriptive alt, width/height, responsive sources.

## Core Web Vitals baseline

### Mobile

- Performance 66
- Accessibility 73
- SEO 92
- FCP 3,6 s
- LCP 11,9 s
- TBT 80 ms
- CLS 0

### Desktop

- Performance 88
- Accessibility 78
- SEO 92
- FCP 0,8 s
- LCP 2,1 s
- TBT 60 ms
- CLS 0,002

## Performance backlog

1. Найти точный LCP element на главной.
2. Создать responsive AVIF/WebP hero, корректный intrinsic size.
3. Убрать lazy-loading только с LCP image; preload один ресурс.
4. Удалить/отложить render-blocking CSS и неиспользуемый JS.
5. Ввести cache busting и long-lived cache для versioned static.
6. Добавить image dimensions, снизить общий image payload.
7. Проверить third-party tags после consent.
8. Повторить Lighthouse 3 раза на staging и production.

## Accessibility

- alt отсутствует у части изображений;
- unnamed links/buttons;
- недостаточный contrast;
- small targets;
- нарушен heading order;
- viewport запрещает zoom через `user-scalable=no`.

Цель: WCAG 2.2 AA для основных shopping flows.

## Критерии приёмки

- mobile LCP ≤ 2,5 s на p75 field data после накопления;
- lab LCP ≤ 3,0 s на типовом mobile throttling;
- все индексируемые шаблоны имеют unique title/H1/canonical;
- Product structured data проходит Rich Results Test;
- Merchant price/availability совпадают с landing page;
- staging отсутствует в индексе.
