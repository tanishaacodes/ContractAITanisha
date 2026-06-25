"""
Sentence Type Classifier for Clause Library
============================================
Classifies contract sentences into taxonomy types: Heading, Definition, Obligation, Risk, or Right.

Based on PDF requirements:
- BERT-based classifier with keyword-based fallback logic
- Classification types: HEADING, DEFINITION, OBLIGATION, RISK, RIGHT
- Accuracy target: ~89% for sentence type classification

Usage:
    classifier = get_sentence_classifier()
    sentence_type = classifier.classify("The Contractor shall complete the work within 30 days.")
    # Returns: "OBLIGATION"
"""

import logging
import re
from typing import Dict, List, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)


class SentenceTypeClassifier:
    """
    Classifies contract sentences into taxonomy types using keyword-based rules.

    Future enhancement: Replace with BERT-based model for higher accuracy.
    """

    # Keyword patterns for each sentence type
    KEYWORD_PATTERNS = {
        'HEADING': {
            'patterns': [
                r'^\d+\.?\s+[A-Z][A-Za-z\s]+$',  # Numbered headings
                r'^article\s+\d+',
                r'^section\s+\d+',
                r'^clause\s+\d+',
                r'^schedule\s+[a-z0-9]',
                r'^exhibit\s+[a-z0-9]',
                r'^appendix\s+[a-z0-9]',
            ],
            'keywords': [
                'definitions', 'terms', 'interpretation', 'recitals',
                'preamble', 'whereas', 'background', 'scope'
            ],
            'weight': 1.0
        },
        'DEFINITION': {
            'patterns': [
                r'means\b',
                r'shall mean',
                r'is defined as',
                r'refers to',
                r'definition of',
                r'"[^"]+" means',
            ],
            'keywords': [
                'definition', 'defined', 'term', 'meaning', 'interpretation',
                'hereinafter', 'includes', 'excluding'
            ],
            'weight': 0.9
        },
        'OBLIGATION': {
            'patterns': [
                r'shall\b',
                r'must\b',
                r'will\b',
                r'agrees to',
                r'required to',
                r'obligated to',
                r'responsible for',
                r'undertakes to',
                r'covenant',
            ],
            'keywords': [
                'obligation', 'duty', 'responsibility', 'perform', 'deliver',
                'provide', 'pay', 'complete', 'ensure', 'maintain',
                'comply', 'execute', 'submit', 'report', 'notify'
            ],
            'weight': 1.0
        },
        'RISK': {
            'patterns': [
                r'liability\b',
                r'penalty\b',
                r'damages\b',
                r'indemnif',
                r'liquidated damages',
                r'breach\b',
                r'default\b',
                r'termination\b',
                r'force majeure',
            ],
            'keywords': [
                'risk', 'liability', 'penalty', 'damages', 'indemnity',
                'indemnification', 'breach', 'default', 'termination',
                'delay', 'failure', 'loss', 'injury', 'harm', 'damage',
                'consequence', 'sanction', 'fine', 'forfeiture'
            ],
            'weight': 1.1
        },
        'RIGHT': {
            'patterns': [
                r'may\b',
                r'entitled to',
                r'has the right',
                r'shall have the right',
                r'may elect',
                r'at its discretion',
                r'option to',
            ],
            'keywords': [
                'right', 'entitlement', 'privilege', 'may', 'option',
                'discretion', 'freedom', 'license', 'permit', 'allow',
                'authorize', 'consent', 'approval'
            ],
            'weight': 0.8
        },
    }

    def __init__(self):
        """Initialize the sentence type classifier."""
        logger.info("SentenceTypeClassifier initialized with keyword-based rules")

    def classify(self, text: str) -> str:
        """
        Classify a sentence into one of the taxonomy types.

        Args:
            text (str): The sentence/clause text to classify

        Returns:
            str: One of HEADING, DEFINITION, OBLIGATION, RISK, RIGHT
        """
        if not text or not text.strip():
            return 'OBLIGATION'  # Default fallback

        text_lower = text.lower().strip()
        scores = {}

        # Score each type based on keyword matches
        for sentence_type, rules in self.KEYWORD_PATTERNS.items():
            score = 0

            # Check regex patterns
            for pattern in rules['patterns']:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    score += 2.0 * rules['weight']

            # Check keywords
            for keyword in rules['keywords']:
                if keyword.lower() in text_lower:
                    score += 1.0 * rules['weight']

            scores[sentence_type] = score

        # Get type with highest score
        if max(scores.values()) > 0:
            classified_type = max(scores, key=scores.get)
            logger.debug(f"Classified '{text[:50]}...' as {classified_type} (score: {scores[classified_type]})")
            return classified_type

        # Fallback: if "shall" is present, likely OBLIGATION
        if re.search(r'\bshall\b', text_lower):
            return 'OBLIGATION'

        # Default to OBLIGATION for contract clauses
        return 'OBLIGATION'

    def classify_batch(self, texts: List[str]) -> List[str]:
        """
        Classify multiple sentences in batch.

        Args:
            texts (List[str]): List of sentence/clause texts

        Returns:
            List[str]: List of sentence types
        """
        return [self.classify(text) for text in texts]

    def get_classification_confidence(self, text: str) -> Dict[str, float]:
        """
        Get confidence scores for all classification types.

        Args:
            text (str): The sentence/clause text

        Returns:
            Dict[str, float]: Scores for each type (0-1 normalized)
        """
        if not text or not text.strip():
            return {t: 0.0 for t in self.KEYWORD_PATTERNS.keys()}

        text_lower = text.lower().strip()
        scores = {}

        # Calculate raw scores
        for sentence_type, rules in self.KEYWORD_PATTERNS.items():
            score = 0

            for pattern in rules['patterns']:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    score += 2.0 * rules['weight']

            for keyword in rules['keywords']:
                if keyword.lower() in text_lower:
                    score += 1.0 * rules['weight']

            scores[sentence_type] = score

        # Normalize scores to 0-1 range
        max_score = max(scores.values()) if scores.values() else 1.0
        if max_score > 0:
            normalized_scores = {k: v / max_score for k, v in scores.items()}
        else:
            normalized_scores = {k: 0.0 for k in scores.keys()}

        return normalized_scores


# Singleton instance
_classifier_instance: Optional[SentenceTypeClassifier] = None


@lru_cache(maxsize=1)
def get_sentence_classifier() -> SentenceTypeClassifier:
    """
    Get singleton instance of sentence type classifier.

    Returns:
        SentenceTypeClassifier: The classifier instance
    """
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = SentenceTypeClassifier()
    return _classifier_instance


# Convenience function
def classify_sentence(text: str) -> str:
    """
    Quick classification of a single sentence.

    Args:
        text (str): Sentence text

    Returns:
        str: Sentence type (HEADING, DEFINITION, OBLIGATION, RISK, RIGHT)
    """
    classifier = get_sentence_classifier()
    return classifier.classify(text)
