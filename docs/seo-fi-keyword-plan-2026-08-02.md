# Финский SEO-план для decopaint.fi

Дата: 2 августа 2026 г.
Статус: read-only исследование; сайт, staging и production не изменялись.

## Охват и метод

Анализ основан на:

- 154 действующих карточках товара;
- 352 PDF и двух других товарных документах;
- 293 уникальных PDF по содержимому;
- текущих Title, Meta Description, H1–H4, canonical, `lang`, alt и внутренних
  ссылках главной, каталога, ключевых категорий и репрезентативных товаров;
- текущей финской поисковой выдаче и формулировках конкурирующих страниц;
- подтверждённой карте типов материалов, оснований, назначений и способов
  нанесения из карточек и технических листов.

Приоритеты ниже — качественная оценка коммерческой важности, соответствия
ассортименту и наблюдаемой выдачи. Это не точные значения частотности. Перед
массовым выпуском нужно добавить 12–16 месяцев Google Search Console и выгрузку
Keyword Planner по Finland/Finnish, чтобы отсортировать кластеры по показам,
кликам, объёму и конкуренции.

## Главные выводы текущего аудита

1. Главная имеет Title `Deco Paint Finland`; каталог — `Decopaint oikos`.
2. Главная, категории и товары используют одну общую Meta Description.
3. Финские страницы отдают `<html lang="en">`.
4. `meta keywords` содержит длинный переспамленный список, повторы и опечатки;
   этот тег нужно удалить.
5. Многие категории не имеют уникального индексируемого вступления и FAQ.
6. Существуют конкурирующие URL с почти одинаковым интентом:
   `/catalog/` и `/catalog/tuotteet/`, а также пары
   `/catalog/tag/sisustusmaalit/` ↔ `/catalog/sisustusmaali/`,
   `/catalog/tag/sisustuslaastit/` ↔ `/catalog/sisustuslaasti/` и
   `/catalog/tag/koristemaalit/` ↔ `/catalog/koristemaali/`.
7. Canonical строится из полного request URL. В индексе уже видна карточка с
   `?page=19&size=`, поэтому незначащие параметры могут создавать дубликаты.
8. Google чаще показывает общие каталоги и отдельные товары, а не ожидаемую
   целевую категорию. Например, по `site:decopaint.fi sisustusmaali` видны
   `/catalog/sisakattomaali/`, главная и общий каталог.
9. У части галерей alt повторяется (`lisäkuva`, `Effect Photo`), а hero и
   информационные значки имеют пустой alt независимо от декоративной роли.
10. Карточки могут отдавать crawler-у цену `0,00`; это нужно исправить до
    расширения Product/Offer structured data.

## Карта коммерческих запросов и целевых страниц

