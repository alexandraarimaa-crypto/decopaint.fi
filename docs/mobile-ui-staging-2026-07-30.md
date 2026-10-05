# Mobile UI staging candidate — 2026-07-30

## Status

Approved visual direction has been converted into a Django candidate and
activated on the closed staging release `mobile-ui-20260730`. Production is
unchanged and still requires a separate explicit approval.

## Baseline

Mobile PageSpeed baseline captured before implementation:

- Performance: 69
- Accessibility: 73
- Best Practices: 96
- SEO: 92
- FCP: 2.9 s
- LCP: 10.7 s
- TBT: 90 ms
- CLS: 0
- Speed Index: 3.5 s

## Scope

The candidate:

- modernizes the mobile header and existing Bootstrap offcanvas menu;
- adds task-based search and category shortcuts to the homepage;
- reorganizes category cards and popular products on small screens;
- adds consultation and material-calculator entry points;
- improves category intro, catalog search/navigation tools and product cards;
- adds a non-transactional material estimate on product pages;
- adds a sticky product CTA connected to the existing `cart_form`;
- improves empty cart and checkout presentation;
- exposes an essential-only action in the existing consent banner;
- removes the viewport zoom restriction;
- gives the first hero image explicit dimensions and high fetch priority;
- reduces the requested Urbanist font variants.

## Explicit non-scope

- no database or migrations;
- no prices, taxes, stock, variants or product content mutations;
- no cart calculation changes;
- no delivery method changes;
- no Paytrail/PostNord changes;
- no Merchant Center writes;
- no GA4 event schema or consent semantics changes;
- no production customer/order data copied to staging.

## Runtime files

- `shop/templates/shop/base/base.html`
- `shop/templates/shop/base/header.html`
- `shop/templates/shop/base/modal.html`
- `shop/templates/shop/else/main.html`
- `shop/templates/shop/else/main_popular.html`
- `shop/templates/shop/product/list.html`
- `shop/templates/shop/product/detail.html`
- `cart/templates/cart/cart.html`
- `cart/templates/cart/checkout.html`
- `shop/static/assets/css/mobile-modern.css`
- `shop/static/assets/js/mobile-modern.js`

Staging-only validation:

- `scripts/validate_mobile_ui.py`

Candidate checksums are stored in
`work/mobile-ui-candidate-manifest-20260730.sha256`.

Closed-staging installation evidence is stored in
`docs/mobile-ui-staging-release-evidence-2026-07-30.md`.

Staging archive:

`work/decopaint-mobile-ui-staging-20260730.tar.gz`

SHA-256:

`4d755907b52a7f6ea54fb3b8d8e899eec709b02316176a959a0e1806c2268aed`

Clean production-ready runtime archive:

`work/decopaint-mobile-ui-production-ready-20260730.tar.gz`

Clean archive SHA-256:

`796a31f40a02ab8ac3a448a451674c6907a148300eabb2e3fc45e0b74080d05c`

## Local evidence

- static candidate contract checks: `MOBILE_UI_STATIC_CHECKS_OK=1`;
- JavaScript syntax: passed with Node `--check`;
- no new browser network writes in `mobile-modern.js`;
- checkout form IDs, payment/delivery values and Analytics integration remain;
- baseline rollback archive:
  `work/decopaint-mobile-ui-baseline-20260730.tar.gz`;
- baseline archive SHA-256:
  `0ff8188f6b6a5068de405cf435df8d6bcfd676a783fb63f687a2f7155c03d1ae`.

## Staging acceptance

1. Candidate manifest matches uploaded files.
2. Django template compilation passes.
3. `manage.py check --deploy` has no new release-specific findings.
4. Existing full isolated test suite remains green.
5. Closed staging remains HTTP 403 externally and keeps the noindex header.
6. Synthetic mobile journey passes:
   homepage → search/category → product variant → calculator → cart → checkout.
7. Delivery and payment choices remain selectable with synthetic data.
8. Reject/accept/reopen/revoke consent paths remain functional.
9. No GA/Ads requests when staging `ANALYTICS_ENABLED=False`.
10. Mobile viewport checks pass at 360×800, 390×844 and 430×932.
11. Desktop smoke confirms no unintended visual regression.
12. Lighthouse does not regress and the LCP candidate improves versus 10.7 s.

## Production gate

No production installation is authorized by the current approval. After staging
evidence and visual acceptance, request a separate explicit production approval.
