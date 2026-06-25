"""
Obligation Extraction Service
==============================
Extracts obligations from contract clauses using regex patterns.
Identifies: who, what, when, and consequences.

Future Enhancement: Can be upgraded to use Legal-BERT for better accuracy.
"""

import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import dateparser

logger = logging.getLogger(__name__)


class ObligationExtractor:
    """
    Extract obligations from clause text using regex patterns.

    Identifies:
    - Obligated party (YOUR_COMPANY, COUNTERPARTY, BOTH)
    - Obligation type (PAYMENT, DELIVERY, COMPLIANCE, etc.)
    - Deadline/timing requirements
    - Penalty/consequences for breach
    """

    # Obligation trigger patterns
    OBLIGATION_PATTERNS = [
        # "shall" obligations
        (r'(\w+\s+(?:company|contractor|vendor|supplier|client|customer|party))\s+shall\s+(.+?)(?:\.|;|$)', 'SHALL'),
        # "must" obligations
        (r'(\w+\s+(?:company|contractor|vendor|supplier|client|customer|party))\s+must\s+(.+?)(?:\.|;|$)', 'MUST'),
        # "required to" obligations
        (r'(\w+\s+(?:company|contractor|vendor|supplier|client|customer))\s+(?:is|are)\s+required\s+to\s+(.+?)(?:\.|;|$)', 'REQUIRED'),
        # "agrees to" obligations
        (r'(\w+\s+(?:company|contractor|vendor|supplier|client|customer))\s+agrees?\s+to\s+(.+?)(?:\.|;|$)', 'AGREES'),
        # "will" obligations (future tense)
        (r'(\w+\s+(?:company|contractor|vendor|supplier|client|customer|party))\s+will\s+(.+?)(?:\.|;|$)', 'WILL'),
        # "responsible for" obligations
        (r'(\w+\s+(?:company|contractor|vendor|supplier|client|customer))\s+(?:is|are)\s+responsible\s+for\s+(.+?)(?:\.|;|$)', 'RESPONSIBLE'),
    ]

    # Deadline/timing patterns
    DEADLINE_PATTERNS = [
        (r'within\s+(\d+)\s+(days?|weeks?|months?|years?)', 'RELATIVE'),
        (r'by\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4})', 'ABSOLUTE'),
        (r'on\s+or\s+before\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4})', 'ABSOLUTE'),
        (r'no\s+later\s+than\s+(.+?)(?:\.|;|,|$)', 'DEADLINE'),
        (r'(immediately|promptly|forthwith)', 'IMMEDIATE'),
        (r'(quarterly|monthly|annually|weekly|daily)', 'RECURRING'),
    ]

    # Penalty/consequence patterns
    PENALTY_PATTERNS = [
        (r'penalty\s+of\s+([₹$€£]?\s*[\d,]+(?:\.\d{2})?)', 'FIXED'),
        (r'liquidated\s+damages\s+of\s+([₹$€£]?\s*[\d,]+(?:\.\d{2})?)', 'LIQUIDATED'),
        (r'(\d+)%\s+of\s+(?:contract|total|project)\s+value', 'PERCENTAGE'),
        (r'termination\s+of\s+(?:this\s+)?(?:agreement|contract)', 'TERMINATION'),
        (r'breach\s+of\s+contract', 'BREACH'),
    ]

    # Obligation type keywords
    TYPE_KEYWORDS = {
        'PAYMENT': ['pay', 'payment', 'invoice', 'fee', 'remuneration', 'compensation', 'amount due'],
        'DELIVERY': ['deliver', 'provide', 'supply', 'furnish', 'complete', 'perform', 'execute'],
        'COMPLIANCE': ['comply', 'compliance', 'adhere', 'conform', 'satisfy', 'meet requirements'],
        'REPORTING': ['report', 'notify', 'inform', 'disclose', 'communicate', 'advise'],
        'NOTICE': ['notice', 'notification', 'written notice', 'inform in writing'],
        'TERMINATION': ['terminate', 'termination', 'end', 'cancel', 'discontinue'],
        'OTHER': [],
    }

    # Party identification
    PARTY_KEYWORDS = {
        'YOUR_COMPANY': ['contractor', 'vendor', 'supplier', 'service provider', 'consultant', 'we', 'us', 'our'],
        'COUNTERPARTY': ['client', 'customer', 'employer', 'buyer', 'purchaser', 'you', 'your'],
        'BOTH': ['both parties', 'each party', 'parties', 'mutual'],
    }

    def extract_obligations(self, clause_text: str, clause_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Extract all obligations from clause text.

        Args:
            clause_text: Text to analyze
            clause_type: Optional clause type hint

        Returns:
            List of obligation dictionaries
        """
        if not clause_text or len(clause_text.strip()) < 10:
            return []

        obligations = []
        text_lower = clause_text.lower()

        # Find all obligation triggers
        for pattern, trigger_type in self.OBLIGATION_PATTERNS:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)

            for match in matches:
                try:
                    party_text = match.group(1) if match.lastindex >= 1 else ''
                    obligation_text = match.group(2) if match.lastindex >= 2 else ''

                    if not obligation_text or len(obligation_text.strip()) < 5:
                        continue

                    # Extract obligation details
                    obligation = {
                        'title': self._generate_title(obligation_text, clause_type),
                        'description': obligation_text.strip(),
                        'full_text': match.group(0),
                        'category': self._classify_obligation_type(obligation_text, clause_type),
                        'responsible_party': self._identify_party(party_text),
                        'priority': self._assess_priority(obligation_text),
                        'due_date_text': self._extract_deadline(clause_text),
                        'clause_reference': clause_type or 'General',
                        'confidence': self._calculate_confidence(trigger_type, obligation_text),
                        'extraction_metadata': {
                            'trigger_type': trigger_type,
                            'pattern_used': pattern[:50],
                            'extracted_at': datetime.now().isoformat()
                        }
                    }

                    # Extract penalty information
                    penalty_info = self._extract_penalty(clause_text)
                    if penalty_info:
                        obligation['penalty_info'] = penalty_info

                    obligations.append(obligation)

                except Exception as e:
                    logger.warning(f"Failed to extract obligation: {e}")
                    continue

        # Deduplicate similar obligations
        obligations = self._deduplicate_obligations(obligations)

        return obligations

    def _generate_title(self, obligation_text: str, clause_type: Optional[str]) -> str:
        """Generate concise title for obligation"""
        # Take first 50 chars and clean up
        title = obligation_text[:50].strip()
        if len(obligation_text) > 50:
            title += '...'

        # Add clause type prefix if available
        if clause_type:
            title = f"[{clause_type}] {title}"

        return title

    def _classify_obligation_type(self, obligation_text: str, clause_type: Optional[str]) -> str:
        """Classify the type of obligation"""
        text_lower = obligation_text.lower()

        # Check clause type hint first
        if clause_type:
            clause_type_lower = clause_type.lower()
            for category, keywords in self.TYPE_KEYWORDS.items():
                if any(kw in clause_type_lower for kw in keywords):
                    return category

        # Check obligation text
        max_matches = 0
        best_category = 'OTHER'

        for category, keywords in self.TYPE_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches > max_matches:
                max_matches = matches
                best_category = category

        return best_category

    def _identify_party(self, party_text: str) -> str:
        """Identify which party is obligated"""
        party_text_lower = party_text.lower()

        for party, keywords in self.PARTY_KEYWORDS.items():
            if any(kw in party_text_lower for kw in keywords):
                return party

        return 'YOUR_COMPANY'  # Default assumption

    def _assess_priority(self, obligation_text: str) -> str:
        """Assess priority level of obligation"""
        text_lower = obligation_text.lower()

        # High priority keywords
        high_priority = ['immediately', 'urgent', 'critical', 'mandatory', 'required', 'shall', 'must']
        medium_priority = ['should', 'expected', 'requested']

        if any(kw in text_lower for kw in high_priority):
            return 'HIGH'
        elif any(kw in text_lower for kw in medium_priority):
            return 'MEDIUM'
        else:
            return 'LOW'

    def _extract_deadline(self, text: str) -> Optional[str]:
        """Extract deadline/timing information"""
        for pattern, deadline_type in self.DEADLINE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None

    def _extract_penalty(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract penalty/consequence information"""
        for pattern, penalty_type in self.PENALTY_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return {
                    'type': penalty_type,
                    'text': match.group(0),
                    'amount': match.group(1) if match.lastindex >= 1 else None
                }
        return None

    def _calculate_confidence(self, trigger_type: str, obligation_text: str) -> float:
        """Calculate confidence score for extraction"""
        confidence = 0.5  # Base confidence

        # Higher confidence for strong trigger words
        if trigger_type in ['SHALL', 'MUST', 'REQUIRED']:
            confidence += 0.3
        elif trigger_type in ['AGREES', 'RESPONSIBLE']:
            confidence += 0.2
        else:
            confidence += 0.1

        # Increase confidence if obligation is detailed
        if len(obligation_text) > 50:
            confidence += 0.1

        # Cap at 1.0
        return min(confidence, 1.0)

    def _deduplicate_obligations(self, obligations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate or very similar obligations"""
        if len(obligations) <= 1:
            return obligations

        unique_obligations = []
        seen_descriptions = set()

        for obligation in obligations:
            # Create a normalized version for comparison
            normalized = obligation['description'].lower().strip()

            # Check if similar obligation already exists
            is_duplicate = False
            for seen in seen_descriptions:
                if self._similarity_ratio(normalized, seen) > 0.8:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_obligations.append(obligation)
                seen_descriptions.add(normalized)

        return unique_obligations

    def _similarity_ratio(self, str1: str, str2: str) -> float:
        """Calculate simple similarity ratio between two strings"""
        if not str1 or not str2:
            return 0.0

        # Simple word-based similarity
        words1 = set(str1.split())
        words2 = set(str2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0


# Convenience function
def extract_obligations_from_clause(clause_text: str, clause_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Extract obligations from clause text"""
    extractor = ObligationExtractor()
    return extractor.extract_obligations(clause_text, clause_type)