| Приоритет | Финские запросы | Интент | Основная страница | Решение |
|---|---|---|---|---|
| P0 | `oikos maali`, `oikos maalit`, `oikos suomi` | бренд/покупка | `/` | Главная: бренд + основные семейства, без попытки ранжироваться по каждому товарному запросу |
| P0 | `sisustusmaali`, `sisäseinämaali`, `seinämaali sisälle`, `oikos sisustusmaali` | категория/покупка | `/catalog/sisustusmaali/` | Сделать единственной основной страницей именно красок для внутренних стен |
| P0 | `kalkkimaali`, `kalkkimaali seinään`, `oikos kalkkimaali` | категория/покупка | `/catalog/kalkkimaali/` | Три подтверждённых продукта; объяснить отличие от kalkkipinnoite и kalustekalkkimaali |
| P0 | `sisustuslaasti`, `sisustuslaasti seinään`, `koristelaasti` | категория/сравнение | `/catalog/sisustuslaasti/` | Вводный выбор по материалу, основанию и способу нанесения |
| P0 | `koristemaali`, `koristemaali seinään`, `koristemaalit` | категория/покупка | `/catalog/koristemaali/` | Multidecor, Multidecor Skin, Encanto и другие подтверждённые продукты |
| P0 | `efektimaali`, `efektimaali seinään`, `efektiseinä maali`, `efektimaalaus seinään` | вдохновение/покупка | `/catalog/efektimaali/` | Отдельный интент от koristemaali; добавить реальные эффекты и способы нанесения |
| P0 | `kalkkipinnoite`, `marmorino`, `marmorino laasti`, `marmorilaasti seinään` | категория/покупка | `/catalog/kalkkipinnoite/` | Marmorino Naturale/Fine и связанные подтверждённые системы |
| P0 | `ulkomaali`, `ulkoseinämaali`, `julkisivumaali`, `julkisivupinnoite` | категория/покупка | новая `/catalog/ulkomaalit/` | Создать нормальную canonical-страницу и после проверки перенаправить `/catalog/tag/ulkomaalit/` |
| P0 | `siloksaanimaali`, `siloksaanimaali ulkoseinälle`, `mineraalimaali julkisivulle` | техническая категория | `/catalog/siloksan-mineraalimaali/` | Развести с общей страницей ulkomaalit; показать только подтверждённые продукты и основания |
| P0 | `pohjamaali`, `pohjamaali seinälle`, `tartuntapohjamaali`, `primer maali` | выбор/покупка | `/catalog/pohjamaali-primer/` | Разделить внутри страницы по основанию и задаче; не обещать универсальную совместимость |
| P0 | `homeenestomaali`, `homeenesto seinään` | проблема/покупка | `/catalog/homeenestomaali/` | Использовать только подтверждённые BioAntimuffa/Sterylcalce данные; отдельно объяснить устранение причины влаги |
| P0 | `kaakelimaali`, `laattamaali`, `kaakelimaali kylpyhuoneeseen` | покупка/инструкция | `/catalog/kaakelimaali/` + Ecosmalto per Ceramica | Обязательно показать PDF-ограничение: не для поверхностей с постоянным контактом с водой |
| P0 | `patterimaali`, `lämpöpatterin maali`, `patterin maalaus` | покупка/инструкция | `/catalog/patterimaali/` + Ecosmalto Thermo | Категория для выбора, товар для точной покупки, статья для инструкции |
| P0 | `parkettilakka`, `puulattian lakka`, `lakka puulattialle` | покупка | Ecoprotettivo Parquet | Одного товара достаточно: усиливать карточку, не создавать тонкую категорию |
| P0 | `eristysmaali`, `maali nikotiinitahroille`, `noki seinässä maalaus`, `savutahrat seinässä` | проблема/покупка | Decortina New + новый guide | PDF подтверждает внутренние стены с дымом/никотином; не расширять на неподтверждённые пятна |
| P1 | `metalliefektimaali`, `metallinhohtoinen seinämaali`, `kultamaali seinään` | эффект/покупка | новая `/catalog/metalliefektimaali/` | Curated landing: Imperium и другие продукты только при наличии product-level PDF evidence |
| P1 | `struktuurimaali`, `tekstuurimaali seinään`, `struktuuripinta seinään` | эффект/покупка | `/catalog/struktuurimaali/` | Основной продукт Kreos; техника и инструменты из PDF |
| P1 | `savilaasti`, `savilaasti seinään`, `savipinnoite` | материал/покупка | `/catalog/savilaasti/` + Argilla Materica | Не переносить свойства других брендов; использовать только Argilla Materica PDF |
| P1 | `betoniefekti seinään`, `betonipinta seinään`, `betonipinnoite sisäseinään` | эффект/покупка | Cemento Materico | Не использовать слово `mikrosementti`; официальный PDF подтверждает decorative concrete effects для интерьера |
| P1 | `stuccolaasti`, `stucco seinään`, `venetsialainen stucco`, `venetsialainen rappaus` | материал/обучение | `/catalog/kalkki-stucco/` + новый guide | Raffaello Decorstucco, Stucco Romano и Aureum после проверки терминов в каждом PDF |
| P1 | `sisäkattomaali`, `kattomaali sisälle`, `himmeä kattomaali` | категория/покупка | `/catalog/sisakattomaali/` | Удалить товары, которые не подтверждены для kattopinta, или объяснить их роль |
| P1 | `kalustemaali`, `maali kalusteille`, `kalustemaali puulle` | категория/покупка | `/catalog/kalustemaali/` | Фильтровать по подтверждённому основанию; не считать все emalimaalit подходящими для любого kaluste |
| P1 | `ruosteenmuuntoaine`, `ruosteenestoaine metallille` | покупка | существующие точные категории и товары | Развести conversion и prevention intents на разные страницы |
| P1 | `betonin suoja-aine`, `betonin kyllästysaine`, `betonin vedenhylkivä käsittely` | техническая покупка | `/catalog/impregnointiaineet-kyllastysaineet/` | Внутри — Betoncryll Idrorepellente и другие только по подтверждённым основаниям |

## Карта важных товарных страниц

