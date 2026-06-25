"""
Risk Engine for Contract Analysis

Calculates risk scores based on contract financial terms,
payment conditions, liability clauses, and vendor risk factors.
"""
import logging
from typing import Dict, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class RiskEngine:
    """
    Contract Risk Scoring Engine

    Analyzes SAP contract data and assigns risk scores based on:
    - Contract value
    - Payment terms
    - Liability clauses
    - Vendor credit rating
    - Contract duration
    - Geographic risk
    - Currency exposure
    """

    # Risk weights for different factors
    WEIGHTS = {
        'contract_value': 0.25,
        'payment_terms': 0.20,
        'liability': 0.20,
        'vendor_credit': 0.15,
        'duration': 0.10,
        'currency': 0.10
    }

    # Risk thresholds
    THRESHOLDS = {
        'LOW': 30,
        'MEDIUM': 60,
        'HIGH': 80
    }

    def score(self, contract: Dict[str, Any]) -> int:
        """
        Calculate overall risk score for a contract

        Args:
            contract: SAP contract data (OData response)

        Returns:
            Risk score (0-100)
        """
        try:
            # Extract contract data
            data = contract.get('d', contract)

            # Individual risk component scores
            value_risk = self._score_contract_value(data)
            payment_risk = self._score_payment_terms(data)
            liability_risk = self._score_liability(data)
            vendor_risk = self._score_vendor(data)
            duration_risk = self._score_duration(data)
            currency_risk = self._score_currency(data)

            # Weighted total score
            total_score = (
                value_risk * self.WEIGHTS['contract_value'] +
                payment_risk * self.WEIGHTS['payment_terms'] +
                liability_risk * self.WEIGHTS['liability'] +
                vendor_risk * self.WEIGHTS['vendor_credit'] +
                duration_risk * self.WEIGHTS['duration'] +
                currency_risk * self.WEIGHTS['currency']
            )

            final_score = min(int(total_score), 100)

            logger.info(f"Risk score calculated: {final_score} "
                       f"(value:{value_risk}, payment:{payment_risk}, "
                       f"liability:{liability_risk})")

            return final_score

        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return 50  # Default medium risk if calculation fails

    def _score_contract_value(self, data: Dict) -> float:
        """Score risk based on contract value"""
        try:
            net_value = float(data.get('NetAmount', 0))

            if net_value > 10_000_000:  # > 1 Crore
                return 80
            elif net_value > 5_000_000:
                return 60
            elif net_value > 1_000_000:
                return 40
            elif net_value > 100_000:
                return 20
            else:
                return 10

        except (ValueError, TypeError):
            return 10

    def _score_payment_terms(self, data: Dict) -> float:
        """Score risk based on payment terms"""
        try:
            payment_terms = str(data.get('PaymentTerms', ''))

            # Extract days (e.g., "NET 90" or "90 days")
            days = 0
            for word in payment_terms.split():
                if word.isdigit():
                    days = int(word)
                    break

            # Extended payment terms = higher risk
            if days >= 120:
                return 80
            elif days >= 90:
                return 60
            elif days >= 60:
                return 40
            elif days >= 30:
                return 20
            else:
                return 10

        except Exception:
            return 30  # Default

    def _score_liability(self, data: Dict) -> float:
        """Score risk based on liability clauses mentioned in contract description"""
        try:
            description = data.get('PurchaseContractDesc', '').upper()
            contract_text = data.get('ContractText', '').upper()
            combined_text = f"{description} {contract_text}"

            risk_score = 0

            # Check for high-risk liability keywords
            if 'UNLIMITED' in combined_text and 'INDEMNITY' in combined_text:
                risk_score += 60

            if 'INDEMNITY' in combined_text:
                risk_score += 30

            if 'UNLIMITED LIABILITY' in combined_text:
                risk_score += 40

            if 'NO LIMITATION' in combined_text:
                risk_score += 30

            # Check for protective clauses (reduce risk)
            if 'LIABILITY CAP' in combined_text or 'LIMITED TO' in combined_text:
                risk_score -= 20

            if 'FORCE MAJEURE' in combined_text:
                risk_score -= 10

            return max(0, min(risk_score, 100))

        except Exception:
            return 20

    def _score_vendor(self, data: Dict) -> float:
        """Score risk based on vendor credit rating"""
        try:
            # In a real implementation, this would query vendor master data
            vendor_rating = data.get('VendorCreditRating', '')

            rating_scores = {
                'AAA': 5,
                'AA': 10,
                'A': 20,
                'BBB': 40,
                'BB': 60,
                'B': 80,
                'CCC': 90,
                '': 30  # Unknown
            }

            return rating_scores.get(vendor_rating, 30)

        except Exception:
            return 30

    def _score_duration(self, data: Dict) -> float:
        """Score risk based on contract duration"""
        try:
            valid_from = data.get('ValidityStartDate')
            valid_to = data.get('ValidityEndDate')

            if not valid_from or not valid_to:
                return 20

            # Calculate duration in months (simplified)
            # In production, use proper date parsing
            # Longer contracts = higher risk
            duration_years = 1  # Placeholder

            if duration_years >= 5:
                return 70
            elif duration_years >= 3:
                return 50
            elif duration_years >= 2:
                return 30
            else:
                return 10

        except Exception:
            return 20

    def _score_currency(self, data: Dict) -> float:
        """Score risk based on currency exposure"""
        try:
            currency = data.get('DocumentCurrency', 'INR')

            # Foreign currency = higher FX risk
            if currency not in ['INR', 'USD', 'EUR']:
                return 60
            elif currency == 'USD' or currency == 'EUR':
                return 30
            else:
                return 10

        except Exception:
            return 10

    def category(self, score: int) -> str:
        """
        Convert numeric risk score to category

        Args:
            score: Risk score (0-100)

        Returns:
            Risk category: LOW, MEDIUM, HIGH, or CRITICAL
        """
        if score < self.THRESHOLDS['LOW']:
            return 'LOW'
        elif score < self.THRESHOLDS['MEDIUM']:
            return 'MEDIUM'
        elif score < self.THRESHOLDS['HIGH']:
            return 'HIGH'
        else:
            return 'CRITICAL'

    def get_risk_details(self, contract: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get detailed risk breakdown

        Returns:
            Dictionary with risk score, category, and component scores
        """
        data = contract.get('d', contract)

        score = self.score(contract)
        category = self.category(score)

        return {
            'overall_score': score,
            'category': category,
            'components': {
                'contract_value': self._score_contract_value(data),
                'payment_terms': self._score_payment_terms(data),
                'liability': self._score_liability(data),
                'vendor_credit': self._score_vendor(data),
                'duration': self._score_duration(data),
                'currency': self._score_currency(data)
            }
        }
