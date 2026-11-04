# Sales flow correction — issue 17

Baseline period: 27 October–2 November 2026. Ads: 18,896 impressions, 167 clicks, EUR 101.49, one primary brand purchase EUR 88.64. Two genuinely paid shop orders total EUR 123.14; GA4 recorded three transactions/EUR 211.78 because one transaction was duplicated. Product-to-cart funnel: 86 product-view users, four cart users; 65 product-view users were mobile. Historical totals are a baseline, not an expected immediate uplift.

Production already has sticky mobile buying, reviews, finished-surface pictures and manual package information. Preserve those features. The actual defects are competing browser/server purchase owners, raw GA/GS cookie envelopes sent as MP identities, stripped campaign parameters, add-to-cart measured before successful addition, ambiguous total-coat consumption and checkout delivery estimates hidden in tooltips.

Marmorino FINE technical sheet: https://decopaint.fi/media/product_documents/marmorino-naturale-mn-10-en.pdf, Application/Yield: 1–1.5 kg/m² in two coats. Existing 5 kg and 20 kg coverage (10–15 and 40–60 m²) contradicts this. Correct to approximately 3.3–5 and 13.3–20 m². Existing public retail 49.32/178.56 EUR remains unchanged; minimum indicative material cost per m² becomes 9.86/8.93 EUR. Other manual product values remain untouched.

The calculator is deliberately eligible only for explicit full-coat rates and compatible active package labels, rounds package counts upward, uses current selected unit price and requires a separate Apply quantity button. No generic material consumption assumption or automatic checkout action.

Validation and deployment evidence must be appended after completion. Success should be judged over a subsequent complete period by unique paid transactions, product→cart and checkout→paid conversion, acquisition source consistency and cost per paid order. This release does not promise a sales increase or change ad budget/primary keywords.

## Release evidence

PR #18 merged as `65b82d0`; CI 41873815094 passed. Exact-source private staging passed 13 new tests. Source/static installation verified 25 targets and private backups, and the three descriptive Marmorino rows changed with every variant field unchanged. Smoke uncovered the hosting's separate public static alias and entity-encoded rich-text delivery copy; public assets were republished with exact HTTP content hashes, and the delivery-copy follow-up fixes the encoded copy without unescaping arbitrary HTML. Catalogue stock filtering, canonical/noindex and selected-package calculation were verified on the live site. Remaining live checkout/debug checks are recorded separately after completion.

Google's validation endpoint returned zero messages for the deployed synthetic payload. Production pack prices remained 49.32/178.56 EUR. Successful add-to-cart yielded one unit-price event (69.43 EUR for the selected MM 01 package) and disappeared after redirect consumption; desktop and mobile checkout retained the 2 December dispatch estimate. Mobile calculator and sticky price were checked at 390 px. A narrow thumbnail-column delivery note is corrected in the same follow-up.