| Товар | Основной запрос | Дополнительные запросы | Техническая граница |
|---|---|---|---|
| Marmorino Naturale | `marmorino` | `marmorino kalkkilaasti`, `marmoripinta seinään` | PDF: lime-putty coating, sisä- ja ulkoseinät, конкретные primer/protection |
| Marmorino Naturale Fine | `marmorino fine` | `hienorakeinen marmorino` | Не смешивать расход Fine и обычной версии |
| Travertino Romano | `travertino romano` | `travertiinipinta seinään`, `kiviefekti seinään` | Применение, слои, primer и protection — только по его PDF |
| Cemento Materico | `betoniefekti seinään` | `betonipinnoite sisäseinään` | Не продвигать как mikrosementti; PDF подтверждает interior decorative concrete effects |
| Argilla Materica | `savilaasti seinään` | `argilla materica` | PDF: interior decoration; указать чувствительность к воде и system components |
| Multidecor | `multidecor koristemaali` | `koristemaali seinään` | Общий head-запрос остаётся категории |
| Imperium | `metalliefektimaali` | `imperium seinämaali`, `kultainen seinäefekti` | Interior/exterior walls and furnishings подтверждены; не обещать пригодность для любой металлической поверхности |
| Kreos | `struktuurimaali` | `kreos seinä`, `tekstuurimaali` | PDF подтверждает interior walls/furnishings и конкретные инструменты |
| Silkos Torino | `siloksaanimaali` | `julkisivumaali rappaukselle` | Уточнить основание и систему грунтования; не называть puujulkisivumaaliksi |
| Ecosmalto per Ceramica | `kaakelimaali` | `laattamaali lattiaan`, `kaakelimaali seinään` | Явно показать запрет постоянного контакта с водой |
| Ecosmalto Thermo | `patterimaali` | `maali lämpöpatterille` | Металл/радиатор подтверждены PDF |
| Ecoprotettivo Parquet | `parkettilakka` | `puulattian lakka` | PDF: деревянные полы, влажность древесины и Turapori base coat |
| Decortina New | `eristysmaali nikotiinitahroille` | `maali savu- ja nokitahroille` | Не расширять на плесень, воду или неизвестные пятна |
| 306 BioAntimuffa | `homeenestomaali` | `bioantimuffa` | Не обещать ремонт причины влажности или лечение существующего повреждения |
| Ultrasaten | `antibakteerinen seinämaali` | `pestävä seinämaali` | Только точные сертификаты/проценты из действующего PDF/сертификата |
| 250 BioFissativo Alta Adesione / Aggrappante Ecologico | `tartuntapohjamaali` | `pohjamaali PVC:lle`, `pohjamaali laminaatille` | На посадочной странице показывать матрицу `alusta → hyväksytty primer`, а не объединять свойства продуктов |

## Предлагаемые Title, Meta Description и H1

