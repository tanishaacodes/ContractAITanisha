"""
Geography Risk Scoring
Identifies risky geographical locations in contracts
"""

# High-risk geographies with risk scores (0-1 scale)
RISKY_GEOS = {
    "congo": 0.9,
    "democratic republic of congo": 0.9,
    "iraq": 0.85,
    "afghanistan": 0.95,
    "syria": 0.98,
    "libya": 0.8,
    "yemen": 0.9,
    "somalia": 0.85,
    "sudan": 0.75,
    "south sudan": 0.8,
    "venezuela": 0.7,
    "myanmar": 0.75,
    "burma": 0.75,
    "north korea": 0.95,
    "iran": 0.8,
    "lebanon": 0.65,
    "palestine": 0.7,
    "crimea": 0.8,
}

# Medium-risk geographies
MEDIUM_RISK_GEOS = {
    "russia": 0.6,
    "china": 0.4,
    "pakistan": 0.55,
    "nigeria": 0.5,
    "ethiopia": 0.45,
    "egypt": 0.4,
    "turkey": 0.45,
    "brazil": 0.35,
    "mexico": 0.4,
    "argentina": 0.35,
}

def geography_risk(text: str):
    """
    Calculate geography risk score based on contract text

    Args:
        text: Contract full text

    Returns:
        Risk score (0-100) and list of detected locations
    """
    text_lower = text.lower()
    detected = []
    max_score = 0

    # Check high-risk locations
    for geo, score in RISKY_GEOS.items():
        if geo in text_lower:
            detected.append((geo.title(), score * 100))
            max_score = max(max_score, score * 100)

    # Check medium-risk locations
    for geo, score in MEDIUM_RISK_GEOS.items():
        if geo in text_lower:
            detected.append((geo.title(), score * 100))
            max_score = max(max_score, score * 100)

    # Return highest risk if any found, else default low risk
    if not detected:
        return 10, []

    return round(max_score, 2), detected
