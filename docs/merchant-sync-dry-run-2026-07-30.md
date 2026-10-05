# Merchant Center sync dry-run — 2026-07-30

## Scope

Read-only comparison of:

- products returned by the Google Merchant Center Content API;
- the single best active, available variant selected by the current
  `google_shopping` synchronization logic for each active website product.

The diagnostic did not call product insert, update, delete, background queue,
or the existing synchronization endpoints.

## Result

| Metric | Count |
| --- | ---: |
| Merchant product resources | 141 |
| Merchant unique offer IDs | 141 |
| Website eligible best variants | 154 |
| Website unique offer IDs | 154 |
| Matching offer IDs | 121 |
| Present on website only | 33 |
| Present in Merchant only | 20 |
| Merchant duplicate offer IDs | 0 |
| Website duplicate offer IDs | 0 |
| Merchant resources without offer ID | 0 |
| Eligible website variants without item code | 0 |

Expected net change after a reviewed synchronization would be 33 additions and
20 removals, leaving 154 unique offer IDs. This is only set arithmetic, not an
approval to mutate Merchant Center.

## Website-only offer IDs

These are eligible according to the current website synchronization rules but
are absent from Merchant Center:

```text
1059RETE
FT0S0TR00E
GRIP1056PG
I0TMC0000E
IAA000000J
ICP000000E
IFN000000E
LPC1C0000E
LPR0F0000Z
LTRF00000E
LTT000AC0F
NFA100000B
OIAPENS300
OIAPENS500
OIAPET0G00
OIARULS000
OIARULS100
OIASPA0000
OIASPA1S00
OIATAMLT00
OIATAMR000
OISCOPM00D
OISEFSW00E
OISIGR000B
OISPIG000E
OISULOTR1E
PALPAL0D0E
TD103TR00D
TT0N10000E
W03010000D
W03020000D
W03030000D
W03040000D
```

## Merchant-only offer IDs

These exist in Merchant Center but are not selected by the current website
synchronization rules:

```text
1052FINE
12975538193447625686
481895917413437093
5687090640067733162
FT0S0TR00P
I0TMC0AA0S
IFN000000O
LPC1C0000O
LTT000DO0F
LTT000TO0F
NFA103102G
OISCOPM00S
OISES7339E
OISULOTR1O
PALPAL129E
TD107TR00S
W03018784P
W03028784P
W03038784P
W03048784P
```

Do not automatically delete this group. It includes several IDs that appear to
be manually created or from a different item-code convention. Each must first
be mapped to its product, source, and intended canonical offer ID.

## Reconciliation result

- 19 Merchant-only offers have an exact title and product-URL match with 19
  website-only canonical IDs. These are ID migrations, not 19 additional
  products.
- 14 website-only offers have no Merchant-only counterpart and are genuine
  additions candidates.
- `1052FINE` is an old Biomalta Extreme Fine offer. The current website
  selection is `1050N`. Both IDs are approved for Shopping, DisplayAds and
  SurfacesAcrossGoogle, so `1052FINE` is a duplicate-removal candidate only
  after separate approval.
- Three Merchant-only offers use automatically crawled numeric IDs; the
  remaining unmatched IDs are API or unknown/manual sources.

## Safety finding

The existing `sync_missing_products()` and
`incremental_update_optimized_single_variant()` flows are not dry-run
operations. They can delete Merchant-only products and add or update website
products. They must not be used for diagnostics without a separate dry-run
implementation and explicit approval for the final mutations.

## Recommended next step

Validate the 14 genuine additions and add them without deleting anything. Then
add the 19 canonical replacement IDs, wait for Merchant approval, and request a
separate owner decision before removing any old counterparts.

## Approved additions-only execution

The owner separately approved adding the 14 genuine products and 19 canonical
replacement IDs without updating or deleting existing Merchant products.

### Preflight

| Check | Result |
| --- | ---: |
| Target offer IDs | 33 |
| Already present before insertion | 0 |
| Invalid or incomplete payloads | 0 |
| In-stock payloads | 29 |
| Out-of-stock payloads | 4 |

The four website variants transmitted as out of stock were:

```text
1059RETE
IAA000000J
TD103TR00D
TT0N10000E
```

Availability was not overridden because stock/order settings were outside the
approved scope.

### API compatibility finding

The production product-data builder emitted legacy top-level keys
`pickup_SLA`, `pickup_method`, and `storeCode` for the 29 in-stock products.
Google rejected those requests without creating products. The additions-only
execution normalized the first two keys to `pickupSla` and `pickupMethod` and
removed unsupported top-level `storeCode`; the same 29 products were then
accepted.

The additions-only run initially used one-time request normalization. A
separately tested production fix was deployed later on 2026-07-30:

- regular payloads now emit `pickupMethod` and `pickupSla`;
- legacy payloads are normalized before the Content API call;
- unsupported top-level `storeCode` is removed;
- confirmed online and COD orders queue an upsert-only refresh for the distinct
  products in that order;
- the order-triggered path never runs full-catalog deletion.

Validation completed in closed staging (23 tests, `OK`) and in production with
import, payload compatibility, queue-process, and HTTP smoke checks. No
synthetic production order was created.

### Final Merchant result

| Metric | Count |
| --- | ---: |
| Merchant unique offer IDs after propagation | 174 |
| Target offer IDs present | 33 |
| Target offer IDs missing | 0 |
| Initially approved by Google | 18 |
| Pending Google processing | 15 |
| Disapproved | 0 |
| Product updates performed | 0 |
| Product deletions performed | 0 |

The 20 pre-existing Merchant-only IDs were retained. The 15 pending products
were still undergoing image/attribute processing. Observed issue codes were:

- `image_link_pending_crawl` on 15 products;
- `missing_potentially_required_attribute` on 17 products;
- `text_value_too_long` on 12 products;
- `image_too_big` on 2 products;
- `image_link_internal_error` on 1 product.

These were pending/warning signals in the first post-insert check, not
disapprovals. A later read-only check should confirm the final Google review
result before any content or image updates are proposed.
