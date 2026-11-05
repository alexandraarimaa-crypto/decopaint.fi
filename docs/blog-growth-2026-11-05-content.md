# Fiberglass wallpaper guide — content candidate, 5 November 2026

Issue #19. Improve the existing guide, preserving its URL, category, publication
date, linked products, existing instructions, image credits and translations.

## Content change

- FI/SV/EN titles describe the guide, materials and cost without promising a
  finished wall for the price of a coating pack.
- Add a short jump link, a 10 m² Marmorino Naturale Fine worked calculation,
  pack-cost comparison, direct product-calculator link, a project-enquiry
  checklist and links to the finish comparison and quantity guide.
- Label the calculation as an example, not a completed customer project.
  Keep the original credited images. Genuine project photos remain an input
  for a later content update; none were invented.

## Sources and arithmetic

Public Marmorino Naturale Fine technical data and the linked manufacturer
mn/10/en sheet specify 1–1.5 kg/m² TOTAL for two coats. At the upper value,
10 m² needs 15 kg; adding the example's optional 10% reserve gives 16.5 kg.
Do not multiply by the coat count again.

Public white-product prices checked 5 November 2026: 5 kg EUR 49.32 and
20 kg EUR 178.56. Three 5 kg packs cost EUR 147.96; one 20 kg pack EUR 178.56;
four 5 kg packs EUR 197.28. The latter two options each cover the reserve.
Prices are a dated snapshot; the live product page remains the current source.
Repairs, levelling compound, primer, tools, protection, delivery and labour are
excluded. Substrate and system compatibility must be assessed separately.

## Controlled content and release

Candidates are in content/blog/lasikuitutapetin-tasoitus/. publication.json
identifies exactly one article and the unchanged slug/category/product links.
All three original sources were exported locally and matched to the admin form
before editing; Finnish default and translation were identical. Backups remain
in the task workspace and must be preserved for a scoped content rollback.

Review localized content and a local noindex preview, validate links, image
references and arithmetic, and pass CI/review before the bounded CMS update.
Do not overwrite a concurrent edit: compare the live source with the verified
baseline immediately before saving. Save only this article's title/content
fields, then reopen the form and public pages to verify the result and unchanged
associations. No image replacement, product edit, pricing update, order,
customer, Merchant or analytics-setting operation is included.

Status: candidate only until a separately recorded publication verification.
The code/template release in the earlier dated plan remains separate.

## Candidate verification

The rebased isolated regression suite passed 106 tests on 5 November 2026.
SEO, mobile UI and search static validators passed. All three candidates retain
the five original image references and every original link. Static HTML checks
found no scripts, event handlers, forms or duplicate IDs. Decimal arithmetic
verified the three pack totals and the optional 16.5 kg reserve calculation.
The full Finnish noindex preview was reviewed at desktop and 390 px width;
the page did not overflow horizontally. This is local content-preview evidence,
not evidence that the separate template release reached hosted staging.
