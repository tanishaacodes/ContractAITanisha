"""
BOQ Cost Modeling + Margin Optimization Engine
Calculates optimal bid pricing with win probability analysis
"""
from typing import List, Dict, Tuple
from decimal import Decimal


class BOQCostModeler:
    """Calculate comprehensive BOQ costs with risk premiums"""

    def __init__(self):
        # Default cost percentages
        self.default_overhead = 10.0  # 10% overhead
        self.default_risk_factor = 0.05  # 5% risk premium

    def calculate_item_cost(self, item: Dict) -> Decimal:
        """
        Calculate total cost for a single BOQ item

        Args:
            item: Dictionary with cost components

        Returns:
            Total unit cost including overhead and risk
        """
        # Base costs (guard against None from nullable DB fields)
        material = Decimal(str(item.get('base_material_cost') or 0))
        labor = Decimal(str(item.get('base_labor_cost') or 0))
        equipment = Decimal(str(item.get('base_equipment_cost') or 0))

        base_cost = material + labor + equipment

        # Overhead
        overhead_percent = item.get('overhead_percentage', self.default_overhead)
        overhead = base_cost * Decimal(str(overhead_percent / 100))

        # Risk premium
        risk_factor = item.get('risk_factor', self.default_risk_factor)
        risk_premium = base_cost * Decimal(str(risk_factor))

        # Total unit cost
        total_cost = base_cost + overhead + risk_premium

        return total_cost

    def calculate_project_cost(self, work_items: List[Dict]) -> Dict:
        """
        Calculate total project cost from all BOQ items

        Args:
            work_items: List of work item dictionaries

        Returns:
            Cost breakdown dictionary
        """
        total_material = Decimal('0')
        total_labor = Decimal('0')
        total_equipment = Decimal('0')
        total_overhead = Decimal('0')
        total_risk = Decimal('0')

        category_costs = {
            'CIVIL': Decimal('0'),
            'MECHANICAL': Decimal('0'),
            'MEP': Decimal('0'),
            'OTHER': Decimal('0')
        }

        for item in work_items:
            # Calculate unit cost
            unit_cost = self.calculate_item_cost(item)
            quantity = Decimal(str(item.get('quantity') or 1))

            # Total item cost
            item_total = unit_cost * quantity

            # Accumulate by category
            category = item.get('category', 'OTHER')
            if category in category_costs:
                category_costs[category] += item_total

            # Accumulate components
            total_material += Decimal(str(item.get('base_material_cost') or 0)) * quantity
            total_labor += Decimal(str(item.get('base_labor_cost') or 0)) * quantity
            total_equipment += Decimal(str(item.get('base_equipment_cost') or 0)) * quantity

        # Calculate overhead and risk on base
        base_cost = total_material + total_labor + total_equipment
        total_overhead = base_cost * Decimal('0.1')  # 10%
        total_risk = base_cost * Decimal('0.05')  # 5%

        total_project_cost = base_cost + total_overhead + total_risk

        return {
            'base_cost': float(base_cost),
            'material_cost': float(total_material),
            'labor_cost': float(total_labor),
            'equipment_cost': float(total_equipment),
            'overhead': float(total_overhead),
            'risk_premium': float(total_risk),
            'total_cost': float(total_project_cost),
            'category_breakdown': {k: float(v) for k, v in category_costs.items()}
        }