| URL | Title | Meta Description | H1 |
|---|---|---|---|
| `/` | `OIKOS-maalit ja sisustuspinnoitteet \| Deco Paint` | `Osta OIKOS-sisustusmaalit, kalkkimaalit, sisustuslaastit ja julkisivupinnoitteet. Tuotekohtaiset ohjeet, tekniset PDF:t ja asiantuntija-apu.` | `OIKOS-maalit ja sisustuspinnoitteet kotiin ja ammattilaisille` |
| `/catalog/` | `OIKOS-maalit, pinnoitteet ja työkalut \| Deco Paint` | `Selaa Deco Paintin OIKOS-tuotteita. Rajaa tuotteet käyttökohteen, alustan ja tuotetyypin mukaan ja tarkista tekniset tiedot ennen valintaa.` | `OIKOS-maalit, pinnoitteet ja tarvikkeet` |
| `/catalog/sisustusmaali/` | `Sisustusmaalit ja sisäseinämaalit \| OIKOS` | `Tutustu OIKOS-sisustusmaaleihin. Vertaa käyttökohdetta, kiiltoa, riittoisuutta ja teknisiä tietoja ja valitse kohteeseen sopiva sisäseinämaali.` | `Sisustusmaalit sisäseinille` |
| `/catalog/kalkkimaali/` | `Kalkkimaalit seinille \| OIKOS` | `Vertaa OIKOS-kalkkimaaleja Pittura Alla Calce Verona, Sterylcalce ja Tiepolo Opaco. Tarkista alusta, pohjustus, riittoisuus ja levitysohje.` | `Kalkkimaalit seinäpinnoille` |
| `/catalog/sisustuslaasti/` | `Sisustuslaastit ja koristepinnoitteet \| OIKOS` | `Tutustu OIKOS-sisustuslaasteihin ja -pinnoitteisiin. Vertaa materiaalia, alustaa, työvälineitä, pohjustusta ja teknisiä käyttöohjeita.` | `Sisustuslaastit ja pinnoitteet seinille` |
| `/catalog/koristemaali/` | `Koristemaalit seinille \| OIKOS` | `Löydä OIKOS-koristemaali elävään seinäpintaan. Vertaa Multidecor-, Encanto- ja muita vaihtoehtoja sekä niiden pohjusteita ja levitystapoja.` | `Koristemaalit yksilöllisiin seinäpintoihin` |
| `/catalog/efektimaali/` | `Efektimaalit ja efektiseinät \| OIKOS` | `Tutustu OIKOS-efektimaaleihin, työvälineisiin ja vahvistettuihin levitystapoihin. Valitse haluttuun pintaan teknisesti sopiva tuote.` | `Efektimaalit näyttäviin seinäpintoihin` |
| `/catalog/kalkkipinnoite/` | `Kalkkipinnoitteet ja Marmorino \| OIKOS` | `Tutustu Marmorino Naturale- ja muihin OIKOS-kalkkipinnoitteisiin. Tarkista alusta, pohjuste, suojaus, riittoisuus ja tekninen PDF.` | `Kalkkipinnoitteet ja Marmorino-pinnat` |
| новая `/catalog/ulkomaalit/` | `Julkisivumaalit ja ulkopinnoitteet \| OIKOS` | `OIKOS-julkisivumaalit ja ulkopinnoitteet rappaus-, betoni- ja sementtipinnoille. Valitse järjestelmä alustan ja teknisten tietojen mukaan.` | `Julkisivumaalit ja ulkopinnoitteet` |
| `/catalog/siloksan-mineraalimaali/` | `Siloksaanimaalit julkisivuille \| OIKOS` | `Vertaa OIKOS-siloksaani- ja siloksan-mineraalimaaleja ulkoseinille. Tarkista hyväksytty alusta, pohjuste, riittoisuus ja levitysolosuhteet.` | `Siloksaanimaalit ulkoseinille` |
| `/catalog/pohjamaali-primer/` | `Pohjamaalit ja tartuntapohjamaalit \| OIKOS` | `Valitse OIKOS-pohjamaali alustan ja pintatuotteen mukaan. Vertaa tartuntaa, imevyyden tasausta, levitystä ja hyväksyttyä jatkokäsittelyä.` | `Pohjamaalit eri alustoille` |
| Marmorino Naturale | `Marmorino Naturale kalkkipinnoite \| OIKOS` | `OIKOS Marmorino Naturale on kalkkipohjainen sisä- ja ulkoseinien pinnoite. Katso riittoisuus, Consolidante Calce -pohjustus ja suojaus PDF:stä.` | `Kalkkipinnoite Marmorino Naturale` |
| Cemento Materico | `Cemento Materico betoniefekti seinään \| OIKOS` | `OIKOS Cemento Materico sisäseinien koristeellisiin betoniefekteihin. Katso Il Primer, työvälineet, suojaus, riittoisuus ja tekninen PDF.` | `Cemento Materico -pinnoite betoniefektiin` |
| Ecosmalto per Ceramica | `Kaakelimaali seinille ja lattioille \| OIKOS` | `Ecosmalto per Ceramica sisätilojen kaakeli-, betoni-, kivi- ja terrakottapinnoille. Ei jatkuvaan vesikosketukseen. Katso järjestelmä ja ohje.` | `Kaakelimaali Ecosmalto per Ceramica` |
| Ecoprotettivo Parquet | `Parkettilakka puulattialle \| OIKOS` | `Ecoprotettivo Parquet on puulattioiden suojalakka. Tarkista Turapori-pohjustus, puun kosteus, riittoisuus, kuivuminen ja levitysohje PDF:stä.` | `Parkettilakka Ecoprotettivo Parquet` |
| Decortina New | `Eristysmaali nikotiini- ja savutahroille \| OIKOS` | `Decortina New sisäseinien savu-, noki- ja nikotiinitahroille. Katso pinnan valmistelu, Crilux/Neofix-pohjustus, riittoisuus ja kuivuminen.` | `Eristysmaali Decortina New` |

Title и Meta являются черновиками. Перед staging они проходят автоматическую
проверку длины, уникальности и отсутствия неподтверждённых утверждений.

