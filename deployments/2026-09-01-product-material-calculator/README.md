# Product material calculator admin settings

Production release for `decopaint.fi`, deployed on 2026-09-01.

This folder contains every source file changed for product-level manual material
calculator settings. Paths below `shop/` match the Django application paths and
can be copied over the project root.

## Behavior

- Adds a manual calculator override to every product in Django admin.
- Adds editable minimum and maximum coverage plus the coverage unit.
- Adds the `Menekkilaskurin pakkaukset` inline for package sizes and variants.
- Adds quick-edit calculator columns and a filter to the product list.
- Preserves the existing automatic calculator when the manual override is off.
- Uses `db_constraint=False` for the new package relations because the existing
  production `shop_product` and `shop_variant` tables use MyISAM.
- Deduplicates seeded package sizes across color variants.

## Duca Di Venezia seed

Migration `shop.0061_product_material_calculator_settings` configures product
ID `1295` with:

- Manual override: enabled
- Coverage: `12-14 m2/l`
- Packages: `1 L` and `4 L`

## Changed files

- `shop/models.py`
- `shop/admin.py`
- `shop/views.py`
- `shop/material_calculator.py`
- `shop/tests_material_calculator.py`
- `shop/migrations/0061_product_material_calculator_settings.py`
- `shop/templates/shop/product/detail.html`
- `shop/static/assets/js/mobile-modern-20260820-calculator.js`

## Verification

The release passed:

```bash
python manage.py check
python manage.py test shop.tests_material_calculator
python manage.py migrate shop 0061
```

Five calculator tests pass. Live verification confirmed the editable fields in
`/admin/shop/product/1295/change/`, the package inline, the product-list quick
edit controls, and the public Duca calculator. At `20 m2`, the live calculator
returns `1.67 L` and recommends `2 x 1 L`.

The byte-verified production release archive has SHA-256:

```text
6e3959fe906230589e404c1bcbeba7028c75f8b6c5ff10c98c968d042a473494
```

## Backup and rollback

The pre-deployment code archive and full compressed MySQL dump are stored on
the production server in:

```text
/home/decpai/release-backups/menekkilaskuri-product-admin-20260901T121050/
```

Rollback requires restoring the previous source files, migrating `shop` back
to `0060`, restoring the public calculator JavaScript, and restarting Django.
Use the database dump if a full database restore is required.