class MarginOptimizer:
    """Optimize bid margin based on win probability"""

    def __init__(self):
        pass

    def generate_scenarios(
        self,
        base_cost: Decimal,
        tender_risk_score: float,
        company_competitiveness: float,
        margin_range: Tuple[int, int] = (5, 25),
        step: int = 5
    ) -> List[Dict]:
        """
        Generate bid scenarios with different margins

        Args:
            base_cost: Base project cost
            tender_risk_score: Risk score (0-1)
            company_competitiveness: Company's past win rate (0-1)
            margin_range: (min_margin%, max_margin%)
            step: Margin increment

        Returns:
            List of scenario dictionaries
        """
        scenarios = []
        min_margin, max_margin = margin_range

        # Normalise base_cost to float so arithmetic is consistent
        base_cost_f = float(base_cost)

        for margin_pct in range(min_margin, max_margin + 1, step):
            # Calculate bid price
            margin_factor = margin_pct / 100
            bid_price = base_cost_f * (1 + margin_factor)

            # Estimate win probability
            win_prob = self._estimate_win_probability(
                margin_pct,
                tender_risk_score,
                company_competitiveness
            )

            # Calculate expected profit
            profit = bid_price - base_cost_f
            expected_profit = profit * (win_prob / 100)

            scenarios.append({
                'margin_percentage': margin_pct,
                'total_cost': base_cost_f,
                'bid_price': bid_price,
                'gross_profit': profit,
                'win_probability': win_prob,
                'expected_profit': expected_profit
            })

        return scenarios

    def _estimate_win_probability(
        self,
        margin_pct: int,
        risk_score: float,
        competitiveness: float
    ) -> float:
        """
        Estimate win probability based on multiple factors

        Factors:
        - Margin: Lower margin = higher win probability
        - Risk: Higher risk = lower win probability
        - Competitiveness: Company's track record

        Returns:
            Win probability (0-100)
        """
        # Base probability starts at 70%, decreases with margin
        base_prob = 70 - (margin_pct * 2)  # Each 1% margin reduces win prob by 2%

        # Risk adjustment (0-1 score, higher = worse)
        risk_adjustment = -risk_score * 10  # Up to -10% for high risk

        # Competitiveness adjustment (0-1 score, higher = better)
        competitive_adjustment = competitiveness * 5  # Up to +5% for good track record

        # Market condition adjustment (can be parameterized)
        market_adjustment = 0  # Neutral

        # Calculate total probability
        win_probability = (
            base_prob +
            risk_adjustment +
            competitive_adjustment +
            market_adjustment
        )

        # Clamp between 5% and 95%
        win_probability = max(5, min(95, win_probability))

        return round(win_probability, 2)

    def select_optimal(self, scenarios: List[Dict]) -> Dict:
        """
        Select optimal bid scenario based on expected profit

        Args:
            scenarios: List of bid scenarios

        Returns:
            Recommended scenario
        """
        if not scenarios:
            return None

        # Find scenario with highest expected profit
        optimal = max(scenarios, key=lambda s: s['expected_profit'])

        # Also consider risk-adjusted options
        # If a slightly lower margin has similar expected profit but higher win prob, prefer it
        optimal_expected = optimal['expected_profit']

        for scenario in scenarios:
            # If expected profit is within 5% and win probability is 10%+ higher
            if (scenario['expected_profit'] >= optimal_expected * 0.95 and
                scenario['win_probability'] >= optimal['win_probability'] + 10):
                optimal = scenario
                break

        return optimal


