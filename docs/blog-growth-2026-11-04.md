# Blog search and enquiry improvements — 4 November 2026

Issue: https://github.com/alexandraarimaa-crypto/decopaint.fi/issues/19

## Public baseline

Read-only audit of https://decopaint.fi/blog/, the lime-finish comparison,
paint-quantity guide, Marmorino Naturale product, robots.txt and sitemap.xml.
The two guide pages returned 200, index/follow and self-canonical URLs and
were present in the sitemap. Both inherited the generic shop description.
No guide-to-guide links were found on those two pages, and the Marmorino page
did not link back to its buying guide. Existing article CTAs led to /contact/.
The two guides were published 31 October and 3 November; no conclusion about
their organic performance can be drawn this early.
Search Console and GA4 reports were reviewed read-only after explicit owner
authorization on 5 November. Private performance figures are retained only in
the task deliverables, not this public source repository. No uplift from the
unreleased candidate is claimed.

## Candidate behavior

- Descriptions for four inspected guides (comparison, quantity, fibreglass
  wallpaper and Ottocento) are written in FI/SV/EN. All other
  articles derive descriptions from their currently translated visible content.
- Detail canonicals use the article path; blog pagination keeps only its
  resolved page number. New BlogPosting JSON-LD and article Open Graph data
  match the visible title, description, actual creation time and image.
  No personal author, update date, review or offer is invented.
- Up to three related guides prioritize common products, then the same category;
  the current guide is excluded. Product pages show their existing linked guides.
- New article CTAs link to /contact/?guide=<public-slug>#project-enquiry.
  Only an existing validated article slug triggers a translated, editable prompt.
  The existing form, CSRF, mail destination and POST behavior are preserved.
  No email, phone, image, free text or other personal data enters a URL.
- New interface text is supplied in Finnish, Swedish and English without relying
  on unversioned production translation catalogs.
- Blog view counting and modeltranslation configuration remain untouched.

## Measurement after deployment

Record deployment date/commit and export Search Console pages and queries for
Finland, with brand and non-brand queries reviewed separately. Compare 28-day
windows and the previous year where data exist. Record indexing status for
both guides using URL Inspection. Compare clicks, impressions, CTR and position
by page/query; low CTR must be assessed alongside position and query mix.

In GA4, review Organic Search landing pages, product-page visits, add_to_cart,
confirmed purchases and revenue. Include repeat-visit purchase paths. Existing
form submissions do not have a verified server-success measurement in this
scope: do not count a CTA click or submit-button click as generate_lead.
Verify the actual email-success event before using lead conversion rates.
Any account configuration requires its own approved change.

Check indexing and errors after release; make a first directional review after
28 days and a fuller review after 8–12 weeks. These are review intervals, not
rank or revenue guarantees. No reminder or recurring task has been created.

## Content priorities after account data are available

1. Marmorino hinta / m²: build a real product-and-primer cost example with dated
   live prices, exact pack sizes and the chosen application system. Do not invent
   installer labour rates or combine incompatible products.
2. Kalkkimaali vai tavallinen seinämaali: compare finish, substrate, maintenance
   and the real use case; link to distinct product/category destinations.
3. Tehosteseinä olohuoneeseen: use genuine project photographs, actual substrate,
   area and measured material use, with permission for publication.
4. Marmorino-seinän puhdistus ja hoito: follow the current manufacturer system
   and link to compatible care/protection products.
These are candidates, not measured high-volume keywords. Check existing pages
and queries before creating a second page for the same search intent.

## Release gate and runtime reconciliation

Status: local tested candidate only. No production CMS, database, order, price,
stock, payment, email, Merchant or analytics configuration was changed.

The live admin has translations and a view counter that are not present in the
sanitized repository's blog model/view files. Do not deploy the full checkout
or overwrite deployed blog/models.py or blog/views.py from this repository.
Reconcile the current deployed template bytes with GitHub first. The base and
product templates are also shared with the audited sales-flow runtime projection.
Apply the small reviewed template hunks to an audited, source-controlled runtime
snapshot and commit any reconciliation before producing a release.

After CI/review, deploy the exact reconciled GitHub commit to closed staging.
Use synthetic data only, isolated database and disabled external writes. Confirm
external 403/noindex, all locales, guide relevance, real canonical/meta/schema,
contact prefill/escaping and unchanged ordinary contact form. Submit a synthetic
message only against a staging locmem mail backend, never the production inbox.
Check product selection/cart/checkout smoke without a real order or payment.

Prepare a verified backup of the affected templates/helpers and rollback to the
previous exact commit. No schema or content migration is needed. Owner approval
is still required by AGENTS.md before production activation. After activation,
read-only smoke the two guides, associated product, contact, sitemap and checkout.

## Local verification

The isolated regression command (see docs/testing.md) covers the new guides plus
users, Paytrail, Merchant, analytics, search, SEO, legacy URLs and sales release.
Use test settings; no customer records or credentials are needed. The new tests
exercise FI/SV/EN descriptions and prompts, HTML/JSON escaping, clean canonicals,
related-guide relevance, reverse product links and generic-contact fallback.
Closed hosting staging and post-production checks are not marked complete.
