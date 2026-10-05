# Staging runbook

Статус на 30 июля 2026: закрытый server-side staging развёрнут, migrations и 17 regression tests выполнены успешно. Внешний доступ остаётся запрещённым.

## Подготовленные артефакты

- Git branch: `security/p0-staging`
- Commit: `1425dc7`
- Final patch archive: `work/decopaint-p0-staging-final.tar.gz`
- SHA-256: `b898148d489cdbc51bee60e1be4218414cfd2882e894cab113c6d389f5237d84`
- Закрывающий `.htaccess`: `work/staging.htaccess`

## Изоляция

Целевая схема:

- код: `/home/decpai/staging/decopaint`;
- БД: отдельная SQLite в `/home/decpai/staging-data/`;
- production MySQL не подключается;
- production users/orders не копируются;
- email использует locmem backend;
- Merchant writes отключены;
- Paytrail credentials заменены staging-заглушками;
- отдельные session/CSRF cookie names;
- `DEBUG=False`;
- внешний доступ запрещён;
- `X-Robots-Tag: noindex, nofollow, noarchive`.

Фактическое размещение:

- release: `/home/decpai/staging/releases/1425dc7`;
- active symlink: `/home/decpai/staging/decopaint`;
- SQLite: `/home/decpai/staging-data/decopaint.sqlite3`;
- document root: `/home/decpai/public_html/develop`;
- внешний ответ: HTTP 403.

## Порядок развертывания

1. Создать server directories с правами только владельца.
2. Скопировать production source без settings, OAuth JSON, media, static, logs, exports и backup.
3. Наложить patch archive и проверить SHA-256.
4. Сгенерировать отдельный random `SECRET_KEY` вне web root.
5. Построить secret-free staging settings через `scripts/build_staging_settings.py`.
6. Выполнить secret scan.
7. Запустить migrations только в staging SQLite.
8. Запустить `manage.py check --deploy`.
9. Запустить `users` и `pk_paytrail` tests.
10. Установить закрывающий `.htaccess`.
11. Выполнить server-side smoke tests.
12. Не подключать staging к production Paytrail, Merchant или SendGrid.

## Acceptance gates

- anonymous и чужой пользователь не видят payment details;
- success callback проверяет все `checkout-*` поля, HMAC, merchant, transaction и amount;
- `ok` переводит заказ в paid один раз;
- `pending/delayed` не переводит заказ в paid;
- повторный callback не дублирует письмо;
- paid order нельзя отменить cancel callback;
- COD confirmation доступен только owner/session;
- confirmation template не содержит customer PII/enhanced-conversion payload;
- Merchant mutation endpoints требуют POST + CSRF и отключены на staging;
- logs не содержат POST/GET payload, email, телефон, адрес или signature.

## Rollback

Staging находится вне production app root. Откат состоит в отключении Passenger directives и возврате закрывающего 403 `.htaccess`; production код и БД не меняются.

## Результат проверки 2026-07-30

- Django `check --deploy`: выполнен, только ожидаемые staging/legacy warnings.
- Migrations: выполнены в отдельной SQLite.
- Test suite: 17 tests, `OK`.
- WSGI import: `WSGI_IMPORT_OK`.
- External isolation: HTTP 403.
- Robots header: `noindex, nofollow, noarchive`.
- Production smoke-check: HTTP 200.