## Недостающие посадочные страницы

| Приоритет | Новый URL | Главный запрос | Назначение |
|---|---|---|---|
| P0 | `/catalog/ulkomaalit/` | `ulkomaali`, `julkisivumaali` | Единая коммерческая страница вместо tag URL и нескольких конкурирующих фильтров |
| P1 | `/catalog/metalliefektimaali/` | `metalliefektimaali` | Curated products с подтверждёнными PDF; Imperium — главный товар |
| P1 | `/oppaat/maalin-menekki-laskuri/` | `maalin menekki laskuri`, `paljonko maalia tarvitaan` | Индексируемый калькулятор с переходом к варианту товара; расход всегда product-specific |
| P1 | `/oppaat/sisaseinan-maalaus/` | `sisäseinän maalaus`, `miten maalata seinä` | Подготовка, основание, primer, нанесение и ссылки на категории |
| P1 | `/oppaat/pohjamaalin-valinta/` | `mikä pohjamaali`, `pohjamaali eri pinnoille` | Проверяемая матрица основание → допустимые грунты → совместимые покрытия |
| P1 | `/oppaat/kalkkimaali-vai-kalkkipinnoite/` | `kalkkimaali vai kalkkipinnoite` | Развести два разных интента и направить на правильные категории |
| P1 | `/oppaat/marmorino-ja-stucco/` | `marmorino`, `venetsialainen stucco` | Объяснение техник с Marmorino/Stucco продуктами и официальными инструкциями |
| P1 | `/oppaat/efektiseina/` | `efektiseinä`, `efektimaalaus seinään` | Галерея реальных систем; каждая фотография связана с точным продуктом/техникой |
| P1 | `/oppaat/julkisivumaalin-valinta/` | `julkisivumaalin valinta` | Выбор по rappaus/betoni/sementti и текущему покрытию, без утверждений для puu без доказательства |
| P1 | `/oppaat/kaakelimaalaus/` | `kaakelien maalaus`, `laattojen maalaus` | Полная система Ecosmalto per Ceramica и явные ограничения воды |
| P1 | `/oppaat/nikotiini-ja-savutahrat/` | `nikotiinitahrat seinässä`, `noki seinässä` | Подготовка и Decortina New без расширения на неизвестные загрязнения |
| P2/blocked | `/oppaat/kylpyhuoneen-seinan-pinnoite/` | `maali kylpyhuoneen seinään` | Только decision/handoff page до экспертной проверки влажных зон и систем; не делать автоматическую товарную рекомендацию |

Страницу `mikrosementti` пока не создавать. У трёх Biomalta Extreme товаров
нет пригодного технического PDF в текущем индексе, и нельзя утверждать, что
`hartsipinnoite` равнозначен `mikrosementti`.

## Как внедрять ключевые слова без переспама

### H1–H3 и тексты

- Один видимый H1 на страницу, содержащий основной запрос естественно.
- Первый абзац: основной запрос один раз, назначение страницы и граница выбора.
- H2: `Valitse tuote alustan mukaan`, `Pohjustus ja yhteensopivat tuotteet`,
  `Riittoisuus ja levitys`, `Usein kysyttyä`.
- H3: конкретные основания или видимые FAQ-вопросы.
- Товарные карточки в сетке — H3, а hero-подзаголовок — обычный paragraph, не H4.
- Не устанавливать требуемую «плотность ключей». Использовать основной термин,
  естественные синонимы и точные названия продуктов.

### Описания категорий

Каждая основная категория получает 350–700 уникальных финских слов:

1. что входит в категорию;
2. как выбирать по основанию и помещению;
3. различия между материалами;
4. подтверждённые primer/protection systems;
5. таблица товаров с назначением и ссылками на PDF;
6. 4–6 FAQ;
7. CTA к товару или специалисту.

Товар получает короткое уникальное введение, подтверждённое применение,
основания, подготовку, нанесение, расход, совместимые продукты, ограничения и
источники. Маркетинговое описание не должно противоречить PDF.

### URL и canonical

- Не менять существующие product slugs: они связаны с индексом, Merchant Center
  и рекламой.
- Новые страницы получают короткий финский slug без дат и бренда.
- Выбрать `/catalog/` основным общим каталогом; `/catalog/tuotteet/` — 301 или
  canonical только после проверки ссылок и sitemap.
- Три пары tag/category объединить через 301 либо сделать tag filters
  `noindex,follow`; основной URL — singular category.
