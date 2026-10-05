# Deco Paint Finland

Private source repository for `decopaint.fi`.

This repository consolidates the sanitized Django source, source-controlled
static assets, release documentation, selected CMS content, and the mobile UI
prototype recovered from the project history through 20 August 2026.

## Repository contents

- Django storefront, checkout, Paytrail, Merchant, analytics, and SEO code.
- Source-grounded product search and its tests.
- Source CSS/JavaScript used by the production templates.
- Release, security, deployment, rollback, and audit documentation in `docs/`.
- Versioned article and social content in `content/`.
- The mobile concept in `prototypes/mobile/`.

## Deliberately excluded

Production secrets, `config/settings.py` values, service-account JSON, customer
and order data, databases, media uploads, logs, backups, deployment archives,
and generated caches must never be committed. Production data and media remain
covered by the hosting backup process; Git is the source of truth for code and
versioned content, not a database backup.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
set -a && source .env && set +a
python manage.py migrate
python manage.py runserver
```

For the isolated regression suite:

```bash
python manage.py test \
  users.tests pk_paytrail.tests google_shopping.tests \
  shop.tests_analytics shop.tests_search_engine shop.tests_search_view \
  shop.tests_seo config.tests_legacy_urls \
  --settings=config.test_settings
```

## Delivery policy

All changes go through a branch and pull request. Production deployment is a
separate, explicitly approved step after closed-staging validation, backup, and
rollback preparation. See `docs/github-workflow.md` and `AGENTS.md`.
