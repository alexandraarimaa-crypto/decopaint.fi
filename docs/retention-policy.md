# Retention policy

Черновик для утверждения владельцем и юристом; не является юридической консультацией.

| Данные | Предлагаемый срок | Основание/действие |
|---|---:|---|
| Бухгалтерские данные заказа | по требованиям Финляндии | ограничить доступ, не удалять раньше закона |
| Customer account | пока активен + утверждённый grace period | self-service deletion/anonymization |
| Abandoned cart/session | 30–90 дней | минимизация |
| Application/security logs | 30–90 дней | без PII, доступ только ops |
| Payment callback technical log | 30–90 дней | IDs маскированы, без payload/signature |
| Marketing consent evidence | срок согласия + audit period | version, timestamp, source |
| B2B application | утверждённый decision period | удалить/анонимизировать отклонённые заявки |
| Staging data | максимально коротко | только synthetic/anonymized |
| Backup | 7 daily сейчас | определить monthly/legal tier и restore tests |

## Обязательные действия

- Реестр полей PII и processors.
- Документированные delete/anonymize workflows.
- Legal hold исключения.
- Автоматическое удаление логов.
- Проверка, что удаление аккаунта не разрушает обязательные бухгалтерские записи.
- DSAR export/delete process с идентификацией заявителя.