- Canonical товара всегда `/product/<slug>/`, без `page`, `size` и прочих
  незначащих параметров.
- Pagination получает self-canonical; фильтры и поиск — согласованную
  noindex/canonical политику.

### Alt-тексты

- Packshot: `OIKOS Marmorino Naturale kalkkipinnoite, 5 kg` только если размер
  действительно виден/соответствует изображению.
- Effect photo: `Marmorino Naturale -pinnoitteella tehty vaalea seinäpinta`
  только если именно это показано.
- Галерейные фотографии получают разные описания видимого эффекта, оттенка и
  помещения; `lisäkuva` и `Effect Photo` заменить.
- Декоративные иконки рядом с тем же видимым текстом сохраняют `alt=""`.
- Нельзя добавлять один и тот же keyword во все изображения.

### Внутренние ссылки

- Главная → 6 основных семейств с описательными anchors.
- Категория → подкатегория → товар → официальный PDF/guide.
- Product page → только подтверждённые primer, base coat, protection и tools.
- Guide → category/product; category → соответствующий guide.
- Анкоры чередовать естественно: `kalkkipinnoitteet`, `Marmorino-tuotteet`,
  `katso tekniset tiedot`, а не повторять один exact-match по всему сайту.
- Добавить breadcrumbs и BreadcrumbList; category ItemList и корректный Product
  + Offer после server-rendered price/availability.

### FAQ и статьи

FAQ создаётся только из вопросов, на которые есть точный ответ в карточке или
PDF. В каждом ответе показывается ссылка на источник. FAQPage markup должен
полностью совпадать с видимым текстом.

Первая очередь статей:

1. `Miten valita sisustusmaali eri huoneisiin?`
2. `Kalkkimaali vai kalkkipinnoite: mitä eroa niillä on?`
3. `Marmorino-seinä: alusta, pohjustus ja suojaus`
4. `Efektiseinä maalilla tai sisustuspinnoitteella`
5. `Pohjamaalin valinta rappaukselle, kipsille, puulle, metallille ja PVC:lle`
6. `Julkisivumaali rappaus- ja betonipinnalle`
7. `Kaakelien maalaus Ecosmalto per Ceramica -järjestelmällä`
8. `Nikotiini- ja savutahrojen eristäminen ennen maalausta`
9. `Patterin maalaus: valmistelu ja oikea maali`
10. `Maalin menekin laskeminen tuotekohtaisen riittoisuuden avulla`

## Запрещённые или отложенные утверждения

- Не писать, что все OIKOS-товары `myrkyttömiä`, `muovittomia`,
  `antibakteerisia`, `HACCP-sertifioituja` или подходят для märkätila.
- Не применять сертификат одного товара ко всей категории.
- Не называть Biomalta `mikrosementti`, пока это не подтверждено официальным
  документом.
- Не рекомендовать систему во влажной зоне только по слову `kosteudenkestävä`.
- Не объединять Marmorino Naturale и Fine расход, слои или время высыхания.
- Не использовать отзывы клиентов как источник технического свойства.

## План изменений после одобрения

### Этап 1 — данные и технические шаблоны

1. Зафиксировать Search Console/Keyword Planner baseline.
2. Создать уникальные SEO-поля в models/admin без изменения цен и товаров.
3. Исправить `lang="fi"`, canonical parameters, heading order и meta keywords.
4. Добавить тесты уникальности Title/H1/canonical и отсутствие PII.

### Этап 2 — существующие страницы

1. Подготовить тексты P0 категорий из подтверждённых источников.
2. Добавить уникальные Title/Meta/H1–H3, image-specific alt и внутренние ссылки.
3. Устранить дубли tag/category и `/catalog/tuotteet/` на staging.
4. Исправить server-rendered price/availability и Product/Offer schema.

### Этап 3 — новые landing/guides

1. Создать P0/P1 страницы по одной небольшой партии.
2. Привязать каждое техническое утверждение к source ID/PDF.
3. Добавить FAQ, BreadcrumbList и ItemList/Product schema по необходимости.
4. Проверить Search Console URL Inspection/Rich Results после production
   только при отдельном одобрении.

### Staging gates

- закрытый HTTP-auth/noindex staging;
- backup и отдельная ветка/release;
- Django tests, template compile, `check --deploy`;
- crawl staging: unique Title/H1/canonical, no broken links и orphan pages;
- visual mobile/desktop QA;
- Merchant landing URL/price/availability regression;
- Lighthouse не хуже baseline;
- production не затрагивается до отдельного подтверждения.
