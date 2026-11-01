# Merchant feed production evidence — 2026-11-01

Runtime correction is deployed from reviewed commit 8d42fb4592591a198543a8f984f2744852f034e9 (PRs #13 and #14). Installed tasks.py SHA-256 is 7007d0c01b98d23cd1eff20c285105eff227bc1f33f1970929d1366be58dbda7. Both live API support files retain their audited hashes. No migrations or catalogue edits were performed.

78 isolated regression tests passed locally, on closed server staging, and in CI. All 149 managed offer prices were compared with the live anonymous storefront price endpoint on 1 November: zero differences. Homepage, product, cart and empty checkout smoke tests passed. The queue has one new supervised master and four child processes; no duplicate master was started.

The supplemental source merchant-feed-corrections-linked-2026-08-07.tsv retained its eight IDs, Google categories and product types. Only its stale availability column was removed; Google matched 8/8 rows, recognized every attribute, and reported no file issues. The exact published TSV is stored beside this document.

The Content API primary source default rule now prioritizes sources in this order: image corrections, linked feed corrections, efficiency labels, Content API, tilaustuote supplemental, public price override. This moves Content API only one position. The tilaustuote source contains legacy availability values, so that change leaves image/category/label precedence intact. The draft test processed 149 products, changed only availability (33 products at test time), and retained 149/149 Shopping approvals. Other pre-existing diagnostic warnings were not edited.

Initial 12 existing-offer updates were accepted on 31 October. A fresh public-price audit and existing-offer-only comparison on 1 November led to another 56 accepted upserts. Account inventory remained 172 products: 149 managed by this API and 23 from other sources. No additions or deletions were performed. Final Google processing is asynchronous; do not infer completion for all offers merely from accepted API responses.

Biomalta Extreme Fine (1050N) is confirmed in the Merchant Center UI at EUR 197.66, Backorder, Approved, Needs attention (0). It previously showed EUR 39.53 and a price mismatch. The site's displayed dispatch date is refreshed to 28 days ahead (29 November on 1 November).

Rollback of external precedence: restore Content API below tilaustuote, and restore the prior availability column to the eight-row linked file from its earlier controlled source. Do not remove products or replace the integration. Code backups and product snapshots remain private outside webroot; no customer data or credentials are stored here.
