# Confidential sanitized audit snapshot

Создано 30 июля 2026 из production source только для статического аудита.

Это не deployable artifact:

- production settings и секреты исключены;
- media/static/database/logs исключены;
- два legacy maintenance script с hardcoded DB credential исключены;
- OAuth credential JSON исключён;
- customer/order data не копировались.

До создания рабочего Git-репозитория необходимо:

1. создать environment-based settings;
2. ротировать найденные credentials;
3. добавить synthetic fixtures;
4. восстановить нужные maintenance commands без hardcoded secrets;
5. пройти полный test suite на закрытом staging.
