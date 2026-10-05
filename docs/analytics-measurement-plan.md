# Analytics measurement plan

## Baseline

- GA4 и Google Ads используют direct `gtag`.
- Consent Mode v2 default-denied в EEA реализован.
- GTM-контейнер `GTM-MMLHMKRW` пуст; он не должен публиковаться параллельно с
  direct `gtag`, чтобы не создавать дубликаты.
- До кандидата 2026-07-30 стандартная ecommerce-воронка отсутствовала.
- Google Signals включён, но User-ID поступал из `0 of 1` web streams.
- `add_to_cart` ошибочно был key event; `purchase` не поступал.

## Реализация-кандидат 2026-07-30

- Single source: direct `gtag`, GA4 `G-HXEJKEB3MW`; GTM остаётся пустым.
- События: `view_item`, `add_to_cart`, `begin_checkout`,
  `add_shipping_info`, `add_payment_info`, `purchase`,
  `view_search_results`.
- `purchase` строится только после валидного Paytrail success или принятого
  COD и использует snapshot заказа.
- `transaction_id` имеет формат `DP-{order_id}`; refresh в одной session
  подавляется, дополнительная дедупликация выполняется GA4.
- Для авторизованного клиента передаётся только HMAC-based opaque User-ID
  `dp_*`; email, имя, телефон и адрес не используются как идентификатор.
- Custom события отправляются только при `analytics_storage=granted`.
- URL query string исключён из `page_location`; поисковый запрос проходит
  contact-data redaction.
- Google Signals разрешён тегом только под управлением Consent Mode.

## События GA4

| Event | Триггер | Обязательные параметры |
|---|---|---|
| `view_item_list` | видимый список товаров | `item_list_id`, `item_list_name`, `items` |
| `select_item` | переход из списка | list context, `items` |
| `view_item` | карточка товара | currency, value, item_id, item_name, variant |
| `add_to_cart` | успешное изменение cart | currency, value, quantity, items |
| `remove_from_cart` | успешное удаление | currency, value, items |
| `view_cart` | отдельный cart view после его восстановления | currency, value, items |
| `begin_checkout` | checkout start | currency, value, items, coupon |
| `add_shipping_info` | метод доставки принят | shipping_tier, value, items |
| `add_payment_info` | метод оплаты принят | payment_type, value, items |
| `purchase` | сервер подтвердил оплату/принятый COD | transaction_id, value, tax, shipping, coupon, items |
| `refund` | подтверждённый возврат | transaction_id, value, items |

## Правила данных

- Не отправлять email, телефон, имя, адрес, свободный текст или user ID с прямой идентификацией.
- `item_id` должен совпадать с Merchant/Ads и быть устойчивым.
- `value` и `currency` берутся из сохранённого server-side заказа.
- `purchase` допускается один раз на order/transaction; повторный callback не создаёт событие.
- Enhanced conversions включаются только при корректном `ad_user_data` consent и по требованиям Google.
- Client event не является источником статуса оплаты.

## Дедупликация

Текущий code-only выпуск не меняет production DB:

1. Paytrail callback валидируется и идемпотентно подтверждает заказ.
2. Страница подтверждения получает allowlisted payload с `DP-{order_id}`.
3. Повторный render в той же session не формирует событие.
4. Browser `sessionStorage` блокирует повторную отправку.
5. GA4 дедуплицирует повтор на другом client по уникальному `transaction_id`.

Transactional outbox/Measurement Protocol остаётся отдельным будущим проектом:
он требует DB-схемы, API secret, retry policy и отдельного согласования.

## Валидация

- GA4 DebugView на staging с synthetic order.
- Network payload review без PII.
- GA4 Realtime и purchase report.
- Сверка: orders vs paid orders vs GA4 purchases vs Ads conversions.
- Допуск: 0 duplicate transaction ID; объяснимое расхождение из-за consent/ad blockers.
- Consent tests: reject all, analytics only, marketing accepted, revoke.

## KPI

- product view → add to cart;
- add to cart → checkout;
- checkout → paid order;
- revenue/order и margin после предоставления COGS;
- payment failure/cancel rate;
- delivery method share;
- organic landing conversion;
- Ads cost per paid order, ROAS и profit-aware ROAS.
