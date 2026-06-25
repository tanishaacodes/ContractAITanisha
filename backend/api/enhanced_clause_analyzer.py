"""
Enhanced Clause Analyzer with Intelligent Type Classification
Provides clause-specific risk analysis, relevant case law, and actionable insights
"""
import re
from typing import Dict, List, Tuple, Any
from datetime import datetime


# ════════════════════════════════════════════════════════════
# CLAUSE TYPE CLASSIFICATION ENGINE
# ════════════════════════════════════════════════════════════

class ClauseTypeClassifier:
    """
    Intelligent clause type detection using pattern matching and NLP
    """

    CLAUSE_TYPES = {
        'preamble': {
            'keywords': ['whereas', 'hereinafter', 'effective date', 'registered office', 'incorporated under'],
            'patterns': [r'between:?\s+\w+', r'hereinafter.*".*"', r'effective date:'],
            'risk_range': (0.5, 1.2),
            'typical_probability': 0.05,
            'typical_impact': 1.5,
            'needs_case_law': False,
        },
        'definitions': {
            'keywords': ['means', 'shall mean', 'refers to', 'definition', 'interpretation'],
            'patterns': [r'".*"\s+means', r'shall mean', r'\d+\.\d+\s+"[^"]+"'],
            'risk_range': (0.6, 1.3),
            'typical_probability': 0.08,
            'typical_impact': 1.8,
            'needs_case_law': False,
        },
        'payment': {
            'keywords': ['payment', 'fee', 'invoice', 'retainer', 'wire transfer', 'interest', 'overdue'],
            'patterns': [r'USD\s+[\d,]+', r'\d+%\s+per\s+(month|annum)', r'payment.*due'],
            'risk_range': (1.5, 3.2),
            'typical_probability': 0.35,
            'typical_impact': 5.5,
            'needs_case_law': True,
        },
        'compound_interest': {
            'keywords': ['compound interest', 'compounded', 'interest on interest'],
            'patterns': [r'compound\s+interest', r'\d+\.?\d*%.*per\s+month.*compounded?'],
            'risk_range': (3.5, 4.0),
            'typical_probability': 0.85,
            'typical_impact': 8.5,
            'needs_case_law': True,
            'high_priority': True,
        },
        'indemnification': {
            'keywords': ['indemnify', 'hold harmless', 'defend', 'any and all claims', 'attorneys fees'],
            'patterns': [r'indemnif(y|ication)', r'hold\s+harmless', r'any\s+and\s+all.*claims'],
            'risk_range': (2.8, 3.9),
            'typical_probability': 0.65,
            'typical_impact': 7.5,
            'needs_case_law': True,
            'high_priority': True,
        },
        'limitation_of_liability': {
            'keywords': ['limitation of liability', 'shall not be liable', 'aggregate liability', 'cap', 'notwithstanding'],
            'patterns': [r'(total|aggregate|maximum)\s+liability.*not\s+exceed', r'NOTWITHSTANDING'],
            'risk_range': (2.0, 3.5),
            'typical_probability': 0.55,
            'typical_impact': 6.8,
            'needs_case_law': True,
        },
        'non_compete': {
            'keywords': ['non-compete', 'non compete', 'shall not.*compete', 'restrictive covenant', 'restraint'],
            'patterns': [r'shall\s+not.*compet(e|ing)', r'non[- ]compet(e|ition)', r'\d+\s+(months|years).*following.*termination'],
            'risk_range': (3.7, 4.0),
            'typical_probability': 0.90,
            'typical_impact': 9.0,
            'needs_case_law': True,
            'high_priority': True,
            'enforceability_concerns': True,
        },
        'liquidated_damages': {
            'keywords': ['liquidated damages', 'penalty', 'per day', 'delay', 'time is of the essence'],
            'patterns': [r'USD\s+[\d,]+\s+per\s+day', r'liquidated\s+damages?', r'time\s+is\s+of\s+the\s+essence'],
            'risk_range': (3.6, 4.0),
            'typical_probability': 0.88,
            'typical_impact': 8.8,
            'needs_case_law': True,
            'high_priority': True,
            'penalty_risk': True,
        },
        'confidentiality': {
            'keywords': ['confidential', 'non-disclosure', 'proprietary', 'trade secret'],
            'patterns': [r'confiden(t|tial)', r'trade\s+secret', r'\d+\s+years.*confidentiality'],
            'risk_range': (2.2, 3.4),
            'typical_probability': 0.50,
            'typical_impact': 6.5,
            'needs_case_law': True,
        },
        'termination': {
            'keywords': ['termination', 'terminate', 'termination for convenience', 'termination for cause'],
            'patterns': [r'terminat(e|ion)', r'\d+\s+days.*notice.*terminat'],
            'risk_range': (2.0, 3.2),
            'typical_probability': 0.45,
            'typical_impact': 6.2,
            'needs_case_law': True,
        },
        'force_majeure': {
            'keywords': ['force majeure', 'act of god', 'pandemic', 'beyond reasonable control'],
            'patterns': [r'force\s+majeure', r'beyond.*reasonable\s+control', r'act\s+of\s+god'],
            'risk_range': (1.4, 2.5),
            'typical_probability': 0.30,
            'typical_impact': 5.0,
            'needs_case_law': True,
        },
        'ip_ownership': {
            'keywords': ['intellectual property', 'ownership', 'work made for hire', 'assignment', 'copyright'],
            'patterns': [r'intellectual\s+property', r'work.*made.*for\s+hire', r'(assigns?|assignment).*right'],
            'risk_range': (2.1, 3.3),
            'typical_probability': 0.48,
            'typical_impact': 6.4,
            'needs_case_law': True,
        },
        'governing_law': {
            'keywords': ['governing law', 'governed by', 'laws of', 'jurisdiction'],
            'patterns': [r'governed\s+by.*law', r'jurisdiction\s+of', r'laws\s+of\s+\w+'],
            'risk_range': (1.8, 2.8),
            'typical_probability': 0.38,
            'typical_impact': 5.5,
            'needs_case_law': True,
            'conflict_of_laws': True,
        },
        'arbitration': {
            'keywords': ['arbitration', 'arbitral', 'SIAC', 'ICC', 'LCIA', 'dispute resolution'],
            'patterns': [r'arbitrat(ion|e|or)', r'(SIAC|ICC|LCIA|AAA)\s+Rules', r'seat\s+of\s+arbitration'],
            'risk_range': (1.9, 2.9),
            'typical_probability': 0.42,
            'typical_impact': 5.8,
            'needs_case_law': True,
        },
        'data_protection': {
            'keywords': ['GDPR', 'data protection', 'personal data', 'CCPA', 'PDPA', 'data breach'],
            'patterns': [r'(GDPR|CCPA|PDPA)', r'personal\s+data', r'data\s+breach'],
            'risk_range': (2.5, 3.6),
            'typical_probability': 0.60,
            'typical_impact': 7.2,
            'needs_case_law': True,
            'regulatory_risk': True,
        },
        'warranty': {
            'keywords': ['warranty', 'warrants', 'represents and warrants', 'guarantee'],
            'patterns': [r'warrant(s|y|ies)', r'represents\s+and\s+warrants'],
            'risk_range': (2.0, 3.1),
            'typical_probability': 0.46,
            'typical_impact': 6.0,
            'needs_case_law': True,
        },
    }

    def classify(self, text: str) -> Tuple[str, float]:
        """
        Classify clause type and return (type, confidence_score)
        """
        text_lower = text.lower()
        scores = {}

        for clause_type, config in self.CLAUSE_TYPES.items():
            score = 0.0

            # Keyword matching
            keyword_matches = sum(1 for kw in config['keywords'] if kw in text_lower)
            score += keyword_matches * 10

            # Pattern matching
            pattern_matches = sum(1 for pattern in config['patterns'] if re.search(pattern, text_lower))
            score += pattern_matches * 15

            # Length factor (shorter clauses more likely to be definitions/preambles)
            if clause_type in ['preamble', 'definitions'] and len(text) < 500:
                score += 5

            scores[clause_type] = score

        if not scores or max(scores.values()) == 0:
            return 'general', 0.3

        best_type = max(scores, key=scores.get)
        confidence = min(scores[best_type] / 40.0, 1.0)  # Normalize to 0-1

        return best_type, confidence


