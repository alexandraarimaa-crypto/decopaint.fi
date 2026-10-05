# Product Open Graph and structured-data R8 production release — 2026-08-02

## Outcome

The remaining Finnish SEO product-metadata follow-up is complete in production.
Product pages now expose shareable Open Graph metadata and source-grounded
Product JSON-LD. The release did not change catalog data, prices, inventory,
orders, checkout, delivery, Paytrail, Merchant Center or Analytics settings.

## Design decision

Every active product has variants and some products have more than 20,000.
Embedding every variant would materially increase HTML size and mobile load.
A product-level minimum price was also unsafe because several variants share
the same visible option tuple while the storefront resolves one deterministic
record.

R8 therefore uses this rule:

- every active product receives Product name, description, absolute image,
  canonical URL, OIKOS brand and SKU when available;
- an Offer is added only when the same server-side option tuple used by the
  visible price widget resolves one concrete active variant;
- price is the anonymous/public storefront price for that exact variant;
- `order_item=True` becomes `PreOrder`; otherwise it becomes `InStock`;
- no exact variant means no Offer, never an invented price or availability.

All JSON is serialized server-side and escapes `<`, `>`, and `&` before it is
placed in the script element.

## Release identity

- Closed staging:
  `/home/decpai/staging/releases/seo-fi-p0-20260802-r8`.
- Accepted archive:
  `/home/decpai/staging/decopaint-seo-r8-20260802-v4.tar.gz`.
- Archive SHA-256:
  `e20a4de2258b97e8de8774758e3f32ba13d6e3ef55c6d13f98776d17405008a9`.
- Production backup:
  `/home/decpai/release-backups/seo-product-og-r8-20260802T174800Z/before.tar.gz`.
- Backup SHA-256:
  `9ad16b84fcbb0fa56401488fa655cc4769c153145d36d39b1d9ef782379a5144`.
- `shop/product_schema.py` was absent before the release and is recorded by
  `product_schema_was_absent`.

## Baseline and deployment

Before installation, the current production hashes were saved. Homepage,
Sterylplus, checkout and payment-method endpoints were healthy. Active
`stderr.log` was 7,483,667 bytes.

The archive was verified locally and on the server. Staging static validation,
no-migration check and all 17 tests passed. The backup passed `gzip -t` and
listed exactly the five replaced paths.

Five existing files and one new helper were installed as one small code-only
batch. `manage.py check` completed before Passenger restart. Installed files
then matched the closed-staging candidate byte-for-byte.

## Verification

- Full read-only audit: 154 active products, 154 valid, zero errors.
- 115 pages expose exact Offers; 39 safely omit unresolved Offers.
- Maximum rendered product HTML: 304,565 bytes.
- Sterylfix: schema 26.77 EUR/InStock equals AJAX 26.77, `order_item=False`.
- Sterylplus: schema 30.72 EUR/PreOrder equals AJAX 30.72,
  `order_item=True`.
- Ultrasaten: schema 48.00 EUR/InStock equals AJAX 48.00,
  `order_item=False`.
- Veldecor: schema 52.86 EUR/PreOrder equals AJAX 52.86,
  `order_item=True`.
- Homepage, both product types, empty checkout and payment methods: HTTP 200.
- Warm response times: 0.081–0.214 seconds.
- One gtag loader, one analytics asset and default consent initialization remain
  present; the existing product GA4 payload remains present.
- `stderr.log` reached 7,483,759 bytes during restart and then stayed stable;
  its 92-byte delta has zero error/traceback markers.

The production DB account correctly refused creation of a test database when a
redundant production test run was attempted. The command stopped before tests
started and changed no data. The exact installed code had already passed all
17 tests against isolated staging.

## Integration impact

Merchant synchronization and feed code were not touched or invoked. JSON-LD
uses the storefront's existing variant resolver and public pricing, so it does
not become another source of catalog truth. GA4, consent, checkout, mail,
Paytrail and delivery code were not changed. No synthetic order, payment,
message, Merchant request or Analytics event was created.

## Rollback

Verify and extract `before.tar.gz` into the production root, remove only the new
`shop/product_schema.py`, run `manage.py check`, restart Passenger and repeat
product/checkout/payment smoke. No database restore or external integration
rollback is permitted or required.
