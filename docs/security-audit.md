# Security audit

Дата: 30 июля 2026

## P0

### IDOR: сведения об оплате заказа

`users.load_payment_details(order_id)` не требует аутентификации и не проверяет владельца заказа. Числовой ID используется напрямую, затем запрашиваются платёжные данные.

Исправление:

- `@login_required`;
- `get_object_or_404(Order, id=order_id, user=request.user)` или отдельная admin permission;
- одинаковый 404 для отсутствующего и чужого заказа;
- rate limit и audit log без PII;
- тесты anonymous/owner/other user/admin.

### Paytrail callback/state

Успешный callback проверяет HMAC, но не обеспечивает полноценную проверку допустимого статуса, суммы, валюты и одноразового перехода. Повторный callback может повторно поставить задачу письма. COD success принимает произвольный `order_id`.

Исправление:

- отдельный server callback и customer return URL;
- транзакция БД + `select_for_update`;
- уникальный transaction ID;
- allow-list success statuses;
- сравнить merchant, amount, currency, order reference;
- переход только `pending -> paid`;
- email и analytics outbox только после commit, один раз;
- customer page получает opaque signed token или session-owned order.

### PII в логах

Платёжный и cart flow печатает request POST/GET, имя, email, телефон, адрес и callback параметры. `stderr.log` уже вырос до 7,13 MB.

Исправление:

- удалить debug prints;
- structured logging с allow-list полей;
- маскировать order ID/transaction ID;
- log rotation и короткий retention;
- считать существующий лог потенциально чувствительным и ограничить доступ;
- согласовать безопасное удаление после retention/legal review.

### Production debug и secrets

- `DEBUG=True`;
- hardcoded DB credential в административных scripts;
- OAuth client JSON находится в source tree;
- секреты необходимо ротировать после внедрения environment settings.

## P1

- cPanel 2FA не включён.
- Django 4.1.13 вне поддержки.
- destructive Merchant endpoints допускают GET.
- registration/email endpoint допускает user enumeration и email abuse.
- logout через GET.
- публичный directory listing на `develop.decopaint.fi`.
- HSTS, CSP и Permissions-Policy отсутствуют.
- cPanel Force HTTPS отображается Off; фактический redirect надо покрыть тестом.
- error responses/traceback история требует triage.

## Security headers — baseline

Есть:

- `X-Frame-Options: SAMEORIGIN`;
- `X-Content-Type-Options: nosniff`;
- `Referrer-Policy: same-origin`;
- secure session/CSRF cookies;
- `Cross-Origin-Opener-Policy: same-origin`.

Нет:

- HSTS;
- CSP;
- Permissions-Policy.

Вводить CSP сначала в `Report-Only`, затем исправить нарушения и включить enforcement.

## Rotation plan

1. Инвентаризировать все secret consumers.
2. Добавить environment variables и fail-closed startup checks.
3. Выпустить новые DB/Google/Paytrail/PostNord/SendGrid credentials.
4. Переключить staging, затем production.
5. Отозвать старые ключи.
6. Очистить source tree, archives и build artifacts.
7. Проверить логи и backup policy; не переписывать backup без согласованной процедуры.

## Не выполнено

Penetration test, dependency CVE scan в production environment, DAST authenticated flows и restore drill пока не выполнялись.

## Подготовленный P0 patch

В branch `security/p0-staging` (`1425dc7`) подготовлены owner checks, dynamic Paytrail HMAC validation, amount/transaction/status checks, DB locking, идемпотентные side effects, COD session ownership, удаление PII из confirmation page и POST/CSRF для Merchant mutations.

Paytrail logic основана на [официальной Payment API документации](https://docs.paytrail.com/): callback может вызываться несколько раз; подпись должна включать все сортированные `checkout-*` параметры; статусы `ok`, `pending`, `delayed` и `fail` обрабатываются раздельно.
