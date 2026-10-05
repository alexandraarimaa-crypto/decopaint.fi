# CRO backlog

Все гипотезы требуют baseline и не должны ухудшать доступность, SEO или точность заказа.

| Приоритет | Гипотеза | Метрика | Риск |
|---|---|---|---|
| P0 | Корректная server-side цена/наличие повышает доверие | view → add-to-cart | расхождение вариантов |
| P0 | Ясные delivery time/cost рядом с CTA снижает неопределённость | add-to-cart, checkout | неверные обещания |
| P0 | Mobile LCP improvement уменьшает bounce | engaged sessions, purchase | visual regression |
| P1 | Sticky mobile CTA на длинной product page | add-to-cart | перекрытие контента |
| P1 | Calculator расхода с объяснимой формулой | add-to-cart/value | неверный расчёт |
| P1 | Образцы/цветовые карточки как отдельный CTA | lead/order | операционная нагрузка |
| P1 | Trust block: returns, payment, delivery, support | checkout start | clutter |
| P1 | Checkout field reduction и inline validation | checkout completion | интеграции |
| P2 | Gallery: реальный интерьер + material close-up | engagement | тяжёлые изображения |
| P2 | Comparison table по системам/поверхностям | category → product | контентная точность |
| P2 | B2B CTA с явной ценностью и SLA | qualified applications | неготовый процесс |

## Приоритетные product-page элементы

1. Цена, размер/вариант и доступность без JS-задержки.
2. Расход, площадь покрытия и нужное число упаковок.
3. Для каких оснований и помещений подходит.
4. Срок и стоимость доставки/самовывоза.
5. Инструкции, datasheet и safety documents.
6. Возврат и поддержка.
7. Реальные изображения результата и упаковки.

## Эксперименты

- Минимум одна primary metric и guardrails.
- Не запускать A/B при недостаточном трафике; использовать sequential qualitative validation.
- Фиксировать дату, вариант, аудиторию, результат и решение.
- Не объявлять победу по кликам, если paid-order rate или margin ухудшились.
