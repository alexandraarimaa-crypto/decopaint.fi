# Privacy flow

## Потоки

| Источник | Данные | Получатель | Контроль |
|---|---|---|---|
| Checkout | имя, email, телефон, адрес | Deco Paint, Paytrail, PostNord, SendGrid | договор/заказ, минимизация |
| Account | профиль, история заказов | Deco Paint | auth, owner check |
| Analytics | поведение, device IDs | Google Analytics | consent |
| Advertising | conversion/enhanced conversion | Google Ads | ad consent + policy |
| Merchant | product data | Google | без customer PII |
| B2B application | company/contact data | Deco Paint | purpose/retention |

## Consent state

- До выбора: analytics/ad storage denied в EEA.
- После выбора: обновлять только разрешённые категории.
- Отзыв согласия должен быть доступен так же легко, как выдача.
- Security/checkout functionality не блокируется marketing consent.
- Consent version и timestamp должны быть проверяемыми без хранения лишних данных.

## Текущие проблемы

- Production release P0 удалил browser-side enhanced-conversion PII со
  страницы success и блокирует PII в Paytrail debug logs.
- Нет подтверждённой data retention/deletion automation.
- Нет описанной DSAR процедуры.
- GA4 user-provided data collection включён в property, но automatic
  collection выключен; raw/hashed email в текущем GA4-кандидате не передаётся.

## GA4 candidate 2026-07-30

- Авторизованные пользователи получают стабильный HMAC-based opaque User-ID.
- Секрет для HMAC не выводится в HTML и не хранится в репозитории.
- Для гостя используется только consented GA client/session identity.
- Клиентский sanitizer удаляет allowlist-нарушения и redacts email/phone-like
  строки; server payload builders не включают customer PII.
- В consent UI добавлен отдельный `ad_personalization`, выбор не применяется до
  сохранения, настройки можно повторно открыть и отозвать.
- Privacy notice явно описывает GA4, User-ID и исключённые данные.

## Критерии

- reject-all не создаёт analytics/ad cookies;
- revoke останавливает дальнейшие non-essential events;
- purchase без marketing consent остаётся валидным заказом, но не отправляет prohibited ad user data;
- ни один analytics/log payload не содержит plain email/phone/address;
- privacy notice перечисляет processors, цели, сроки и права.
