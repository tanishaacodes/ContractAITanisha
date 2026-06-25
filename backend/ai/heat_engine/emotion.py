"""
Emotional Friction Detection

Uses Legal-BERT to detect aggressive/emotional language in negotiations.
"""
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# Initialize Legal-BERT for emotion detection
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

# Emotion/friction level mapping
EMOTION_MAP = {
    "LOW": 0.2,
    "MEDIUM": 0.5,
    "HIGH": 0.9
}


def emotion_score(text):
    """
    Calculate emotional friction score for negotiation text.

    Detects:
    - Aggressive tone
    - Absolutist language
    - Legal hard-stops
    - Defensive posturing

    Args:
        text: Negotiation message or redline text

    Returns:
        float: Friction score (0-1, where 1 = high friction)
    """
    if not text or len(text.strip()) < 10:
        return 0.3  # Neutral default

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

        # Map to friction level
        predicted_class = logits.argmax().item()
        labels = ["LOW", "MEDIUM", "HIGH"]
        label = labels[predicted_class] if predicted_class < len(labels) else "MEDIUM"

        return EMOTION_MAP[label]

    except Exception as e:
        print(f"Emotion detection error: {e}")
        return 0.5  # Fallback to medium friction


def emotion_label(score):
    """
    Convert numeric friction score to label.

    Args:
        score: Friction score (0-1)

    Returns:
        str: "LOW", "MEDIUM", or "HIGH"
    """
    if score < 0.35:
        return "LOW"
    elif score < 0.65:
        return "MEDIUM"
    else:
        return "HIGH"


def detect_friction_patterns(text):
    """
    Identify specific friction patterns in text.

    Args:
        text: Negotiation text

    Returns:
        list: Detected friction patterns
    """
    text_lower = text.lower()
    patterns = []

    # Aggressive patterns
    aggressive_terms = [
        "absolutely not",
        "non-negotiable",
        "must have",
        "deal breaker",
        "unacceptable",
        "refuse to",
        "cannot agree",
        "strongly object",
        "completely unacceptable"
    ]

    for term in aggressive_terms:
        if term in text_lower:
            patterns.append({
                "type": "AGGRESSIVE",
                "term": term,
                "severity": "HIGH"
            })

    # Defensive patterns
    defensive_terms = [
        "protect our interests",
        "need to ensure",
        "concerned about",
        "hesitant to",
        "uncomfortable with",
        "need clarification"
    ]

    for term in defensive_terms:
        if term in text_lower:
            patterns.append({
                "type": "DEFENSIVE",
                "term": term,
                "severity": "MEDIUM"
            })

    # Absolutist language
    absolutist_terms = [
        "never",
        "always",
        "all",
        "none",
        "every",
        "impossible",
        "under no circumstances"
    ]

    for term in absolutist_terms:
        if term in text_lower:
            patterns.append({
                "type": "ABSOLUTIST",
                "term": term,
                "severity": "MEDIUM"
            })

    return patterns


def emotional_trend(messages):
    """
    Analyze emotional trend across negotiation messages.

    Args:
        messages: List of negotiation messages (chronological)

    Returns:
        dict: Trend analysis
    """
    if not messages or len(messages) < 2:
        return {
            "trend": "STABLE",
            "escalating": False,
            "current_friction": 0.3
        }

    scores = [emotion_score(msg) for msg in messages]

    # Calculate trend
    recent_avg = sum(scores[-3:]) / min(len(scores[-3:]), 3)
    early_avg = sum(scores[:3]) / min(len(scores[:3]), 3)

    trend_diff = recent_avg - early_avg

    if trend_diff > 0.15:
        trend = "ESCALATING"
        escalating = True
    elif trend_diff < -0.15:
        trend = "DE-ESCALATING"
        escalating = False
    else:
        trend = "STABLE"
        escalating = False

    return {
        "trend": trend,
        "escalating": escalating,
        "current_friction": scores[-1] if scores else 0.3,
        "avg_friction": sum(scores) / len(scores),
        "peak_friction": max(scores),
        "friction_history": scores
    }
