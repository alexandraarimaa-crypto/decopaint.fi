# Country-based default language — 2026-08-20

## Contract

- Finland: Finnish (`fi`).
- Sweden: Swedish (`sv`).
- Every other identified country: English (`en`).
- A manual language cookie or session selection always has priority.
- Search/Shopping crawlers stay Finnish to protect the Finnish canonical
  storefront from location-dependent indexing.

## Implementation

- Country headers from the hosting/proxy layer are used when available.
- Otherwise the visitor address is checked against local CC0 IPv4/IPv6 ranges
  for Finland and Sweden; a public address outside those ranges is `other`.
- No remote API request is made during a page load.

## Verification

- Seven unit tests passed.
- Live: FI homepage `200/fi`, SE catalog `200/sv`, US terms `200/en`, US product
  `200/en`.
- Manual English cookie on a Finnish request remained `en`.
- US Googlebot request remained `fi`.

## Safety and rollback

No prices, discounts, products, stock, orders, carts, payments, Merchant Center
or Google Ads settings changed. Restore the exact settings backup documented in
`docs/rollback.md` and restart Passenger to disable the middleware.