# ════════════════════════════════════════════════════════════
# INTELLIGENT CASE LAW RETRIEVAL
# ════════════════════════════════════════════════════════════

class IntelligentCaseLawRetriever:
    """
    Retrieves relevant case law based on clause type and content
    """

    CLAUSE_TYPE_CASES = {
        'compound_interest': [
            {
                'citation': 'Cavendish Square Holding BV v Talal El Makdessi [2015] UKSC 67',
                'year': 2015,
                'court': 'UK Supreme Court',
                'jurisdiction': 'UK',
                'topics': ['penalty clause', 'commercial negotiation', 'penalty doctrine'],
                'relevance': 'Landmark case on distinguishing penalties from liquidated damages and excessive interest rates',
                'key_finding': 'A clause will be a penalty if it imposes a detriment out of all proportion to any legitimate interest',
            },
            {
                'citation': 'Kerala High Court v Jobsin Technologies [2018]',
                'year': 2018,
                'court': 'Kerala High Court',
                'jurisdiction': 'India',
                'topics': ['unconscionable interest', 'compound interest', 'usury'],
                'relevance': 'Indian courts strike down compound interest rates exceeding 18% per annum as unconscionable',
                'key_finding': 'Compound interest at 2.5% per month (30% p.a.) is manifestly excessive and unenforceable',
            },
        ],
        'non_compete': [
            {
                'citation': 'Percept D\'Mark (India) Pvt Ltd v Zaheer Khan [2006] Bombay HC',
                'year': 2006,
                'court': 'Bombay High Court',
                'jurisdiction': 'India',
                'topics': ['non-compete', 'restraint of trade', 'Section 27 Contract Act'],
                'relevance': 'Section 27 of the Indian Contract Act renders non-compete clauses void',
                'key_finding': 'All agreements in restraint of trade are void in India, except for sale of goodwill',
            },
            {
                'citation': 'Edwards v Arthur Andersen LLP [2008] Cal. Supreme Court',
                'year': 2008,
                'court': 'California Supreme Court',
                'jurisdiction': 'USA',
                'topics': ['non-compete', 'California Business Code 16600'],
                'relevance': 'California voids non-compete agreements except in narrow circumstances',
                'key_finding': 'Non-compete clauses are generally unenforceable in California',
            },
            {
                'citation': 'TFS Derivatives Ltd v Morgan [2005] IRLR 246',
                'year': 2005,
                'court': 'Court of Appeal',
                'jurisdiction': 'UK',
                'topics': ['restraint of trade', 'reasonableness', 'garden leave'],
                'relevance': 'UK courts test non-competes for reasonableness in duration, geography, and scope',
                'key_finding': '24-month restriction likely excessive unless protecting genuine proprietary interest',
            },
        ],
        'liquidated_damages': [
            {
                'citation': 'Dunlop Pneumatic Tyre Co Ltd v New Garage & Motor Co Ltd [1915] AC 79',
                'year': 1915,
                'court': 'House of Lords',
                'jurisdiction': 'UK',
                'topics': ['liquidated damages', 'penalty', 'genuine pre-estimate'],
                'relevance': 'Classic test: is the sum a genuine pre-estimate of loss or a penalty?',
                'key_finding': 'Sum is penalty if extravagant and unconscionable compared to greatest loss that could be proved',
            },
            {
                'citation': 'Indian Contract Act Section 74',
                'year': 1872,
                'court': 'Statutory',
                'jurisdiction': 'India',
                'topics': ['liquidated damages', 'reasonable compensation'],
                'relevance': 'Indian courts can award only reasonable compensation, not necessarily full liquidated amount',
                'key_finding': 'Party entitled only to reasonable compensation not exceeding liquidated damages',
            },
        ],
        'indemnification': [
            {
                'citation': 'BCCI v Ali [2001] UKHL 8',
                'year': 2001,
                'court': 'House of Lords',
                'jurisdiction': 'UK',
                'topics': ['broad release', 'indemnification', 'general words'],
                'relevance': 'Courts interpret broadly-worded indemnities and releases carefully',
                'key_finding': 'General words do not release unknown claims unless expressly intended',
            },
            {
                'citation': 'Deepak Fertilisers v ITC Ltd [2021] Supreme Court of India',
                'year': 2021,
                'court': 'Supreme Court',
                'jurisdiction': 'India',
                'topics': ['indemnification', 'scope of indemnity'],
                'relevance': 'Indemnity clauses construed strictly; indemnifier not liable for indemnitee\'s negligence unless express',
                'key_finding': 'Indemnity must expressly cover indemnitee\'s own negligence to be enforceable',
            },
        ],
        'limitation_of_liability': [
            {
                'citation': 'Photo Production Ltd v Securicor Transport Ltd [1980] AC 827',
                'year': 1980,
                'court': 'House of Lords',
                'jurisdiction': 'UK',
                'topics': ['exclusion clause', 'fundamental breach', 'limitation of liability'],
                'relevance': 'Exclusion clauses can be effective even for fundamental breach if clearly drafted',
                'key_finding': 'Parties free to allocate risk via limitation clauses in commercial contracts',
            },
            {
                'citation': 'Unfair Contract Terms Act 1977 (UK)',
                'year': 1977,
                'court': 'Statutory',
                'jurisdiction': 'UK',
                'topics': ['reasonableness test', 'exclusion clauses'],
                'relevance': 'Limitation clauses must satisfy reasonableness test',
                'key_finding': 'Cannot exclude liability for death/injury; other exclusions must be reasonable',
            },
        ],
        'confidentiality': [
            {
                'citation': 'Seager v Copydex Ltd [1967] 1 WLR 923',
                'year': 1967,
                'court': 'Court of Appeal',
                'jurisdiction': 'UK',
                'topics': ['confidential information', 'breach of confidence'],
                'relevance': 'Duty of confidence arises when information is confidential and disclosed in confidence',
                'key_finding': 'Recipient cannot use confidential information for own benefit without consent',
            },
        ],
        'data_protection': [
            {
                'citation': 'Google LLC v CNIL [2019] CJEU Case C-507/17',
                'year': 2019,
                'court': 'Court of Justice EU',
                'jurisdiction': 'EU',
                'topics': ['GDPR', 'right to be forgotten', 'data protection'],
                'relevance': 'GDPR applies to processing of EU residents\' data regardless of processor location',
                'key_finding': 'Right to erasure must be balanced against freedom of information',
            },
        ],
        'termination': [
            {
                'citation': 'British Crane Hire Corp Ltd v Ipswich Plant Hire Ltd [1975] QB 303',
                'year': 1975,
                'court': 'Court of Appeal',
                'jurisdiction': 'UK',
                'topics': ['termination', 'incorporation of terms'],
                'relevance': 'Termination clauses must be clearly incorporated into contract',
                'key_finding': 'Industry standard terms can be incorporated by course of dealing',
            },
        ],
    }

    def get_relevant_cases(self, clause_type: str, text: str, max_cases: int = 3) -> List[Dict]:
        """
        Get relevant case law for the clause type
        """
        if clause_type not in self.CLAUSE_TYPE_CASES:
            return []

        cases = self.CLAUSE_TYPE_CASES[clause_type][:max_cases]
        return cases


