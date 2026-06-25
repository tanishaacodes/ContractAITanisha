"""
Dimension Normalization and Calibration
Gartner-style 0-100 scaling for consistent quadrants
"""
import re


def parse_contract_value(raw) -> float:
    """
    Parse a freeform currency string into a plain float.

    Handles:
      "$10"                  → 10.0
      "AED 2,500,000.00"    → 2500000.0
      "50 Crore"             → 500000000.0   (1 Crore = 10^7)
      "₹1,00,000"            → 100000.0
      "Rs 25 Lakh"           → 2500000.0     (1 Lakh = 10^5)
      "€3.2 Million"         → 3200000.0
      "1.5 Billion"          → 1500000000.0
      None / empty / garbage → 0.0
    """
    if raw is None:
        return 0.0

    text = str(raw).strip()
    if not text:
        return 0.0

    # Strip known currency prefixes / symbols (case-insensitive)
    text = re.sub(r'(?i)^(AED|INR|USD|EUR|GBP|CHF|SGD|HKD|JPY|CNY|Rs\.?|₹|\$|€|£)\s*', '', text)

    # Remove commas (Indian and international grouping)
    text = text.replace(',', '')

    # Pull out the leading number (int or decimal)
    m = re.match(r'([\d]+\.?[\d]*)', text)
    if not m:
        return 0.0

    number = float(m.group(1))
    remainder = text[m.end():].strip().lower()

    # Apply Indian / international scale words
    SCALES = {
        'billion': 1e9,
        'million': 1e6,
        'lakh':    1e5,
        'crore':   1e7,
        'cr':      1e7,
        'lac':     1e5,
        'l':       1e5,
    }
    for word, multiplier in SCALES.items():
        if remainder.startswith(word):
            number *= multiplier
            break

    return number


def normalize(value, min_val, max_val):
    """
    Normalize a value to 0-100 scale

    Args:
        value: Value to normalize
        min_val: Minimum value in dataset
        max_val: Maximum value in dataset

    Returns:
        Normalized value between 0 and 100
    """
    if max_val == min_val:
        return 50  # Return midpoint if no variation

    normalized = ((value - min_val) / (max_val - min_val)) * 100
    return round(normalized, 2)

def get_risk_level(score):
    """
    Convert numeric risk score to categorical level

    Args:
        score: Risk score (0-100)

    Returns:
        String representing risk level
    """
    if score >= 75:
        return "Very High"
    elif score >= 50:
        return "High"
    elif score >= 25:
        return "Low"
    else:
        return "Very Low"

def normalize_dataset(data: list, field: str):
    """
    Normalize a specific field across a dataset

    Args:
        data: List of dictionaries containing the field
        field: Field name to normalize

    Returns:
        List with normalized values
    """
    if not data:
        return data

    values = [item.get(field, 0) for item in data]
    min_val = min(values)
    max_val = max(values)

    for item in data:
        original = item.get(field, 0)
        item[f'{field}_normalized'] = normalize(original, min_val, max_val)

    return data
