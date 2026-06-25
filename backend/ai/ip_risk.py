"""
Intellectual Property Risk Scoring
Identifies IP-related risks in contracts
"""

# IP risk terms with scores
IP_TERMS = {
    "joint ownership": 80,
    "joint ip": 80,
    "background ip": 40,
    "foreground ip": 60,
    "perpetual license": 75,
    "royalty free": 65,
    "royalty-free": 65,
    "exclusive license": 90,
    "exclusive rights": 90,
    "work for hire": 70,
    "assignment of rights": 75,
    "transfer of ownership": 85,
    "unlimited use": 80,
    "worldwide license": 70,
    "sublicense": 60,
    "derivative works": 55,
    "patent indemnity": 70,
    "ip indemnification": 75,
    "trade secrets": 65,
    "proprietary information": 50,
}

def ip_risk(text: str):
    """
    Calculate IP risk score based on contract text

    Args:
        text: Contract full text

    Returns:
        Risk score (0-100) and list of detected IP terms
    """
    text_lower = text.lower()
    detected = []
    score = 0

    for term, risk_value in IP_TERMS.items():
        if term in text_lower:
            detected.append((term.title(), risk_value))
            score += risk_value

    # Cap at 100
    final_score = min(score, 100)

    return round(final_score, 2), detected