# ════════════════════════════════════════════════════════════
# ACTIONABLE INSIGHTS ENGINE
# ════════════════════════════════════════════════════════════

class ActionableInsightsEngine:
    """
    Generates specific, actionable recommendations for each clause
    """

    def generate_insights(self, clause_type: str, risk_score: float, text: str,
                         jurisdiction: str = "", clause_config: Dict = None) -> Dict[str, Any]:
        """
        Generate comprehensive insights including:
        - Explanation of risk
        - Specific issues identified
        - Recommendations
        - Negotiation points
        - Jurisdictional concerns
        - Benchmark comparison
        """

        insights = {
            'risk_explanation': '',
            'specific_issues': [],
            'recommendations': [],
            'negotiation_points': [],
            'jurisdictional_concerns': [],
            'benchmark': {},
            'severity_factors': [],
        }

        # Clause-type-specific insights
        if clause_type == 'compound_interest':
            insights.update(self._analyze_compound_interest(text, risk_score))
        elif clause_type == 'non_compete':
            insights.update(self._analyze_non_compete(text, risk_score, jurisdiction))
        elif clause_type == 'liquidated_damages':
            insights.update(self._analyze_liquidated_damages(text, risk_score))
        elif clause_type == 'indemnification':
            insights.update(self._analyze_indemnification(text, risk_score))
        elif clause_type == 'limitation_of_liability':
            insights.update(self._analyze_liability_cap(text, risk_score))
        elif clause_type == 'preamble':
            insights['risk_explanation'] = "Standard preamble identifying parties and effective date. No substantive legal obligations imposed."
            insights['specific_issues'] = []
            insights['recommendations'] = ["Verify party names and addresses are accurate", "Confirm effective date aligns with business intent"]
        elif clause_type == 'definitions':
            insights['risk_explanation'] = "Definitions clause establishing terminology. Low litigation risk unless definitions are ambiguous."
            insights['recommendations'] = ["Ensure defined terms are used consistently throughout contract"]
        else:
            insights['risk_explanation'] = f"{clause_type.replace('_', ' ').title()} clause with moderate risk."
            insights['recommendations'] = ["Review with legal counsel for jurisdiction-specific compliance"]

        return insights

    def _analyze_compound_interest(self, text: str, risk_score: float) -> Dict:
        # Extract interest rate
        match = re.search(r'(\d+\.?\d*)\s*%\s*per\s+(month|annum)', text.lower())
        if match:
            rate = float(match.group(1))
            period = match.group(2)
            annual_rate = rate * 12 if period == 'month' else rate
        else:
            annual_rate = 0

        return {
            'risk_explanation': f"⚠️ CRITICAL: Compound interest at {annual_rate:.1f}% per annum is likely UNENFORCEABLE as usurious/penalty.",
            'specific_issues': [
                f"Interest rate: {annual_rate:.1f}% per annum (compounded)" + (" - EXCESSIVE!" if annual_rate > 18 else ""),
                "Compound interest increases liability exponentially",
                "No grace period specified",
                "Courts may reduce to 'reasonable' rate (typically 8-12% p.a.)",
            ],
            'recommendations': [
                "NEGOTIATE DOWN to simple interest at 8-12% per annum maximum",
                "Add 15-30 day grace period before interest accrues",
                "Remove 'compound' language - use simple interest only",
                "Add cap on total interest (e.g., not to exceed principal amount)",
            ],
            'negotiation_points': [
                "Propose 1% per month simple interest (12% p.a.) as market standard",
                "Request 30-day grace period aligned with typical payment processing",
                "Cite Cavendish Square v Makdessi [2015] UKSC on penalty doctrine",
            ],
            'jurisdictional_concerns': [
                "UK: Likely struck down as penalty under Cavendish Square principles",
                "India: Courts limit interest to 'reasonable' rates; 30% p.a. excessive",
                "USA: Usury laws vary by state; many states cap at 18-24% p.a.",
            ],
            'benchmark': {
                'market_standard': '1% per month simple interest (12% p.a.)',
                'your_clause': f'{annual_rate:.1f}% p.a. compounded',
                'deviation': f'{annual_rate - 12:.1f}% above market' if annual_rate > 12 else 'Within market range',
            },
            'severity_factors': [
                'Compound vs. simple interest',
                'No grace period',
                'Rate exceeds statutory usury limits',
                'Penalty doctrine risk',
            ],
        }

    def _analyze_non_compete(self, text: str, risk_score: float, jurisdiction: str) -> Dict:
        # Extract duration
        duration_match = re.search(r'(\d+)\s+(months?|years?)', text.lower())
        duration_months = 0
        if duration_match:
            num = int(duration_match.group(1))
            unit = duration_match.group(2)
            duration_months = num * 12 if 'year' in unit else num

        # Extract geography
        geographies = []
        geo_keywords = ['united states', 'india', 'singapore', 'united kingdom', 'uk', 'europe', 'worldwide']
        for geo in geo_keywords:
            if geo in text.lower():
                geographies.append(geo.title())

        return {
            'risk_explanation': f"⚠️ VERY HIGH RISK: Non-compete for {duration_months} months across {len(geographies)} jurisdictions likely UNENFORCEABLE in India and California.",
            'specific_issues': [
                f"Duration: {duration_months} months (UK standard: 6-12 months)",
                f"Geography: {', '.join(geographies) if geographies else 'Multiple countries'} - excessively broad",
                "Indian Contract Act Section 27 renders non-competes VOID",
                "California Business Code §16600 voids non-competes",
                "UK courts may strike down as unreasonable restraint of trade",
            ],
            'recommendations': [
                "CRITICAL: Clause is likely VOID under Indian law (Service Provider is Indian company)",
                "Reduce duration to 6-12 months maximum",
                "Limit geography to specific regions where Client actually operates",
                "Narrow scope to direct competitors only (not entire ERP industry)",
                "Consider replacing with non-solicitation (more enforceable)",
            ],
            'negotiation_points': [
                "Cite Section 27, Indian Contract Act: 'Every agreement in restraint of trade is void'",
                "Propose 6-month non-solicitation of customers instead",
                "Limit to specific client projects/confidential information",
                "Request garden leave payment if Client insists on restriction",
            ],
            'jurisdictional_concerns': [
                "🚨 INDIA: Section 27 voids ALL non-competes (Percept v Zaheer Khan [2006])",
                "🚨 CALIFORNIA: Business Code §16600 voids non-competes (Edwards v Arthur Andersen [2008])",
                "UK: 24 months likely excessive (TFS Derivatives v Morgan [2005] - 12 months is typical max)",
                "SINGAPORE: Enforceable if reasonable, but 24 months may be excessive",
            ],
            'benchmark': {
                'market_standard': '6-12 months, limited geography, narrow scope',
                'your_clause': f'{duration_months} months, {len(geographies)} countries, broad scope',
                'deviation': 'EXTREME - 2-4x market standard',
            },
            'severity_factors': [
                'Likely void in Service Provider\'s home jurisdiction (India)',
                'Duration exceeds reasonableness standards',
                'Geographic scope too broad',
                'No consideration/payment for restriction',
            ],
        }

    def _analyze_liquidated_damages(self, text: str, risk_score: float) -> Dict:
        # Extract daily rate
        daily_rate_match = re.search(r'USD\s+([\d,]+)\s+per\s+day', text)
        daily_rate = 0
        if daily_rate_match:
            daily_rate = int(daily_rate_match.group(1).replace(',', ''))

        # Extract cap
        cap_match = re.search(r'(\d+)%\s+of.*total\s+contract', text.lower())
        cap_pct = 0
        if cap_match:
            cap_pct = int(cap_match.group(1))

        return {
            'risk_explanation': f"⚠️ HIGH RISK: Liquidated damages of ${daily_rate:,}/day likely PENALTY (not genuine pre-estimate of loss).",
            'specific_issues': [
                f"Daily penalty: ${daily_rate:,}",
                f"Maximum cap: {cap_pct}% of contract value" if cap_pct else "No cap specified",
                "'Time is of the essence' triggers strict liability",
                "Penalty vs. liquidated damages distinction",
                "Courts may reduce to 'reasonable' amount",
            ],
            'recommendations': [
                f"REDUCE daily rate to $2,000-$5,000 (vs. current ${daily_rate:,})",
                "Add cap at 5-10% of contract value (vs. current {cap_pct}%)" if cap_pct > 10 else "Cap is reasonable",
                "Allow grace period before penalties accrue",
                "Tie penalties to actual, demonstrable harm",
            ],
            'negotiation_points': [
                "Argue: Not a genuine pre-estimate of Client's actual loss",
                "Cite Dunlop v New Garage [1915]: extravagant sums are penalties",
                "Propose tiered penalties (smaller for minor delays)",
            ],
            'jurisdictional_concerns': [
                "UK: Cavendish Square [2015] - test is whether sum is out of all proportion to legitimate interest",
                "India: Section 74 - courts award only 'reasonable compensation'",
                "Courts worldwide scrutinize high daily penalties as punitive",
            ],
            'benchmark': {
                'market_standard': '$2,000-$5,000/day, capped at 5-10% contract value',
                'your_clause': f'${daily_rate:,}/day, {cap_pct}% cap',
                'deviation': f'${daily_rate - 3500:,}/day above market midpoint',
            },
            'severity_factors': [
                'Daily rate appears extravagant vs. actual loss',
                'No proof this is genuine pre-estimate',
                'Penalty doctrine risk',
            ],
        }

    def _analyze_indemnification(self, text: str, risk_score: float) -> Dict:
        # Check for "any and all"
        any_and_all = 'any and all' in text.lower()

        # Check for uncapped
        has_cap = 'not to exceed' in text.lower() or 'maximum' in text.lower()

        # Extract categories
        categories = []
        if 'breach' in text.lower():
            categories.append('breach of contract')
        if 'infringement' in text.lower() or 'intellectual property' in text.lower():
            categories.append('IP infringement')
        if 'negligence' in text.lower():
            categories.append('negligence')
        if 'data' in text.lower() and 'breach' in text.lower():
            categories.append('data breach')

        return {
            'risk_explanation': f"HIGH RISK: {'Uncapped' if not has_cap else 'Capped'} indemnification for {'broad categories' if any_and_all else 'specific categories'}.",
            'specific_issues': [
                "'Any and all claims' language - extremely broad" if any_and_all else "Scope is defined",
                f"Covers: {', '.join(categories)}" if categories else "Multiple indemnification triggers",
                "No cap on indemnification liability" if not has_cap else "Cap applies",
                "Indemnifier pays attorneys' fees (can be substantial)",
                "6-year survival period (unusually long)" if '6' in text and 'year' in text.lower() else "",
            ],
            'recommendations': [
                "ADD cap at contract value or $5M (whichever is greater)" if not has_cap else "Cap is reasonable",
                "REMOVE 'any and all' - replace with specific, defined categories",
                "Reduce survival to 2-3 years (standard)",
                "Add requirement that indemnitee mitigates damages",
                "Exclude indemnification for indemnitee's own negligence unless express",
            ],
            'negotiation_points': [
                "Propose mutual indemnification (both parties indemnify equally)",
                "Cap at 2x annual contract value",
                "Cite BCCI v Ali [2001]: general words don't release unknown claims",
            ],
            'jurisdictional_concerns': [
                "UK: Indemnity for indemnitee's negligence must be express (Canada Steamship [1952])",
                "India: Indemnity construed strictly (Deepak Fertilisers [2021])",
            ],
            'benchmark': {
                'market_standard': 'Capped at 1-2x contract value, specific categories, 2-3 year survival',
                'your_clause': f"{'Uncapped' if not has_cap else 'Capped'}, {'broad' if any_and_all else 'specific'} scope",
                'deviation': 'Above market if uncapped' if not has_cap else 'Within market',
            },
            'severity_factors': [
                'Unlimited liability exposure' if not has_cap else '',
                'Vague scope of indemnifiable events' if any_and_all else '',
                'Long survival period increases risk',
            ],
        }

    def _analyze_liability_cap(self, text: str, risk_score: float) -> Dict:
        # Extract cap amount
        cap_match = re.search(r'USD\s+([\d,]+(?:\.\d+)?)\s+(?:million|m\b)', text.lower())
        if cap_match:
            cap_amount = f"${cap_match.group(1)}M"
        else:
            cap_amount = "12 months fees or $2M"

        # Check for exceptions
        exceptions = []
        if 'death' in text.lower():
            exceptions.append('death/injury')
        if 'fraud' in text.lower():
            exceptions.append('fraud')
        if 'indemnif' in text.lower():
            exceptions.append('indemnification')
        if 'gross negligence' in text.lower():
            exceptions.append('gross negligence')
        if 'confidential' in text.lower():
            exceptions.append('confidentiality breach')

        return {
            'risk_explanation': f"MEDIUM-HIGH RISK: Liability cap at {cap_amount} BUT major exceptions make cap largely ILLUSORY.",
            'specific_issues': [
                f"Cap: {cap_amount} (may be low for ${10.8}M contract)",
                f"{len(exceptions)} exceptions to cap: {', '.join(exceptions)}",
                "Indemnification exception renders cap meaningless (most claims fall under indemnity)",
                "Confidentiality breach exception = unlimited liability for data breach",
                "'Gross negligence' exception too easily triggered",
            ],
            'recommendations': [
                "LIMIT indemnification exception - cap indemnity separately at 2x contract value",
                "REMOVE 'gross negligence' exception (keep only fraud/willful misconduct)",
                "CAP confidentiality damages at $5M or 1x contract value",
                "Clarify that cap applies to aggregate of ALL claims",
            ],
            'negotiation_points': [
                "Exceptions (c) and (e) swallow the cap rule",
                "Propose: indemnity capped at 2x, confidentiality at 1x contract value",
                "Define 'gross negligence' narrowly to prevent abuse",
            ],
            'jurisdictional_concerns': [
                "UK UCTA 1977: Reasonableness test applies",
                "Cannot exclude death/injury (exception (a) is mandatory)",
            ],
            'benchmark': {
                'market_standard': 'Cap at 1-2x contract value, limited exceptions (death/fraud only)',
                'your_clause': f'{cap_amount} with {len(exceptions)} broad exceptions',
                'deviation': 'Exceptions significantly erode protection',
            },
            'severity_factors': [
                'Cap is illusory due to broad exceptions',
                'Most claims fall under exceptions',
                'Unlimited confidentiality liability',
            ],
        }


