# Product page performance recovery — 2026-08-20

## Production scope

Only these production files were changed:

- `shop/views.py`
- `shop/product_schema.py`

The product template, colour selector template, price endpoint, cart code,
models, campaigns, Merchant feed, and customer data were not changed.

## Root cause

When no colour had been selected during the first request,
`build_product_data()` generated an `AggregateOffer` by iterating every active
variant and calling `Variant.total_price(None)` for each one. Products with a
large colour palette therefore blocked the initial HTML response while all
variant prices were calculated.

## Fix

- Resolve at most one concrete active variant for the initial structured-data
  `Offer`.
- Prefer a variant matching the visible non-colour selections.
- Fall back to one real active variant if the independently built option lists
  do not form an existing combination.
- Remove the all-variant `AggregateOffer` fallback.
- Preserve the public price, availability, delivery information, return policy,
  reviews, colour AJAX endpoint, price AJAX endpoint, and cart behaviour.

## Verification

- Before: Marmorino Naturale Fine returned no bytes within 25 seconds.
- After warm-up: TTFB 0.59–0.64 seconds; total response 0.91–0.96 seconds.
- `MM 39` was selected successfully in the browser.
- Public prices returned by the production price endpoint:
  - 1 kg: EUR 15.59
  - 5 kg: EUR 68.45
  - 20 kg: EUR 248.49
- No public discount was returned (`discount_percent: 0`).
- Product JSON-LD still contains a real `Offer`, public price,
  `hasMerchantReturnPolicy`, `shippingDetails`, rating and review data.

## Rollback files on the server

- `shop/views.py.bak-20260820-before-performance`
- `shop/product_schema.py.bak-20260820-before-performance`

## Verified deployed SHA-1

- `shop/views.py`: `59cbfa5a37c36036211c292737bd1705f92ab3a1`
- `shop/product_schema.py`: `09f6dc25bdb8f531a4091259b0031c68dd8ee4d7`
