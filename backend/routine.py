"""Skincare routine recommendation engine (rule-based, no ML)."""

from __future__ import annotations

ROUTINE_RULES = {
    "acne": {
        "Clear": [],
        "Mild": [
            {"step": "Cleanse", "ingredient": "Salicylic acid 2% cleanser", "time": "PM", "note": "Unclogs pores, reduces inflammation"},
            {"step": "Treat", "ingredient": "Niacinamide 5% serum", "time": "AM", "note": "Regulates sebum, calms redness"},
        ],
        "Moderate": [
            {"step": "Cleanse", "ingredient": "Salicylic acid 2% cleanser", "time": "PM"},
            {"step": "Treat", "ingredient": "Benzoyl peroxide 2.5% spot treatment", "time": "PM", "note": "Antibacterial, start 2–3×/week"},
            {"step": "Hydrate", "ingredient": "Oil-free moisturizer", "time": "AM/PM", "note": "Prevents barrier damage"},
        ],
        "Severe": [
            {"step": "Cleanse", "ingredient": "Gentle non-foaming cleanser", "time": "AM/PM"},
            {"step": "Treat", "ingredient": "Clindamycin / prescription retinoid", "time": "PM", "note": "Requires dermatologist"},
            {"step": "Protect", "ingredient": "Non-comedogenic SPF 50+", "time": "AM", "note": "Prevents post-inflammatory hyperpigmentation"},
        ],
    },
    "redness": {
        "Clear": [],
        "Mild": [
            {"step": "Calm", "ingredient": "Centella asiatica (cica) serum", "time": "AM/PM", "note": "Anti-inflammatory, barrier repair"},
            {"step": "Hydrate", "ingredient": "Ceramide moisturizer", "time": "AM/PM", "note": "Restores lipid barrier"},
        ],
        "Moderate": [
            {"step": "Cleanse", "ingredient": "Fragrance-free gentle cleanser", "time": "AM/PM"},
            {"step": "Treat", "ingredient": "Azelaic acid 10% cream", "time": "PM", "note": "Reduces erythema, anti-inflammatory"},
            {"step": "Protect", "ingredient": "Mineral SPF 50+ (zinc oxide)", "time": "AM", "note": "Less irritating than chemical filters"},
        ],
        "Severe": [
            {"step": "Cleanse", "ingredient": "Ultra-gentle milk cleanser", "time": "AM/PM"},
            {"step": "Treat", "ingredient": "Prescription topical (dermatologist)", "time": "PM", "note": "May need oral medication"},
            {"step": "Repair", "ingredient": "Barrier balm (petrolatum-based)", "time": "PM", "note": "Occlusive overnight repair"},
        ],
    },
    "blemish": {
        "Clear": [],
        "Mild": [
            {"step": "Brighten", "ingredient": "Vitamin C 10% serum", "time": "AM", "note": "Antioxidant, fades marks"},
            {"step": "Exfoliate", "ingredient": "Glycolic acid 5% toner", "time": "PM", "note": "2–3×/week, promotes turnover"},
        ],
        "Moderate": [
            {"step": "Brighten", "ingredient": "Vitamin C 15% serum", "time": "AM"},
            {"step": "Treat", "ingredient": "Azelaic acid 15% gel", "time": "PM", "note": "Targets PIH, anti-inflammatory"},
            {"step": "Protect", "ingredient": "SPF 50+ (mandatory)", "time": "AM", "note": "UV darkens marks"},
        ],
        "Severe": [
            {"step": "Brighten", "ingredient": "Tranexamic acid 5% serum", "time": "AM/PM", "note": "Strong PIH inhibitor"},
            {"step": "Treat", "ingredient": "Retinoid (adapalene 0.1% / tretinoin)", "time": "PM", "note": "Gradual introduction, dermatologist guided"},
            {"step": "Protect", "ingredient": "Tinted mineral SPF 50+", "time": "AM", "note": "Iron oxides block visible light"},
        ],
    },
}

UNIVERSAL_RULES = {
    "am": [
        {"step": "Sunscreen", "ingredient": "Broad-spectrum SPF 50+", "note": "Reapply every 2 hours outdoors"},
    ],
    "pm": [
        {"step": "Cleanse", "ingredient": "Double cleanse if wearing SPF/makeup", "note": "Oil cleanser → water-based cleanser"},
    ],
    "avoid": [
        "Physical scrubs (apricot, walnut)",
        "High-alcohol toners",
        "Fragrance / essential oils on active lesions",
        "Picking / squeezing",
    ],
    "lifestyle": [
        "Change pillowcase 2×/week",
        "Clean phone screen daily",
        "Hydrate 2–3L water/day",
        "Sleep 7–8 hours",
    ],
}


def _dedupe_steps(steps: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for s in steps:
        time_val = s.get("time", "")
        key = (s["step"], s["ingredient"], time_val)
        if key not in seen:
            seen.add(key)
            out.append(s)
    return out


def build_routine(concerns: dict) -> dict:
    """
    Build AM/PM routine from detected concerns.

    Args:
        concerns: {"acne": {"severity": "...", ...}, "redness": {...}, "blemishes": {...}}

    Returns:
        {"am": [...], "pm": [...], "avoid": [...], "lifestyle": [...], "sunscreen": "..."}
    """
    concern_map = {
        "acne": concerns.get("acne", {}).get("severity", "Clear"),
        "redness": concerns.get("redness", {}).get("severity", "Clear"),
        "blemish": concerns.get("blemishes", {}).get("severity", "Clear"),
    }

    am_steps = []
    pm_steps = []

    for concern, severity in concern_map.items():
        rules = ROUTINE_RULES.get(concern, {}).get(severity, [])
        for rule in rules:
            if rule["time"] in ("AM", "AM/PM"):
                am_steps.append({"step": rule["step"], "ingredient": rule["ingredient"], "note": rule.get("note", "")})
            if rule["time"] in ("PM", "AM/PM"):
                pm_steps.append({"step": rule["step"], "ingredient": rule["ingredient"], "note": rule.get("note", "")})

    am_steps = _dedupe_steps(am_steps)
    pm_steps = _dedupe_steps(pm_steps)

    # Add universal rules
    am_steps.extend(UNIVERSAL_RULES["am"])
    pm_steps.extend(UNIVERSAL_RULES["pm"])

    return {
        "am": am_steps,
        "pm": pm_steps,
        "avoid": UNIVERSAL_RULES["avoid"],
        "lifestyle": UNIVERSAL_RULES["lifestyle"],
        "sunscreen": "Broad-spectrum SPF 50+ daily — non-negotiable",
    }


if __name__ == "__main__":
    import json
    test_concerns = {
        "acne": {"severity": "Moderate", "area_pct": 2.1},
        "redness": {"severity": "Mild", "area_pct": 1.5},
        "blemishes": {"severity": "Clear", "area_pct": 0.0},
    }
    print(json.dumps(build_routine(test_concerns), indent=2))