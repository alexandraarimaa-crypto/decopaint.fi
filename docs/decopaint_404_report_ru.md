# Аудит внутренних HTTP 404 на decopaint.fi

Дата проверки: 8 августа 2026 г.

## Итог

- Проверены все 247 URL из `sitemap.xml`.
- После повторной проверки тайм-аутов все 247 sitemap-страниц отвечают HTTP 200.
- На страницах собрано 11 861 размещение внутренних ссылок и 1 165 уникальных внутренних URL-целей.
- Подтверждены 5 уникальных URL с настоящим HTTP 404 и страницей `404 - Sivua ei löydy`.
- Эти URL используются в 7 карточках раздела `Liittyvät tuotteet` («Связанные товары»).
- В HTML имеется 14 битых элементов `<a>`: в каждой карточке на один URL ссылаются изображение и название товара.
- Ни один из пяти битых URL не находится в актуальном `sitemap.xml`.

## Найденные ошибки и безопасные исправления

### 1. Maalaussivellin Pettinato

- Страница-источник: <https://decopaint.fi/product/ottocento/>
- Битая цель: <https://decopaint.fi/product/maalaussivellin-pettinato/>
- Анкор: `Maalaussivellin Pettinato`
- Статус: HTTP 404, `Sivua ei löydy`
- Место: карточка в `Liittyvät tuotteet`.

Исправление:

1. Если инструмент ещё продаётся — опубликовать существующую карточку товара с тем же slug. В разметке сохранились название, цена и thumbnail, поэтому запись товара, вероятно, не удалена полностью, а снята с публикации.
2. Если товар снят — удалить его из связанных товаров Ottocento. Не заменять автоматически на `Pennello Spanga`: этот товар уже присутствует в том же блоке.
3. Возможный преемник для подтверждения менеджером каталога: <https://decopaint.fi/product/kuviokampa-pettine-in-gomma/>. До подтверждения безопасный 301 — на <https://decopaint.fi/catalog/tyokalut/>.

### 2. Pittura Alla Calce

- Страница-источник: <https://decopaint.fi/product/superfinish24/>
- Битая цель: <https://decopaint.fi/product/pittura-alla-calce/>
- Анкор: `PITTURA ALLA CALCE`
- Статус: HTTP 404, `Sivua ei löydy`
- Место: карточка в `Liittyvät tuotteet`.

Исправление:

- Заменить связанную карточку на актуальную страницу <https://decopaint.fi/product/pittura-alla-calce-verona/>.
- Добавить постоянный редирект: `/product/pittura-alla-calce/` → `/product/pittura-alla-calce-verona/`.
- Это наиболее уверенная замена: актуальная товарная страница присутствует в sitemap, а Superfinish24 предназначен для впитывающих известковых покрытий.

### 3. Raffaello Madreperlato

- Страница-источник: <https://decopaint.fi/product/o-addensante/>
- Битая цель: <https://decopaint.fi/product/raffaello-madreperlato/>
- Анкор: `RAFFAELLO MADREPERLATO`
- Статус: HTTP 404, `Sivua ei löydy`
- Место: карточка в `Liittyvät tuotteet`.

Исправление:

1. Если продукт доступен — снова опубликовать его по прежнему URL.
2. Если продукт снят — удалить карточку из связанных товаров O-Addensante. На странице уже есть актуальный `Raffaello Decorstucco`, поэтому добавлять его второй раз не нужно.
3. Для старого URL можно поставить 301 на <https://decopaint.fi/product/raffaello-decorstucco/> после подтверждения товарной команды.
4. Не направлять ссылку автоматически на `Finitura Madreperlata`: это финишный воск, а не тот же продукт.

### 4. Rullo In Pelle 104 E / Koristetela

- Страница-источник: <https://decopaint.fi/product/kreos/>
- Битая цель: <https://decopaint.fi/product/rullo-in-pelle-104-e/>
- Анкор: `Koristetela`
- Статус: HTTP 404, `Sivua ei löydy`
- Место: карточка в `Liittyvät tuotteet`.

Исправление:

- Если товар снят, заменить связанную карточку на уже используемый в тексте страницы валик <https://decopaint.fi/product/rullo-special-110/> либо удалить карточку.
- Для старого URL поставить 301 на выбранный и подтверждённый валик; до подтверждения — на <https://decopaint.fi/catalog/tyokalut/>.

### 5. Sottosmalto Ecologico

- Страницы-источники:
  - <https://decopaint.fi/product/313-biosmalto-opaco/>
  - <https://decopaint.fi/product/ecosmalto-universale/>
  - <https://decopaint.fi/product/ecosmalto-metallizzato/>
- Битая цель: <https://decopaint.fi/product/sottosmalto-ecologico/>
- Анкор: `Sottosmalto Ecologico`
- Статус: HTTP 404, `Sivua ei löydy`
- Место: карточки в `Liittyvät tuotteet` на всех трёх страницах.

Исправление:

1. Если грунт остаётся в ассортименте — опубликовать прежнюю карточку по тому же URL.
2. Если товар снят — удалить его из связанных товаров на всех трёх страницах.
3. Не подменять его автоматически на `Aggrappante Ecologico`: на страницах они перечислены как разные варианты грунта.
4. Для снятого товара безопасный 301: `/product/sottosmalto-ecologico/` → `/catalog/pohjamaali-primer/`.

## Причина

Все ошибки находятся в автоматически сформированных карточках `Liittyvät tuotteet`. Карточки продолжают показывать название, цену и thumbnail снятого или неопубликованного товара, но ссылка ведёт на несуществующую публичную страницу. Наиболее вероятная причина — устаревшие связи с товарами, снятыми с публикации.

## Выполнено в production

Правки внесены 8 августа 2026 г. через CMS decopaint.fi:

1. На `Ottocento` удалена устаревшая связь с недоступным `Maalaussivellin Pettinato`.
2. На `Superfinish24` недоступный `PITTURA ALLA CALCE` заменён на активный `Pittura Alla Calce Verona`.
3. На `O-Addensante` удалена устаревшая связь с недоступным `RAFFAELLO MADREPERLATO`.
4. На `Kreos` недоступный `Koristetela` заменён на активный `Maalaustela Special`.
5. `Sottosmalto Ecologico` удалён из связанных товаров на страницах `313 BioSmalto Opaco`, `Ecosmalto Universale` и `Ecosmalto Metallizzato`.

Наличие, цены, описания, категории и URL самих товаров не изменялись.

## Проверка после исправления

- Проверены все семь публичных страниц-источников.
- На каждой странице число ссылок на соответствующий старый 404 URL равно нулю.
- На `Superfinish24` новая карточка `Pittura Alla Calce Verona` содержит две корректные ссылки: изображение и название.
- На `Kreos` новая карточка `Maalaustela Special` содержит две корректные ссылки: изображение и название.
- Все семь страниц-источников открываются как обычные товарные страницы.

Сами URL снятых товаров по-прежнему могут отвечать 404, что соответствует их состоянию `Available = false`; внутренних ссылок на них больше нет. Для сохранения внешнего SEO-веса рекомендуется отдельно реализовать серверные 301-редиректы, если на старые адреса существуют внешние ссылки.
