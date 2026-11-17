# Showroom relocation — 17 November 2026

Owner-approved facts: the Asessorinkatu 12 showroom is closed during the move;
the webshop continues operating. From 1 December 2026 visitors are welcomed at
Voivalantie 30, 20780 Kaarina, Mon–Fri 09:00–17:00 and Sat/Sun by appointment.
No unit/entrance letter has been supplied, so none is invented.

## Storefront

- FI/SV/EN notice in the shared base, below the navigation and above page content.
- Before 1 December: clearly label the future address and current showroom closure.
- From 1 December (Europe/Helsinki): automatically switch to the new open showroom.
- Contact/footer show the dated new address; contact hours use the confirmed hours.
- Remove the old map pin and link directions to the exact new street address.
- Pickup gets a descriptive note to arrange collection during the move, with the
  public business phone; delivery options, fees and checkout JavaScript stay intact.
- The temporary banner expires 1 January 2027; the new address remains permanent.

## Communications and approval

Google Business, social posts, newsletter text, email signature and printable door
notice use the same facts. Keep the old Google location temporarily closed until
the move; update the existing profile at opening rather than creating a duplicate.

Owner explicitly requires preview and approval before uploading any Canva-based
advertising creative to social/advertising channels. Use the original Deco Paint
logo without redrawing, recoloring or altering its proportions. No visual ad is
published or activated before that approval. Proposed paid test: 24 Nov–3 Dec,
Kaarina/Turku, within 50–80 EUR total; final setup must show a firm total cap.

## Deployment and rollback

Exact current runtime templates were exported privately on 17 November, archive
SHA256 84a7705861b5785511df2e33abe4ff9b8264e0986cb674466ef73c7f8fd8d48a.
Only the four needed templates and their hashes are versioned as baselines.
The old contact-map public token is replaced with a template placeholder before
versioning; that whole map is removed in the projected result. Separate audited
baseline and raw production hashes preserve both provenance and drift guards.
The seven-file builder refuses baseline drift. Reuse the audited guarded installer;
back up outside the webroot, verify all target hashes, restart existing Passenger.
No database step, migrations or static publication are required.

Run `python manage.py test shop.tests_showroom --settings=config.test_settings`.
Build with `python scripts/build_relocation_release.py --output PRIVATE_CANDIDATE`.
Dry-run/install with `scripts/install_sales_release.py` using that candidate,
production project and a fresh exclusive private backup directory. Use the same
arguments plus `--restore` for guarded rollback; refuse later edits.

Public smoke: homepage/product/contact/footer; FI/SV/EN; desktop and 390 px;
future/current labels, directions, opening hours, pickup description and unchanged
checkout behavior. Do not create a real order/payment or send test customer emails.

## Status

Implementation in progress. Do not treat a prepared asset or merged PR as proof
of deployment/publication. Record exact commit, private checks, backup and public
results in the PR and task completion receipt.
