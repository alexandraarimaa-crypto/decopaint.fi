# Project recovery audit - 2026-08-20

## Scope

The audit reviewed all locally available Codex project sessions from 20 July
through 20 August 2026, their working directories, release reports, Git
history, generated patches, and the sanitized source tree. Unrelated personal
chats were excluded and no chat transcripts are stored in the repository.

## Recovered code history

- Sanitized production baseline.
- Paytrail and order-security P0.
- Automatic Merchant synchronization after confirmed orders.
- Consent-aware GA4 ecommerce and Google Ads enhanced-conversion handling.
- Mobile UI and information-card assets.
- Source-grounded Finnish product search.
- Finnish SEO P0/R7 and Product Open Graph/JSON-LD R8.
- Merchant API migration code, Customer Reviews opt-in, and image payload work.
- Footer links for LinkedIn and YouTube.
- Cart root route and GA4-derived permanent redirects.

The original Git history ended at SEO R7. R8, product search, mobile assets,
Merchant/analytics follow-ups, and several template changes existed only as
working files or release packages and are recovered on the GitHub baseline
branch.

## External changes not represented as code

- Product relationships corrected in the CMS after the 404 crawl.
- Published multilingual blog posts and their CMS media records.
- Merchant Center, Google Ads, Analytics, and Google Cloud configuration.
- Product price, availability, preorder date, and other catalog database data.
- Hosting configuration, production media, databases, backups, and runtime
  secrets.

These systems require dated evidence or controlled exports; they must not be
reconstructed from guessed values or committed secrets.

## Remaining verification

The in-app cPanel session was unavailable during this audit, so the recovered
tree must be compared once against the current sanitized production source
before the first GitHub-driven production release. This is a read-only source
comparison, not a database or media export.