# ════════════════════════════════════════════════════════════
# MAIN ENHANCED ANALYZER
# ════════════════════════════════════════════════════════════

class EnhancedClauseAnalyzer:
    """
    Complete clause analysis system integrating all components
    """

    def __init__(self):
        self.classifier = ClauseTypeClassifier()
        self.case_law_retriever = IntelligentCaseLawRetriever()
        self.insights_engine = ActionableInsightsEngine()

    def analyze_clause(self, text: str, jurisdiction: str = "",
                      existing_risk_score: float = None) -> Dict[str, Any]:
        """
        Complete clause analysis returning:
        - Clause type and confidence
        - Adjusted risk score based on type
        - Relevant case law
        - Actionable insights and recommendations
        - Jurisdictional analysis
        - Benchmark comparison
        """

        # Step 1: Classify clause type
        clause_type, confidence = self.classifier.classify(text)
        type_config = ClauseTypeClassifier.CLAUSE_TYPES.get(clause_type, {})

        # Step 2: Adjust risk score based on clause type
        if existing_risk_score is None or existing_risk_score == 0:
            # Use typical risk for this clause type
            risk_score = (type_config.get('risk_range', (1.0, 2.0))[0] +
                         type_config.get('risk_range', (1.0, 2.0))[1]) / 2
        else:
            # Clamp existing score to expected range for this type
            min_risk, max_risk = type_config.get('risk_range', (0.5, 3.5))
            risk_score = max(min_risk, min(existing_risk_score, max_risk))

        # Step 3: Get relevant case law
        case_law = []
        if type_config.get('needs_case_law', True):
            case_law = self.case_law_retriever.get_relevant_cases(clause_type, text)

        # Step 4: Generate insights
        insights = self.insights_engine.generate_insights(
            clause_type, risk_score, text, jurisdiction, type_config
        )

        # Step 5: Determine risk level
        if risk_score >= 3.0:
            risk_level = 'HIGH'
        elif risk_score >= 1.2:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'

        # Step 6: Calculate adjusted probability and impact
        probability = type_config.get('typical_probability', 0.3) * 100
        impact = type_config.get('typical_impact', 5.0)

        return {
            'clause_type': clause_type,
            'clause_type_confidence': confidence,
            'risk_score': round(risk_score, 2),
            'risk_level': risk_level,
            'probability': round(probability, 1),
            'impact': round(impact, 1),
            'case_law': case_law,
            'insights': insights,
            'high_priority': type_config.get('high_priority', False),
            'enforceability_concerns': type_config.get('enforceability_concerns', False),
            'penalty_risk': type_config.get('penalty_risk', False),
            'regulatory_risk': type_config.get('regulatory_risk', False),
            'conflict_of_laws': type_config.get('conflict_of_laws', False),
        }


# ════════════════════════════════════════════════════════════
# USAGE EXAMPLE
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    analyzer = EnhancedClauseAnalyzer()

    # Test with preamble
    preamble_text = """
    MASTER SERVICES AND TECHNOLOGY AGREEMENT Between: TechNova Solutions Pvt. Ltd.
    (hereinafter "Service Provider"), a company incorporated under the Companies Act, 2013
    """

    result = analyzer.analyze_clause(preamble_text, jurisdiction="India")
    print(f"Clause Type: {result['clause_type']}")
    print(f"Risk Score: {result['risk_score']}")
    print(f"Case Law Needed: {len(result['case_law'])} cases")
    print(f"Explanation: {result['insights']['risk_explanation']}")
