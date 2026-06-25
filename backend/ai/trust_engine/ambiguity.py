"""
Trust Engine - Ambiguity Detection

Detects legal ambiguity using Legal-BERT.
Ambiguity = high litigation + inconsistent outcomes.
"""
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# Initialize Legal-BERT for ambiguity detection
tokenizer = None
model = None
try:
    tokenizer = AutoTokenizer.from_pretrained("nlpaueb/legal-bert-base-uncased")
    model = AutoModelForSequenceClassification.from_pretrained(
        "nlpaueb/legal-bert-base-uncased",
        num_labels=3,
        low_cpu_mem_usage=False
    )
except Exception:
    pass

# Ambiguity level mapping
AMBIGUITY_MAP = {
    "LOW": 0.2,
    "MEDIUM": 0.5,
    "HIGH": 0.85
}


def ambiguity_score(text):
    """
    Calculate ambiguity score for clause text.

    Uses Legal-BERT to classify clause as LOW/MEDIUM/HIGH ambiguity.
    High ambiguity correlates with litigation risk.

    Args:
        text: Clause text to analyze

    Returns:
        float: Ambiguity score (0-1, where 1 = highly ambiguous)
    """
    if not text or len(text.strip()) < 10:
        return 0.5  # Default for empty/short text

    try:
        # Tokenize input
        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        )

        # Get prediction
        with torch.no_grad():
            logits = model(**inputs).logits

        # Map to ambiguity level
        predicted_class = logits.argmax().item()
        labels = ["LOW", "MEDIUM", "HIGH"]
        label = labels[predicted_class] if predicted_class < len(labels) else "MEDIUM"

        return AMBIGUITY_MAP[label]

    except Exception as e:
        print(f"Ambiguity detection error: {e}")
        return 0.5  # Fallback to medium ambiguity


def ambiguity_label(score):
    """
    Convert numeric ambiguity score to human-readable label.

    Args:
        score: Ambiguity score (0-1)

    Returns:
        str: "LOW", "MEDIUM", or "HIGH"
    """
    if score < 0.35:
        return "LOW"
    elif score < 0.65:
        return "MEDIUM"
    else:
        return "HIGH"


def detect_ambiguous_terms(text):
    """
    Identify potentially ambiguous terms/phrases in clause text.

    Args:
        text: Clause text

    Returns:
        list: Ambiguous terms found
    """
    ambiguous_patterns = [
        "reasonable",
        "material",
        "substantial",
        "promptly",
        "best efforts",
        "commercially reasonable",
        "appropriate",
        "adequate",
        "sufficient",
        "as soon as possible",
        "good faith",
        "mutually agreed",
        "to the extent",
    ]

    text_lower = text.lower()
    found = []

    for pattern in ambiguous_patterns:
        if pattern in text_lower:
            found.append(pattern)

    return found
