"""
Clause Intelligence
===================
Detects economic sensitivity of clauses based on keyword patterns.
"""


def _get_clause_text(clause):
    """
    Extract the best available text from a Clause object.
    The Clause model uses 'extracted_text', 'context_sentences', and 'clause_name'
    — NOT 'clause_text'.
    """
    parts = [
        getattr(clause, 'extracted_text', None) or '',
        getattr(clause, 'context_sentences', None) or '',
        getattr(clause, 'text_spans', None) or '',
        getattr(clause, 'clause_name', None) or '',
    ]
    return ' '.join(p for p in parts if p).lower()


PRICE_ADJUSTMENT_KEYWORDS = [
    "price adjustment", "indexation", "cost escalation",
    "benchmark linked", "floating rate", "price escalation",
    "material cost", "commodity linked", "inflation indexed",
    "variable price", "market rate",
]

FINANCING_KEYWORDS = [
    "interest rate", "floating interest", "libor", "sofr",
    "benchmark rate", "base rate", "repo rate", "prime rate",
    "financing cost", "cost of funds",
]

FX_KEYWORDS = [
    "exchange rate", "foreign currency", "fx risk",
    "currency fluctuation", "usd/inr", "dollar rate",
    "rupee depreciation", "currency risk", "forex",
]

COMMODITY_KEYWORDS = [
    "steel price", "copper price", "aluminum", "crude oil",
    "raw material", "commodity price", "material cost",
    "fuel price", "energy cost",
]

TERMINATION_RISK_KEYWORDS = [
    "termination", "breach", "default", "penalty",
    "liquidated damages", "force majeure", "suspension",
]


def detect_clause_type(clause_text):
    """
    Classify a clause by its economic sensitivity type.

    Returns:
        str: one of price_adjustment | financing | fx | commodity | termination_risk | fixed
    """
    text = clause_text.lower()

    for k in PRICE_ADJUSTMENT_KEYWORDS:
        if k in text:
            return "price_adjustment"

    for k in FINANCING_KEYWORDS:
        if k in text:
            return "financing"

    for k in FX_KEYWORDS:
        if k in text:
            return "fx"

    for k in COMMODITY_KEYWORDS:
        if k in text:
            return "commodity"

    for k in TERMINATION_RISK_KEYWORDS:
        if k in text:
            return "termination_risk"

    return "fixed"


def has_price_adjustment_clause(clauses_qs):
    """
    Check if any clause in a queryset has a price adjustment mechanism.
    Args:
        clauses_qs: Django QuerySet of Clause objects
    Returns:
        bool
    """
    for clause in clauses_qs:
        text = _get_clause_text(clause)
        for k in PRICE_ADJUSTMENT_KEYWORDS:
            if k in text:
                return True
    return False


def get_clause_exposure_profile(clauses_qs):
    """
    Return a breakdown of clause types for a contract's clause set.
    Returns: dict with counts per type
    """
    profile = {
        "price_adjustment": 0,
        "financing": 0,
        "fx": 0,
        "commodity": 0,
        "termination_risk": 0,
        "fixed": 0,
    }
    for clause in clauses_qs:
        ctype = detect_clause_type(_get_clause_text(clause))
        profile[ctype] = profile.get(ctype, 0) + 1
    return profile
