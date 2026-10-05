# Google Customer Reviews language correction — 2026-08-20

## Problem

A Finnish order confirmation displayed the Google opt-in dialog in Swedish
because the Google platform script selected the browser/Google-account locale.

## Change

The order confirmation now sets `window.___gcfg.lang` from Django's active
language before loading Google's platform script. No GCR transaction field or
order-processing logic changed.

## Survey timing

Google, not Deco Paint, sends the survey email a few days after the supplied
estimated delivery date. Order 2260 was placed on 2026-08-20; the standard
four-day estimate is 2026-08-24, so an immediate survey email is not expected.
Merchant Center reporting can lag by up to one week.

## Verification and rollback

- Candidate template compiled.
- Locale expression produced `fi`, `sv`, and `en`.
- Production readback matched the candidate and public smoke checks passed.
- Exact rollback path is documented in `docs/rollback.md`.
