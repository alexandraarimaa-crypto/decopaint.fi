# Manual material information by package — 27 October 2026

Task #10 corrects the existing manual fields released in #7–#9.

Tuotteet → product → Pakkauskohtaiset lisätiedot contains one pair of inputs
per existing non-empty package size. Colour, base, grain and gloss do not own
separate copies. Package size is displayed but cannot be changed here; existing
variant/package selection remains the source of sizes. The colour change form
no longer contains either manual input.

The existing API keys, Finnish labels, optional visibility and text rendering
remain. A product/size-only lookup reads common values after the unchanged
variant/price resolver succeeds. Colour/quantity requests retain those labels
while loading. A package change clears old labels and updates through the
existing request queue. No navigation or automatic calculation is added.
The versioned script URL avoids loading the previous seven-day cached script.

## Small storage adjustment and transfer

Variant currently combines size and colour. One small PackageMaterialInfo
relation, unique by product + exact existing size, reuses the same nullable
decimal/text fields and form behavior. Values are not stored on an arbitrary
colour row or copied to every colour, and survive deletion of one colour.
No existing variant/product/package/price/stock/tinting data is changed.

0062 creates the relation. The product FK uses db_constraint=False because
the production product table is MyISAM; Django retains ORM cascade behavior.
There is no engine conversion or ALTER of the existing variant table.
0063 copies each field only if exactly one distinct non-empty legacy value
exists for that product/size. Blank fields do not contradict a single entered
value. Conflicting fields remain empty; unambiguous fields can transfer.
Every original Variant value and column remains, including conflicts and
rows without a usable size. No arbitrary colour/value is selected.

Historical conflicting alternatives appear read-only beside the common inputs
in Tuotteet. The administrator explicitly enters the chosen common values and
saves. This does not delete or overwrite colour values. Clearing a common
field hides it; the storefront never falls back to legacy values. Retrying the
transfer does not overwrite later shared admin values.

New imported sizes appear as unsaved initial forms. GET never creates rows.
Disabled size inputs are initialized from actual product sizes; posted size
tampering is ignored. Colour-only rows without sizes receive no inputs.
Product edit permission controls this metadata without granting price/order
access or new staff roles.

## Read-only production audit

354331 variants, 313 product/package groups, one populated manual variant,
no conflicting groups and no populated rows without a package. The existing
value can transfer unambiguously. Source hashes match deployed 7e7b662.
Original values/hashes are retained privately outside webroot. The audit did
not change production product data or schema.

## Checks and release gates

Test single/multiple colours for single/multiple litre/kilogram packages;
empty/zero/clear behavior; same-size colour/quantity retention; new sizes
without GET writes; disabled size tampering; hidden colour inputs; permissions;
real admin-interface tabs; preserved migration values/conflicts; and deletion
of one colour. Runtime AST checks retain existing pricing/resolver functions
apart from the two metadata values. Existing regression/calculator suites
remain required.

Deploy the reviewed scoped builder, whose expected hashes refer to 7e7b662.
Keep production settings and unchanged translation/schema support. Complete
CI, closed synthetic staging, desktop/mobile review and private verified backup
before requesting separate owner approval under AGENTS.md. Apply only 0062/0063
before enabling code that queries the shared table. Publish the one updated
script to the actual served static directory and verify the versioned public
URL status, MIME type and hash before enabling the product template.
This implementation alone does not authorize production installation.

Rollback restores preceding application/template/static files while retaining
the shared table and legacy columns. Old values remain available to old code,
and new shared values remain preserved for reapplication. Do not reverse 0062
or restore a full database over newer orders. Export/backup both sets of values
before any future destructive cleanup.
