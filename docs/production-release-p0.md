# P0 production release review

Статус на 30 июля 2026: релиз подтверждён владельцем и успешно установлен
в production. Выпуск завершён в `20260730T154003Z`, rollback не потребовался.

## Кандидат

- Production archive: `work/decopaint-p0-production-candidate-clean.tar.gz`
- SHA-256: `b473544cad8f4487cabe0801ebbfe0ed89dac334fb89277a0934f5980fbdcc80`
- Основа: закрытый staging release `/home/decpai/staging/releases/1425dc7`
- Staging regression suite: 17 tests, `OK`
- Изменения схемы БД и migrations: отсутствуют
- Изменения цен, VAT, stock, delivery, товаров Merchant Center и customer/order data: отсутствуют

В archive входят только runtime-файлы:

- `users/views.py`
- `pk_paytrail/views.py`
- `order/templates/order/created.html`
- `order/templates/order/pending.html`
- `google_shopping/views.py`
- `google_shopping/signals.py`
- `google_shopping/templates/admin/google_shopping_upload.html`

## Production baseline

Production root: `/home/decpai/public_html/deco`

| Файл | SHA-256 до релиза |
| --- | --- |
| `users/views.py` | `51b17fc8ef5b86c40afa61235aef142494ae596e2439235c3c74003c1ff5bf68` |
| `pk_paytrail/views.py` | `c3bdc05e8dd3df7109dc0c93c1c18000f67f90c36b11916ee5907849fc7c0dd8` |
| `order/templates/order/created.html` | `a1c5d3ddfef77a26ec293cbd5d27780bdc89bd7717541573bb3b2347d5030ec6` |
| `google_shopping/views.py` | `bae7a5c4de18c02a41957330bb71757c177ef79d76b2cbb7206fbac42460c57e` |
| `google_shopping/signals.py` | `c3ddc5aafe3691427ddb14138513f391386b4dacd245f93f26df86c2a91b7bf7` |
| `google_shopping/templates/admin/google_shopping_upload.html` | `8f6ba5075dcd9b000e16ddba8e029ff767f8275feee851a83504b6668c6738a2` |

`order/templates/order/pending.html` является новым файлом и до релиза отсутствует.

## Read-only preflight

- Production отвечает `200 OK` по HTTPS.
- HTTP перенаправляется на HTTPS с `301`.
- `DEBUG=False`.
- Production root и `tmp` принадлежат `decpai:decpai`, режим `0755`.
- Passenger restart-файл существует: `/home/decpai/public_html/deco/tmp/restart.txt`.
- Production source занимает 63 MB.
- Свободно 222 GB, достаточно для code-only backup и распаковки.
- Каталога `/home/decpai/backups` сейчас нет; перед изменением будет создан закрытый `/home/decpai/release-backups/<timestamp>` вне `public_html` с режимом `0700`.
- `manage.py check --deploy` показывает пять известных предупреждений: HSTS, application-level SSL redirect, session cookie setting, CSRF cookie setting и legacy non-unique email login. Внешний HTTP redirect уже работает, а фактические session/CSRF cookies в HTTPS-ответе имеют флаг `Secure`. Эти настройки не добавляются в P0 без отдельного staging-теста.

## Выполненный выпуск

1. Baseline production-файлов повторно совпал с preflight SHA-256.
2. Создан закрытый code-only backup:
   `/home/decpai/release-backups/p0-20260730T152547Z/production-files-before.tar.gz`.
3. Backup SHA-256:
   `347baae5a49074aac73167eb347ff58ca85b676266db142a5908102849d574dd`.
4. Backup проверен через полный archive listing; режим файла `0600`, каталогов `0700`.
5. Первый локальный production archive был отклонён до распаковки из-за
   служебных macOS `._*` entries. Он не менял production.
6. Пересобран и повторно загружен clean archive; серверный SHA-256 совпал с
   локальным, listing содержит ровно семь runtime-файлов.
7. Python syntax и `manage.py check --deploy` выполнены перед restart; новых
   предупреждений не появилось.
8. Семь файлов установлены, права приведены к `0644`, их production SHA-256
   совпали с candidate.
9. Passenger перезапущен через `tmp/restart.txt`.
10. Production не содержит файлов `._*`.

## Installed SHA-256

| Файл | SHA-256 после релиза |
| --- | --- |
| `users/views.py` | `70f9c405310573405143608514ec9755464dd5e14334140fde6d005904a09614` |
| `pk_paytrail/views.py` | `ab3c67f69b1ca83806bf1b0218c8761fc7c7ec6b4379aae70ece1e3bf891f8fd` |
| `order/templates/order/created.html` | `f34393fa1d57febd854570268859b6151c668b7c2442d47ee1f6a77f05b9621` |
| `order/templates/order/pending.html` | `724e125899db38a66f66748e60f36f95ea070a41226bda6241ff8be506352173` |
| `google_shopping/views.py` | `7862b10b1833c6ee003b38d1ec95ab2e67db510d37874c3f8c9cc587a243c215` |
| `google_shopping/signals.py` | `baf93bc01ebac2622e710aee7542ad8f318265066010c6fb528d439d764a0dd2` |
| `google_shopping/templates/admin/google_shopping_upload.html` | `5d33c1ff476aa4a7c8d8ab7028b9d1ff65b896218dde6ae93745a6bb66f37ae0` |

## Post-release verification

- Homepage: `200`.
- Catalog: `200`.
- Login: `200`.
- Empty checkout: `200`.
- Public product `210-biofondo-coprente`: `200`; dynamic price loader завершился.
- Anonymous payment details request: `302` to login.
- `create_payment` через GET: `405`.
- Paytrail success callback без подписи: `403`.
- Paytrail cancel callback без подписи: `403`.
- Визуальный DOM smoke главной и карточки товара успешен.
- После Passenger restart зафиксирован кратковременный MySQL socket error у
  завершаемого worker. После стабилизации четыре повторных запроса не увеличили
  `stderr.log`: размер остался `7480122` bytes.
- В последних 200 строках проверенного журнала не найдено email, phone,
  address, signature, authorization или token markers.
- Критических отклонений после стабилизации нет; rollback не выполнялся.

## Rollback

1. Восстановить семь путей из timestamped backup.
2. Если `order/templates/order/pending.html` до релиза отсутствовал, удалить только этот новый файл.
3. Перезапустить Passenger.
4. Проверить homepage, product, cart и checkout.
5. Сверить новые платежные callback и заказы за окно релиза без изменения данных.

DB restore не требуется и не должен выполняться: релиз не содержит migrations и не меняет схему БД.
