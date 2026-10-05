#!/usr/bin/env python3
"""Static release checks for the code-only mobile UI candidate."""

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "base": ROOT / "shop/templates/shop/base/base.html",
    "header": ROOT / "shop/templates/shop/base/header.html",
    "modal": ROOT / "shop/templates/shop/base/modal.html",
    "home": ROOT / "shop/templates/shop/else/main.html",
    "popular": ROOT / "shop/templates/shop/else/main_popular.html",
    "catalog": ROOT / "shop/templates/shop/product/list.html",
    "product": ROOT / "shop/templates/shop/product/detail.html",
    "cart": ROOT / "cart/templates/cart/cart.html",
    "checkout": ROOT / "cart/templates/cart/checkout.html",
    "css": ROOT / "shop/static/assets/css/mobile-modern-20260801-equal-cards.css",
    "js": ROOT / "shop/static/assets/js/mobile-modern.js",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_all() -> dict[str, str]:
    for name, path in FILES.items():
        require(path.is_file(), f"Missing {name}: {path}")
    return {name: path.read_text(encoding="utf-8") for name, path in FILES.items()}


def check_template_pairs(text: str, name: str) -> None:
    pairs = {
        "if": "endif",
        "for": "endfor",
        "block": "endblock",
        "with": "endwith",
    }
    stack: list[tuple[str, int]] = []
    for match in re.finditer(r"{%\s*([a-zA-Z_]+)\b.*?%}", text, flags=re.S):
        tag = match.group(1)
        if tag in pairs:
            stack.append((tag, match.start()))
        elif tag in pairs.values():
            expected_open = next(key for key, value in pairs.items() if value == tag)
            require(bool(stack), f"{name}: unexpected {tag}")
            actual_open, position = stack.pop()
            require(
                actual_open == expected_open,
                f"{name}: {tag} closes {actual_open} opened at {position}",
            )
    require(not stack, f"{name}: unclosed template tags {stack}")


def check_css(text: str) -> None:
    without_comments = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    require(
        without_comments.count("{") == without_comments.count("}"),
        "CSS brace count differs",
    )
    for selector in (
        ".dp-mobile-header",
        ".dp-mobile-menu",
        ".dp-home-hero",
        ".dp-home-section-heading",
        ".dp-product-card",
        ".dp-mobile-sticky-buy",
        ".dp-checkout-steps",
        ":focus-visible",
        "prefers-reduced-motion",
    ):
        require(selector in text, f"CSS contract missing: {selector}")


def main() -> int:
    texts = read_all()
    for name in ("base", "header", "modal", "home", "popular", "catalog", "product", "cart", "checkout"):
        check_template_pairs(texts[name], name)

    check_css(texts["css"])
    require(
        "grid-template-columns: 44px minmax(0, 1fr)" in texts["css"],
        "Compact mobile benefits layout is missing",
    )
    require(
        "grid-template-columns: 54px minmax(0, 1fr)" in texts["css"],
        "Compact mobile values layout is missing",
    )
    require(
        texts["css"].count("hyphens: auto;") >= 3,
        "Finnish mobile card hyphenation protection is missing",
    )
    require(
        texts["css"].count("overflow-wrap: break-word;") >= 3,
        "Mobile card overflow protection is missing",
    )
    require(
        re.search(
            r"\.dp-home-benefits \.row > div\s*\{[^}]*display:\s*flex;",
            texts["css"],
            flags=re.S,
        ),
        "Mobile benefit wrappers must stretch their cards",
    )
    require(
        re.search(
            r"\.dp-home-benefits \.card\s*\{[^}]*height:\s*100%;",
            texts["css"],
            flags=re.S,
        ),
        "Mobile benefit cards must fill the grid-row height",
    )

    require(
        'name="viewport" content="width=device-width, initial-scale=1.0"' in texts["base"],
        "Accessible viewport is missing",
    )
    require(
        "mobile-modern-20260801-equal-cards.css" in texts["base"],
        "Versioned mobile CSS is not linked",
    )
    require("mobile-modern.js" in texts["base"], "Mobile JS is not linked")
    require("Vain välttämättömät" in texts["base"], "Essential-only consent action is missing")

    require("dp-mobile-discovery" in texts["home"], "Home discovery block is missing")
    require(
        'placeholder="Esim. patterimaali"' in texts["home"],
        "Home search placeholder must use the verified patterimaali query",
    )
    require(
        "kylpyhuoneen seinä" not in texts["home"],
        "Home search placeholder must not advertise a zero-result query",
    )
    require("MATERIAALILASKURI" in texts["home"], "Home calculator CTA is missing")
    require("ASIANTUNTIJA APUNA" in texts["home"], "Home consultation block is missing")
    require("Sujuvampi ostokokemus" in texts["home"], "Mobile benefits heading is missing")
    require("Laatuominaisuudet" in texts["home"], "Mobile values heading is missing")
    require(
        texts["home"].count("dp-mobile-card-caption") == 8,
        "Expected eight compact mobile card captions",
    )
    for original_icon in (
        "#icon-box-01",
        "#icon-box-02",
        "#icon-box-03",
        "#icon-box-04",
        "bollo-ecologia-bollo-since1984.svg",
        "antibacterial.png",
        "bollo-washability.svg",
        "bollo-HACCP.svg",
    ):
        require(original_icon in texts["home"], f"Original homepage icon missing: {original_icon}")
    require('fetchpriority="high"' in texts["home"], "Priority hero image is missing")

    require("dp-mobile-category-intro" in texts["catalog"], "Mobile category intro is missing")
    require("dp-mobile-catalog-toolbar" in texts["catalog"], "Catalog toolbar is missing")
    require("dp-card-cta" in texts["catalog"], "Product card CTA is missing")

    require('id="cart_form"' in texts["product"], "Product cart form contract changed")
    require('form="cart_form"' in texts["product"], "Sticky CTA is not connected to cart form")
    require('id="price-container"' in texts["product"], "Dynamic price contract changed")
    require("dp-material-calculator" in texts["product"], "Product calculator is missing")

    for contract in (
        'id="paymentForm"',
        'id="create-order"',
        'name="delivery_method"',
        'value="postnord_lokero"',
        'value="postnord_kotiinkuljetus"',
        'value="pickup"',
        'name="payment_method"',
        'value="online"',
        'value="cod"',
        "DecoPaintAnalytics",
    ):
        require(contract in texts["checkout"], f"Checkout contract changed: {contract}")

    require("fetch(" not in texts["js"], "Mobile JS must not add network writes")
    require("email" not in texts["js"].lower(), "Mobile JS must not process email/PII")
    require("localStorage" not in texts["js"], "Mobile JS must not add persistent tracking")

    print("MOBILE_UI_STATIC_CHECKS_OK=1")
    print(f"CHECKED_FILES={len(FILES)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as error:
        print(f"MOBILE_UI_STATIC_CHECKS_OK=0\nERROR={error}", file=sys.stderr)
        raise SystemExit(1)
