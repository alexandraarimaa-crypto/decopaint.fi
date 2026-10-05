"""Product-specific material calculator data.

The public calculator must never fall back to a generic coverage value.  This
module only returns data when the product's own ``Attribute.sufficiency`` and
compatible active package sizes can be parsed safely.
"""

from __future__ import annotations

from html import unescape
import re


NUMBER = r"\d+(?:[.,]\d+)?"
RANGE = rf"(?P<first>{NUMBER})(?:\s*[-–—]\s*(?P<second>{NUMBER}))?"
UNIT = r"(?P<unit>kg|g|l|ml)"


def _plain_text(value):
    text = re.sub(r"<[^>]+>", " ", unescape(str(value or "")))
    return " ".join(text.replace("\xa0", " ").split())


def _number(value):
    return float(str(value).replace(",", "."))


def _normalise_amount(amount, unit):
    unit = unit.lower()
    if unit == "g":
        return amount / 1000, "kg"
    if unit == "ml":
        return amount / 1000, "l"
    return amount, unit


def parse_sufficiency(value):
    """Parse kg/L consumption or m² coverage into a conservative unit/m² rate."""

    raw = _plain_text(value)
    if not raw:
        return None

    normalised = (
        raw.lower()
        .replace("m²", "m2")
        .replace("m^2", "m2")
        .replace("ℓ", "l")
    )

    consumption = re.search(
        rf"{RANGE}\s*{UNIT}\s*(?:/|per)\s*m2\b",
        normalised,
        flags=re.I,
    )
    if consumption:
        first = _number(consumption.group("first"))
        second = _number(consumption.group("second") or consumption.group("first"))
        conservative, unit = _normalise_amount(max(first, second), consumption.group("unit"))
        minimum, _ = _normalise_amount(min(first, second), consumption.group("unit"))
        mode = "consumption"
    else:
        coverage = re.search(
            rf"{RANGE}\s*m2\s*(?:/|per)\s*{UNIT}\b",
            normalised,
            flags=re.I,
        )
        if coverage:
            first = _number(coverage.group("first"))
            second = _number(coverage.group("second") or coverage.group("first"))
            lowest_coverage = min(first, second)
            if lowest_coverage <= 0:
                return None
            unit_amount, unit = _normalise_amount(1, coverage.group("unit"))
            conservative = unit_amount / lowest_coverage
            minimum = unit_amount / max(first, second)
            mode = "coverage"
        else:
            inverse = re.search(
                rf"(?P<amount>{NUMBER})\s*{UNIT}\s*(?:/|per)\s*(?P<area>{NUMBER})\s*m2\b",
                normalised,
                flags=re.I,
            )
            if not inverse:
                return None
            amount, unit = _normalise_amount(
                _number(inverse.group("amount")), inverse.group("unit")
            )
            area = _number(inverse.group("area"))
            if area <= 0:
                return None
            conservative = minimum = amount / area
            mode = "consumption"

    # A rate explicitly described as the total for several coats must not be
    # multiplied once more.  ``/ kerros`` and equivalent wording are per-coat.
    total_for_coats = bool(re.search(
        r"(?:kahteen|kolmeen|\d+)\s+(?:kertaan|käsittelykertaa|kerrosta)|"
        r"(?:two|three|\d+)\s+(?:coats|layers)\s+(?:total|altogether)|"
        r"(?:två|tre|\d+)\s+(?:lager|strykningar)\s+totalt",
        normalised,
        flags=re.I,
    ))

    return {
        "raw": raw,
        "mode": mode,
        "unit": unit,
        "minimum_rate": round(minimum, 8),
        "conservative_rate": round(conservative, 8),
        "rate_includes_coats": total_for_coats,
    }


