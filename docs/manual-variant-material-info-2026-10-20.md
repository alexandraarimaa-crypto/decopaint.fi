# Optional manual material information — 20 October 2026

GitHub task: #6. Baseline: `6816bb7` (main at implementation start).

## Behavior and administration

Open `/admin → Tuotteet → product`. The **Pakkauskohtaiset lisätiedot**
inline lists the existing variants, identified by read-only item code, package
size, colour, base, grain and gloss. Enter **Hinta €/m²** (e.g. `4,85`) and
**Riittoisuus (m²)** (e.g. `85–135` or `100`, without units), then save the
product. Clear either input and save to remove that information. Both fields
are also available on each existing variant's change page. Pagination retains
the existing inline paginator approach, with 100 variants per page.

Values belong to each actual Variant row, including its colour/finish/base.
There is no product-wide fallback and no copying to other variants. If the
same package has several colour rows, enter the information for each desired
row. Existing products, packages and prices are not edited or backfilled.

The existing variant-price response adds two nullable values. The page shows
`alk. 4,85 €/m²` beside the final price and `Riittoisuus 85–135 m²` beside the
package selection. Each empty value is hidden independently. Requests clear
old information immediately; a response superseded by a pending selection
cannot display the previous variant's manual information. The existing price
request queue, variant resolver and all monetary arithmetic remain unchanged.
Quantity, discounts, taxes and the material calculator do not alter these
manual values. Text uses `textContent`, never HTML insertion. Layout uses the
existing small muted text and wrapping Bootstrap flex containers.

## Migration and release gates

`shop.0061_variant_material_info` adds only nullable Decimal/Char columns to
Variant. It contains no data operation, default backfill or modification of
prices, products, packages, stock, orders, customer data or external services.

1. CI and review must pass before merging. Deploy the exact approved commit to
   closed staging with authorization and noindex. Use an isolated synthetic DB
   with Merchant/payment/email integrations disabled.
2. Before changing any deployed DB, obtain the owner's explicit approval as
   required by AGENTS.md, create a private verified DB backup, and record its
   restore verification and current release/migration state. No deployed DB
   was accessed or migrated during implementation.
3. Check `showmigrations shop` against the expected deployed `0060` translation baseline. Run
   `sqlmigrate shop 0061`, assess MySQL table size/locking and maintenance needs,
   then apply only the approved migration with `migrate shop 0061`.
4. Deploy matching code and collect static assets before reopening traffic.
   Test create/edit/clear on staging, desktop and mobile, with multiple sizes,
   colours and rapid switching. Check quantity, discounts, calculator, cart,
   checkout and logs. Check CSRF and staff permissions remain enforced.
5. Production deployment remains a separate approval after recorded staging
   evidence and verified backup. This candidate is not a production release.

## Validation

Automated coverage includes nullable fields, package/product/colour isolation,
manual single/range coverage, comma decimal input, clearing, zero/negative
prices, admin inline writes preserving package and base price, API additions,
JS formatting, independent visibility, text-only rendering, and clearing.

Commands:

```sh
python manage.py test shop.tests_variant_material_info --settings=config.variant_info_test_settings
python manage.py test shop.tests_material_calculator --settings=config.test_settings
node scripts/test_variant_material_info.mjs
```

The existing isolated security/price/payment/Merchant suite remains in CI.
Actual results and verification limitations are recorded in the PR.

## Rollback

Prefer reverting to the preceding reviewed application/static release while
leaving both nullable columns in place; prior code ignores them and manually
entered values remain available. No DB restore is needed for this rollback.
Retain the new migration file in migration history when comparing state.
Dropping these columns with `migrate shop 0060_attribute_a_class_en_attribute_a_class_fi_and_more` destroys entered information:
only do so after separate approval and a verified private backup/export.
Do not restore a full production DB over new orders for this feature rollback.

## Deployed baseline audit — 22/23 October 2026

The authenticated cPanel audit found that production is ahead of the recovered
GitHub source in storefront translations, views, product schema and product
layout. Production already contains translation migration
`0060_attribute_a_class_en_attribute_a_class_fi_and_more`; the new migration is
therefore **0061**, depending on that exact existing migration. The existing
0060 file is recovered unchanged from production; do not run it as a new
migration in production or use fake migrations to conceal a mismatch.

The protected, source-only audit archive (no settings, data, uploads or secrets)
has SHA-256 `be248cbd77e3edf711dde6850ffb0771f86d2a730a47842eb642da1ed910c7fd`.
Models and admin match the pre-feature GitHub baseline. The reviewed runtime
baseline for the differing product files is tracked under
`deployments/manual-variant-info-20261023/baseline/`.

Use `python scripts/build_manual_material_release.py --output <private-dir>`
to generate the **scoped runtime release**, rather than replacing the live
views or product template with the older recovered root files. The builder
adds only the two response fields and the optional labels to the audited
runtime, retaining its existing translations, schema, selection, calculator
and cart behavior. The release manifest contains exact pre-release production
hashes, candidate hashes and an explicit file list. Abort if current live
hashes differ. Never copy the sanitized repository settings into production.
The inline now uses a shop-owned pagination template/tag and requires no
production settings edit or extra application registration.

Translation and product-schema snapshots are staging support only: they are
not production replacement files. `scripts/test_manual_material_release.py`
builds this runtime projection with an isolated synthetic database, asserts
that every existing view function is unchanged apart from the two extra JSON
fields, and runs the real admin/API suite. This compatibility projection is
explicitly limited to the audited files; it is not a claim that all historical
production/repository drift has been reconciled.

Staging must be a new immutable release assembled from the GitHub commit and
this projection, using fresh synthetic data with outbound integrations off.
The existing active staging is preserved as the rollback target. Record manual
browser/responsive results before requesting production approval. No live
schema or product value has been changed by this audit or candidate build.
