# Merchant availability and default variant correction

Issue #12 addresses two confirmed live mismatches. Orderable `order_item`
variants were submitted as out of stock, and the default-variant selector
ignored visible base/grain/gloss options. For Biomalta Extreme Fine this sent
the cheapest tintable base while the first page load selected white 5 kg.
The owner confirmed public white prices of EUR 197.66 / 395.33 / 790.65 for
5 / 10 / 20 kg and subsequently corrected the tintable variant in the admin.
This release does not change any catalogue price or stock flag.

The task now follows the template's first visible option queries before
choosing the palette colour. It keeps existing offer IDs. A missing default
selection fails instead of substituting a different cheaper variant.
Orderable variants are BACKORDER with a Finnish dispatch date four weeks
ahead, refreshed whenever the nightly job or an existing scoped task runs.
The current live product template independently shows the same 28-day
estimate. Stocked items retain their prior availability and pickup fields.

The live `google_shopping/tasks.py` exactly matches the main-branch baseline.
The live API adapter does not match the repository's adapter, and imports a
separate `merchant_payload.py` already forwarding availabilityDate. The
audited copies are retained in deployments/merchant-stock-price-20261031.
`scripts/build_merchant_stock_release.py` therefore builds **tasks.py only**
and pins both support modules without replacing them. The main-branch API
translator separately gains availabilityDate support for compatibility;
that file is not installed in the scoped production release.

Validation covers base/grain/gloss selection, stock pickup, rolling dates,
Finnish midnight and DST, undated backorders and both API translators. The
isolated suite must run on closed staging without Merchant writes, analytics,
email or production customer data. Run an import and read-only payload audit
against production settings before installation, using the candidate task
module, after matching the three pinned source hashes.

Deployment: use the reviewed GitHub commit; build its manifest; verify current
hashes; back up the one runtime file and processed/input attributes for the
existing offers outside webroot; install only tasks.py; restart Passenger and
the managed Django-Q workers without starting duplicate masters. No database
migration or database write is required. Preserve all other runtime files.
After smoke tests, refresh existing offers only. Do not call full-clean upload,
sync_missing_products or any deletion path. Verify processed price,
availability and date in Merchant Center; higher-priority supplemental data
may require a separate scoped rule correction. Request the Biomalta website
check only after the processed values match.

Rollback: restore the verified tasks.py backup and restart the same services.
No database restore. External input rollback must use the saved per-offer
inputs through their owning data source; preserve IDs and never delete offers.
