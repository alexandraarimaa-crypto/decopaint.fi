# Menekkilaskuri production correction — 2026-08-20

## Problem

Every product page received the same mobile calculator configuration:
`data-coverage="9"`, `data-coats="2"`, and a litre-only formula.  It ignored
the product's own `Attribute.sufficiency`.  Marmorino Naturale Fine therefore
showed 5 L for 20 m² even though the storefront states
`0,5–0,75 kg/m²` and its instructions require two coats.

## Implemented contract

- Parse only a product's own area rate in kg/m², g/m², m²/kg, L/m², ml/m² or
  m²/L notation.
- Use the higher material-consumption edge of a range.
- Multiply by a coat count only when the product's own technical text states
  one; do not multiply a rate that explicitly states it already covers all
  coats.
- Recommend only active package sizes and never alter the selected package,
  cart quantity or order automatically.
- Prefer minimum excess material and then minimum package count.
- Convert between L and kg only with the product's explicit `Tiheys` value.
- Hide the calculator when the rate, package unit or required density cannot be
  resolved safely.  Do not guess from a universal fallback.

## Changed paths

- `shop/material_calculator.py` (new)
- `shop/views.py`
- `shop/templates/shop/product/detail.html`
- `shop/templates/shop/base/base.html`
- `shop/static/assets/js/mobile-modern-20260820-calculator.js` (new)
- `shop/tests_material_calculator.py` (new)

The cache-busted JavaScript was also copied to the runtime collected-static
root.  No schema migration or content write was made.

## Verification

- 7 calculation tests: `OK`.
- Python compilation and JavaScript syntax: `OK`.
- Source-data audit: 154 products, 119 with non-empty `Riittoisuus`, zero read
  errors, 73 distinct source formats.
- The parser intentionally rejects `90g/l`, `10-20%/l`, `1/20l` and malformed
  `10-12m/kg`, because these are not safe area-consumption formulas.
- Render audit: all 154 live product pages; 113 safe product-specific
  calculators, zero legacy hard-coded values, zero invalid rendered
  configurations and zero HTTP errors.  Remaining products do not render a
  calculator because they are tools or lack a safely compatible rate/unit.
- Marmorino Naturale Fine, 20 m²: 30 kg; recommendation 1 × 20 kg + 2 × 5 kg.
- Marmorino Naturale Fine, 35 m²: 52.5 kg; recommendation totals 53 kg.
- 210 Biofondo Coprente: litre result from 14–18 m²/L.
- Marmora Romana: m²/L converted to kg packages using 1.7 kg/L density.
- Efektiharja: no calculator because it is a tool without material consumption.

## Rollback evidence

Exact server copies exist with suffix `.bak-20260820-before-calculator` for all
four replaced source/template/legacy asset paths.  The new helper and
cache-busted asset were absent before this release and can be removed safely.

No prices, discounts, variants, colours, inventory, carts, orders, customers,
payment callbacks, Merchant Center or Analytics settings were changed.

## Desktop extension

The same calculator was exposed on desktop product pages without changing its
formula or data contract.  Only the product template changed: the desktop hide
class was removed and styles scoped to `@media (min-width: 768px)` were added.

Live verification at 1280 px:

- Marmorino Naturale Fine, 20 m²: 30 kg; 1 × 20 kg + 2 × 5 kg.
- Marmorino Naturale Fine, 35 m²: 52.5 kg; packages total 53 kg.
- The calculator remained interactive and reported kg for kg packages.

Production rollback copy:
`/home/decpai/public_html/deco/shop/templates/shop/product/detail.html.bak-20260820-before-desktop-calculator`.