def detect_coats(*values):
    """Return an explicitly documented coat count, otherwise one."""

    text = _plain_text(" ".join(str(value or "") for value in values)).lower()
    counts = [int(value) for value in re.findall(
        r"\b([1-9])\s*(?:x\s*)?(?:kerrosta|käsittelykertaa|kertaan|coats?|layers?|"
        r"lager|strykningar)\b",
        text,
        flags=re.I,
    )]

    word_counts = (
        (3, r"\b(?:kolme|kolmeen|three|tre)\s+(?:kerrosta|kertaan|coats?|layers?|lager|strykningar)\b"),
        (2, r"\b(?:kaksi|kahteen|kahdella|two|två)\s+(?:kerrosta|kertaan|coats?|layers?|lager|strykningar)\b"),
        (1, r"\b(?:yksi|yhteen|one|ett)\s+(?:kerros|kertaan|coat|layer|lager|strykning)\b"),
    )
    for count, pattern in word_counts:
        if re.search(pattern, text, flags=re.I):
            counts.append(count)
    if counts:
        return max(counts), True
    return 1, False


def parse_packages(labels, required_unit):
    """Return unique active package sizes compatible with kg or L output."""

    packages = {}
    for original in labels or ():
        label = _plain_text(original)
        match = re.search(rf"(?P<amount>{NUMBER})\s*(?P<unit>kg|g|l|ml)\b", label, flags=re.I)
        if not match:
            continue
        amount, unit = _normalise_amount(_number(match.group("amount")), match.group("unit"))
        if (required_unit and unit != required_unit) or amount <= 0:
            continue
        key = round(amount, 6)
        packages[key] = {"amount": key, "label": label, "unit": unit}
    return [packages[key] for key in sorted(packages)]


def parse_density(value):
    """Return a kg/L density range when the product provides one."""

    raw = _plain_text(value).lower().replace("ℓ", "l").replace("³", "3")
    match = re.search(rf"{RANGE}\s*kg\s*/\s*(?P<volume>l|dm3|m3)\b", raw, flags=re.I)
    if match:
        values = [
            _number(match.group("first")),
            _number(match.group("second") or match.group("first")),
        ]
        if match.group("volume").lower() == "m3":
            values = [value / 1000 for value in values]
        return {"minimum": min(values), "maximum": max(values), "raw": _plain_text(value)}

    match = re.search(rf"{RANGE}\s*g\s*/\s*ml\b", raw, flags=re.I)
    if match:
        values = [
            _number(match.group("first")),
            _number(match.group("second") or match.group("first")),
        ]
        return {"minimum": min(values), "maximum": max(values), "raw": _plain_text(value)}
    return None


def build_material_calculator(
    sufficiency, package_labels, *technical_values, density=None
):
    parsed = parse_sufficiency(sufficiency)
    if not parsed:
        return None

    packages = parse_packages(package_labels, parsed["unit"])
    output_unit = parsed["unit"]
    unit_conversion = 1
    parsed_density = None
    if not packages:
        all_packages = parse_packages(package_labels, None)
        available_units = {item["unit"] for item in all_packages}
        parsed_density = parse_density(density)
        if not parsed_density or len(available_units) != 1:
            return None
        output_unit = available_units.pop()
        if parsed["unit"] == "l" and output_unit == "kg":
            unit_conversion = parsed_density["maximum"]
        elif parsed["unit"] == "kg" and output_unit == "l":
            unit_conversion = 1 / parsed_density["minimum"]
        else:
            return None
        packages = parse_packages(package_labels, output_unit)
        if not packages:
            return None

    coats, coats_explicit = detect_coats(sufficiency, *technical_values)
    multiplier = 1 if parsed["rate_includes_coats"] else coats
    return {
        **parsed,
        "source_unit": parsed["unit"],
        "unit": output_unit,
        "density": parsed_density,
        "coats": coats,
        "coats_explicit": coats_explicit,
        "calculation_rate": round(
            parsed["conservative_rate"] * multiplier * unit_conversion, 8
        ),
        "packages": packages,
    }
