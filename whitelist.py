"""Canonical asset-class whitelist and fuzzy normalization."""
from __future__ import annotations

from rapidfuzz import fuzz, process, utils

WHITELIST: dict[str, list[str]] = {
    "PRE-TAX": [
        "401(k)",
        "401(k) Match",
        "IRA",
        "Rollover IRA",
        "Inherited IRA",
        "Simple IRA",
        "Pension",
        "403(b)",
        "457",
        "401(a)",
        "Profit Sharing",
    ],
    "BROKERAGE": [
        "Stock",
        "Stocks",
        "Brokerage",
        "Stock Grant",
        "Mutual Funds",
        "Options",
        "ESPP",
        "Crypto",
        "Hedge Funds",
        "REIT",
    ],
    "TAX DEFERRED": [
        "Variable Annuity",
        "Fixed Annuity",
        "After Tax 401(k)",
        "LTC/Life Hybrid",
    ],
    "TAX FREE": [
        "Roth IRA",
        "Roth 401(k)",
        "Roth 403(b)",
        "529",
        "Whole Life",
        "Whole Life B",
        "Variable Life",
        "Universal Life",
    ],
    "CASH": ["Checking", "Savings", "MMAs", "Cash", "CDs", "Income"],
    "PROPERTY": ["Home Equity", "Investment Property Equity"],
    "BUSINESS": ["Business Equity"],
    "PROTECTION": ["Term Insurance"],
}

ALL_CLASSES: list[str] = [cls for items in WHITELIST.values() for cls in items]

_CLASS_TO_CATEGORY: dict[str, str] = {
    cls: category for category, items in WHITELIST.items() for cls in items
}

FUZZY_THRESHOLD = 80


def CATEGORY_FOR(asset_class: str) -> str | None:
    """Return the top-level category for a canonical asset class, or None."""
    return _CLASS_TO_CATEGORY.get(asset_class)


def normalize(raw_string: str) -> tuple[str | None, int]:
    """Fuzzy-match a raw asset-class string to the whitelist.

    Returns (canonical_match, confidence) when confidence >= 80, else (None, 0).
    """
    if not raw_string or not raw_string.strip():
        return (None, 0)

    candidate = raw_string.strip()

    # Exact (case-insensitive) match wins outright.
    for cls in ALL_CLASSES:
        if cls.lower() == candidate.lower():
            return (cls, 100)

    # token_set_ratio handles word reordering and punctuation differences
    # like "401k" vs "401(k)" and "401 K" vs "401(k)".
    result = process.extractOne(
        candidate,
        ALL_CLASSES,
        scorer=fuzz.token_set_ratio,
        processor=utils.default_process,
        score_cutoff=FUZZY_THRESHOLD,
    )
    if result is None:
        return (None, 0)

    match, score, _ = result
    return (match, int(score))
