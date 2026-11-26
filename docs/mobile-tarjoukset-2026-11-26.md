# Mobile offers link — 26 November 2026

Issue #26 addresses the owner screenshot: the root mobile menu has eight numbered entries and omits Tarjoukset. The offers category exists and is reachable via a deeper catalogue panel and desktop navigation. Add one native anchor after Tuotteet with the same nav-link classes and the existing product_list_by_category URL reverse, category_slug=tarjoukset. Reuse the current highlighting, scrolling and drawer behavior. Renumber following entries; add no new script, stylesheet, database record or integration call.

The only runtime file is shop/templates/shop/base/modal.html. Read the current production file/hash before release; preserve any drift rather than overwriting it. Prepare a private verified single-file backup and exact-commit closed-staging review before separate production approval. Rollback restores that one template with a later-edit guard.
