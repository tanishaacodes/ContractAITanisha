"""
Party Attribution Classifier
Determines whether clauses favor Buyer, Supplier, or are Neutral
"""
from typing import Dict, List
from functools import lru_cache


class PartyAttributionClassifier:
    """Classifies contract clauses as buyer-favorable, supplier-favorable, or neutral."""

    BUYER_FAVORABLE_PATTERNS = {
        'termination': ['buyer may terminate', 'right to terminate', 'terminate for convenience'],
        'payment': ['payment upon delivery', 'withhold payment', 'payment milestone'],
        'liability': ['supplier shall indemnify', 'supplier liability', 'unlimited liability'],
        'quality': ['service level agreement', 'sla', 'acceptance testing'],
        'audit': ['right to audit', 'inspection rights']
    }

    SUPPLIER_FAVORABLE_PATTERNS = {
        'termination': ['supplier may terminate', 'lock-in period', 'minimum term'],
        'payment': ['payment in advance', 'prepayment', 'late payment fee'],
        'liability': ['limitation of liability', 'force majeure', 'no warranty', 'as is'],
        'ip': ['supplier owns', 'non-exclusive license', 'limited license']
    }

    NEUTRAL_PATTERNS = ['mutual', 'both parties', 'each party', 'reasonable', 'good faith']

    # Mapping from attribution result to RRIE party labels
    ATTRIBUTION_TO_PARTY = {
        'BUYER_FAVORABLE': 'EMPLOYER',
        'SUPPLIER_FAVORABLE': 'CONTRACTOR',
        'NEUTRAL': 'SHARED',
    }

    def __init__(self):
        self.classification_cache = {}

    def classify_clause(self, clause_text: str, clause_type: str = None) -> Dict:
        clause_lower = clause_text.lower()
        buyer_score = self._calculate_buyer_score(clause_lower)
        supplier_score = self._calculate_supplier_score(clause_lower)
        neutral_score = self._calculate_neutral_score(clause_lower)
        
        total = buyer_score + supplier_score + neutral_score
        if total == 0:
            return {'attribution': 'NEUTRAL', 'confidence': 0.3}
        
        buyer_norm = buyer_score / total
        supplier_norm = supplier_score / total
        
        if buyer_norm >= 0.4 and buyer_norm > supplier_norm:
            return {'attribution': 'BUYER_FAVORABLE', 'confidence': buyer_norm}
        elif supplier_norm >= 0.4 and supplier_norm > buyer_norm:
            return {'attribution': 'SUPPLIER_FAVORABLE', 'confidence': supplier_norm}
        return {'attribution': 'NEUTRAL', 'confidence': 0.5}

    def attribute_batch(self, clause_texts: List[str], sentence_types: List[str] = None) -> List[str]:
        """
        Attribute parties for a batch of clauses.
        Returns a list of party labels: CONTRACTOR, EMPLOYER, or SHARED.
        Compatible with rrie_views.py which expects these RRIE-style labels.
        """
        results = []
        for text in clause_texts:
            result = self.classify_clause(text)
            attribution = result.get('attribution', 'NEUTRAL')
            party_label = self.ATTRIBUTION_TO_PARTY.get(attribution, 'SHARED')
            results.append(party_label)
        return results

    def _calculate_buyer_score(self, text: str) -> float:
        return sum(2.0 for patterns in self.BUYER_FAVORABLE_PATTERNS.values() for p in patterns if p in text)

    def _calculate_supplier_score(self, text: str) -> float:
        return sum(2.0 for patterns in self.SUPPLIER_FAVORABLE_PATTERNS.values() for p in patterns if p in text)

    def _calculate_neutral_score(self, text: str) -> float:
        return sum(2.0 for p in self.NEUTRAL_PATTERNS if p in text)


_party_classifier = None

def get_party_classifier():
    global _party_classifier
    if _party_classifier is None:
        _party_classifier = PartyAttributionClassifier()
    return _party_classifier

# Alias for backward compatibility with existing code
def get_party_attributor():
    return get_party_classifier()