class NegotiationAutomation:
    """Automate tender negotiation strategy"""

    def __init__(self, llm_client=None):
        self.llm_client = llm_client

        # Standard counter-proposal templates
        self.counter_templates = {
            'UNLIMITED_LIABILITY': {
                'template': 'Cap liability at {cap_multiple}x contract value',
                'cap_multiple': 2
            },
            'HIGH_LD': {
                'template': 'Limit liquidated damages to {max_percent}% of contract value',
                'max_percent': 10
            },
            'ONE_SIDED_TERMINATION': {
                'template': 'Require {notice_period} days notice for termination without cause, with payment for work completed',
                'notice_period': 90
            },
            'PERFORMANCE_GUARANTEE': {
                'template': 'Reduce performance guarantee to {max_percent}% with staged release',
                'max_percent': 10
            },
            'WARRANTY_PERIOD': {
                'template': 'Limit warranty period to {max_months} months with clear scope',
                'max_months': 24
            },
            'PAYMENT_TERMS': {
                'template': 'Request milestone-based payments with {advance_percent}% mobilization advance',
                'advance_percent': 10
            }
        }

    def generate_counter_proposal(self, risk: Dict, tender_value: Decimal = None) -> Dict:
        """
        Generate counter-proposal for a risk/unfavorable clause

        Args:
            risk: Risk dictionary
            tender_value: Tender value for calculations

        Returns:
            Counter-proposal dictionary
        """
        category = risk.get('category', 'OTHER')

        # Use LLM for custom counter-proposal
        if self.llm_client and risk.get('description'):
            return self._llm_counter_proposal(risk)

        # Use template-based counter-proposal
        if category in self.counter_templates:
            template_config = self.counter_templates[category]
            template = template_config['template']

            # Format template
            counter_text = template.format(**template_config)

            # Generate rationale
            rationale = self._generate_rationale(category, risk)

            return {
                'issue_type': category,
                'original_clause': risk.get('description', ''),
                'counter_proposal': counter_text,
                'rationale': rationale,
                'acceptance_probability': self._estimate_acceptance_probability(category)
            }

        # Generic counter-proposal
        return {
            'issue_type': category,
            'original_clause': risk.get('description', ''),
            'counter_proposal': 'Request clarification and more balanced terms',
            'rationale': 'Current terms pose unacceptable risk to contractor',
            'acceptance_probability': 0.5
        }

    def _llm_counter_proposal(self, risk: Dict) -> Dict:
        """Generate counter-proposal using LLM"""
        prompt = f"""
Rewrite this tender clause to reduce contractor exposure while remaining commercially reasonable:

Original Clause:
{risk.get('description', '')}

Rules:
- Cap liability where unlimited
- Balance termination rights
- Limit liquidated damages to 10%
- Maintain professional tone
- Be specific and clear

Provide:
1. Revised clause text
2. Brief rationale (2-3 sentences)
"""

        try:
            response = self.llm_client.chat(
                model="qwen2.5:0.5b",
                messages=[{"role": "user", "content": prompt}]
            )

            content = response["message"]["content"]

            # Parse response (simplified)
            return {
                'issue_type': risk.get('category', 'OTHER'),
                'original_clause': risk.get('description', ''),
                'counter_proposal': content,
                'rationale': 'Generated to balance risk allocation',
                'acceptance_probability': 0.6
            }
        except:
            return self.generate_counter_proposal(risk, None)

    def _generate_rationale(self, category: str, risk: Dict) -> str:
        """Generate rationale for counter-proposal"""
        rationales = {
            'UNLIMITED_LIABILITY': 'Unlimited liability exposes contractor to catastrophic risk beyond reasonable control. Industry standard is to cap at 2x contract value.',
            'HIGH_LD': 'Liquidated damages exceeding 10% of contract value are punitive rather than compensatory. Industry standard is 10% maximum.',
            'ONE_SIDED_TERMINATION': 'One-sided termination rights create significant risk for contractor investment. Balanced termination provisions with notice period are standard.',
            'PERFORMANCE_GUARANTEE': 'Excessive performance guarantee ties up contractor working capital. Industry standard is 10% with staged release upon completion milestones.',
            'WARRANTY_PERIOD': 'Extended warranty periods beyond 24 months significantly increase contractor risk and cost. Standard defects liability period is 12-24 months.',
            'PAYMENT_TERMS': 'Delayed payment terms impact contractor cash flow and project viability. Milestone-based payments with mobilization advance are industry standard.'
        }

        return rationales.get(category, 'Current terms create unbalanced risk allocation requiring adjustment.')

    def _estimate_acceptance_probability(self, category: str) -> float:
        """Estimate probability of counter-proposal acceptance"""
        probabilities = {
            'UNLIMITED_LIABILITY': 0.7,  # Usually negotiable
            'HIGH_LD': 0.6,  # Sometimes negotiable
            'ONE_SIDED_TERMINATION': 0.5,  # Depends on employer
            'PERFORMANCE_GUARANTEE': 0.6,  # Often negotiable
            'WARRANTY_PERIOD': 0.7,  # Usually negotiable
            'PAYMENT_TERMS': 0.4  # Often fixed by policy
        }

        return probabilities.get(category, 0.5)

    def prioritize_negotiations(self, risks: List[Dict]) -> List[Dict]:
        """
        Prioritize which risks to negotiate based on severity and probability

        Args:
            risks: List of risk dictionaries

        Returns:
            Sorted list with negotiation priority
        """
        scored_risks = []

        for risk in risks:
            # Priority score based on severity and negotiability
            severity = risk.get('severity_score', 0.5)
            category = risk.get('category', 'OTHER')
            acceptance_prob = self._estimate_acceptance_probability(category)

            # Higher score = higher priority
            # Balance severity (need to negotiate) with acceptance probability (likely to succeed)
            priority_score = severity * 0.7 + acceptance_prob * 0.3

            scored_risks.append({
                **risk,
                'negotiation_priority': priority_score,
                'acceptance_probability': acceptance_prob
            })

        # Sort by priority (highest first)
        scored_risks.sort(key=lambda r: r['negotiation_priority'], reverse=True)

        return scored_risks
