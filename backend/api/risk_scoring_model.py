"""
Risk Scoring Model - Model_0 for ContractAI MVP
Implements 20-category risk scoring with keyword-based detection
"""

import re

# Configuration
KEYWORD_WEIGHT = 1.5
MAX_SCORE_PER_CATEGORY = 5

# 20 Risk Categories with 20 Keywords Each
RISK_CATEGORIES = {
    "liability": [
        "liability", "damages", "unlimited liability", "consequential damages",
        "indirect damages", "special damages", "punitive damages", "liability cap",
        "aggregate liability", "excluded damages", "loss of profit",
        "loss of revenue", "no cap", "joint liability", "several liability",
        "willful misconduct", "gross negligence", "damages arising",
        "full liability", "statutory liability", "liability exclusion", "liability waiver"
    ],
    "indemnity": [
        "indemnify", "indemnification", "hold harmless", "third party claims",
        "defend", "defend at own cost", "settlement costs", "legal fees",
        "claims arising", "IP infringement", "bodily injury", "property damage",
        "product liability", "tax indemnity", "employment claims",
        "regulatory fines", "unlimited indemnity", "survival of indemnity",
        "reimbursement obligation", "indemnity scope"
    ],
    "payment": [
        "payment", "invoice", "net 90", "net 120", "delayed payment",
        "payment upon receipt", "payment discretion", "disputed invoice",
        "withholding payment", "offset rights", "conditional payment",
        "milestone payment", "no payment timeline", "extended credit",
        "retention amount", "pay when paid", "deferred payment",
        "installment delays", "interest free delay", "no late fee", "disputed amounts"
    ],
    "pricing": [
        "price escalation", "unilateral price change", "variable pricing",
        "index linked pricing", "currency fluctuation", "cost increase",
        "rate revision", "open pricing", "benchmark pricing",
        "no price lock", "inflation adjustment", "market adjustment",
        "unilateral adjustment", "re-pricing", "volume discount removal",
        "price review clause", "pricing discretion", "fee modification",
        "hidden charges", "additional fees"
    ],
    "termination": [
        "termination", "termination for convenience", "long notice period",
        "no termination right", "penalty on termination",
        "early termination fee", "lock-in period", "survival clause",
        "termination cause only", "restricted termination",
        "termination damages", "automatic survival", "post-termination obligations",
        "termination cost", "exit restrictions", "non-terminable",
        "termination consent", "delayed termination", "termination window",
        "termination liability", "irrevocable term"
    ],
    "auto_renewal": [
        "automatic renewal", "evergreen", "renewal unless terminated",
        "silent renewal", "rolling renewal", "renewal notice",
        "short notice period", "renewal by default", "renewal lock",
        "multi-year renewal", "renewal penalty", "deemed renewal",
        "renewal at discretion", "renewal clause", "recurring term",
        "non-cancellable renewal", "renewal trigger", "renewal condition",
        "renewal extension", "renewal escalation"
    ],
    "ip_ownership": [
        "work for hire", "IP assignment", "perpetual license",
        "exclusive license", "background IP", "foreground IP",
        "derivative works", "moral rights waiver", "IP transfer",
        "ownership vests", "joint ownership", "license back",
        "royalty free license", "sublicensing rights",
        "IP indemnity exclusion", "IP claims",
        "no IP protection", "IP waiver", "patent rights", "copyright ownership"
    ],
    "confidentiality": [
        "confidential information", "disclosure obligation",
        "exceptions to confidentiality", "residual knowledge",
        "permitted disclosure", "compelled disclosure",
        "confidentiality carve-out", "confidentiality term",
        "no confidentiality", "confidentiality waiver",
        "limited confidentiality", "third party disclosure",
        "employee disclosure", "affiliate disclosure",
        "confidentiality breach", "no remedy", "disclosure rights",
        "confidential info definition", "confidentiality exclusion", "disclosure scope"
    ],
    "data_privacy": [
        "personal data", "GDPR", "data controller", "data processor",
        "data breach", "cross-border transfer", "data localization",
        "data subject rights", "consent requirement",
        "data retention", "data deletion", "data anonymization",
        "PII", "sensitive data", "health data",
        "data security measures", "incident notification",
        "privacy laws", "lawful processing", "data compliance"
    ],
    "regulatory_compliance": [
        "applicable laws", "regulatory approval",
        "statutory compliance", "government authority",
        "export control", "sanctions", "anti-bribery",
        "anti-corruption", "competition law", "antitrust",
        "environmental law", "labor law", "tax compliance",
        "industry regulations", "licensing requirements",
        "permit obligations", "regulatory fines", "compliance failure",
        "legal violations", "regulatory breach"
    ],
    "governing_law": [
        "governing law", "jurisdiction", "foreign law",
        "exclusive jurisdiction", "unfavorable jurisdiction",
        "offshore courts", "arbitration seat",
        "choice of law", "conflict of laws",
        "venue selection", "foreign courts",
        "home court advantage", "neutral venue absence",
        "non-local jurisdiction", "governing jurisdiction",
        "legal venue", "cross-border law", "international law",
        "forum selection", "legal seat"
    ],
    "dispute_resolution": [
        "dispute", "arbitration", "binding arbitration", "sole arbitrator",
        "foreign arbitration", "arbitration costs",
        "litigation rights", "waiver of jury trial",
        "class action waiver", "dispute escalation",
        "mandatory mediation", "dispute resolution mechanism",
        "arbitration venue", "arbitration language",
        "no injunctive relief", "limited remedies",
        "exclusive remedy", "dispute costs",
        "no appeal", "dispute timeline", "dispute restriction"
    ],
    "force_majeure": [
        "force majeure", "act of god", "pandemic exclusion",
        "government action", "war", "natural disaster",
        "force majeure exclusion", "limited force majeure",
        "payment obligations survive", "no force majeure",
        "force majeure carve-out", "force majeure notice",
        "extended force majeure", "force majeure termination",
        "partial force majeure", "force majeure liability",
        "supplier force majeure", "labor strikes",
        "supply chain disruption", "force majeure scope"
    ],
    "sla_performance": [
        "warranty", "guarantee", "performance", "service levels",
        "uptime guarantee", "response time", "remedy limitation",
        "service credits", "no SLA", "best efforts only",
        "performance standards", "availability commitment",
        "penalty exclusion", "SLA exclusion", "SLA waiver",
        "performance disclaimer", "delivery timelines",
        "acceptance criteria", "delay tolerance", "milestone breach",
        "non-binding SLA", "limited remedies"
    ],
    "penalty_ld": [
        "penalty", "delay", "breach", "liquidated damages",
        "penalties", "late delivery penalty", "performance penalty",
        "uncapped penalties", "daily penalties", "cumulative penalties",
        "penalty escalation", "penalty without cap", "penalty discretion",
        "penalty per breach", "automatic penalty", "penalty trigger",
        "penalty waiver absence", "penalty survival",
        "penalty calculation", "penalty retention", "excessive penalties"
    ],
    "assignment_coc": [
        "assignment restriction", "no assignment",
        "change of control", "consent required",
        "assignment prohibition", "merger restriction",
        "restructuring consent", "transfer restriction",
        "novation restriction", "assignment penalty",
        "assignment nullity", "automatic termination",
        "change in ownership", "affiliate restriction",
        "assignment void", "transfer consent",
        "assignment condition", "assignment notice",
        "assignment liability", "control change clause"
    ],
    "exclusivity_noncompete": [
        "exclusivity", "non-compete",
        "restricted business", "sole supplier",
        "exclusive arrangement", "market restriction",
        "geographic restriction", "duration restriction",
        "competitive prohibition", "exclusivity term",
        "non-solicitation", "customer restriction",
        "employee restriction", "business restraint",
        "exclusive rights", "exclusivity penalty",
        "exclusive dealing", "non-competition obligation",
        "market lock-in", "exclusivity survival"
    ],
    "insurance": [
        "insurance coverage", "minimum coverage",
        "insurance certificate", "policy limits",
        "no insurance", "insufficient insurance",
        "coverage exclusion", "deductible",
        "self-insured", "lapse of insurance",
        "additional insured", "insurance waiver",
        "insurance obligation", "policy cancellation",
        "insurance survival", "coverage gap",
        "insurance proof", "insurance failure",
        "uninsured risk", "liability insurance"
    ],
    "audit_inspection": [
        "audit rights", "inspection rights",
        "unlimited audit", "frequent audit",
        "third party audit", "audit costs",
        "audit notice", "audit scope",
        "access to records", "on-site inspection",
        "regulatory audit", "compliance audit",
        "audit survival", "audit penalty",
        "audit burden", "audit frequency",
        "audit obligation", "intrusive audit",
        "records retention", "audit liability"
    ],
    "counterparty": [
        "financial instability", "insolvency",
        "bankruptcy", "credit risk",
        "payment default", "prior disputes",
        "weak balance sheet", "going concern",
        "litigation history", "sanctions exposure",
        "reputational risk", "compliance failures",
        "vendor dependency", "single supplier",
        "performance failures", "delivery delays",
        "contract breaches", "termination history",
        "credit downgrade", "counterparty risk"
    ]
}

# Category Display Names
CATEGORY_NAMES = {
    "liability": "Liability Risk",
    "indemnity": "Indemnity Risk",
    "payment": "Payment Risk",
    "pricing": "Pricing Risk",
    "termination": "Termination Risk",
    "auto_renewal": "Auto-Renewal Risk",
    "ip_ownership": "IP Ownership Risk",
    "confidentiality": "Confidentiality Risk",
    "data_privacy": "Data Privacy Risk",
    "regulatory_compliance": "Regulatory Compliance Risk",
    "governing_law": "Governing Law Risk",
    "dispute_resolution": "Dispute Resolution Risk",
    "force_majeure": "Force Majeure Risk",
    "sla_performance": "SLA / Performance Risk",
    "penalty_ld": "Penalty / Liquidated Damages Risk",
    "assignment_coc": "Assignment / Change-of-Control Risk",
    "exclusivity_noncompete": "Exclusivity / Non-Compete Risk",
    "insurance": "Insurance Risk",
    "audit_inspection": "Audit / Inspection Risk",
    "counterparty": "Counterparty Risk"
}


def count_keywords(text, keywords):
    """
    Count the number of unique keywords found in the text.
    Uses word boundary matching for accuracy.
    """
    text = text.lower()
    count = 0
    found_keywords = []

    for kw in keywords:
        pattern = r"\b" + re.escape(kw.lower()) + r"\b"
        if re.search(pattern, text):
            count += 1
            found_keywords.append(kw)

    return count, found_keywords


def score_category(text, keywords):
    """
    Calculate risk score for a single category.
    Score = min(keyword_hits × KEYWORD_WEIGHT, MAX_SCORE_PER_CATEGORY)
    """
    hits, found_keywords = count_keywords(text, keywords)
    score = hits * KEYWORD_WEIGHT
    final_score = min(score, MAX_SCORE_PER_CATEGORY)

    return {
        "score": round(final_score, 2),
        "keyword_hits": hits,
        "found_keywords": found_keywords
    }


def calculate_risk_level(total_score):
    """
    Determine risk level based on total score.
    0-15: Low
    16-40: Medium
    41-65: High
    66-100: Critical
    """
    if total_score <= 15:
        return "Low"
    elif total_score <= 40:
        return "Medium"
    elif total_score <= 65:
        return "High"
    else:
        return "Critical"


def risk_scoring_algorithm(contract_text):
    """
    Main risk scoring algorithm.
    Analyzes contract text against 20 risk categories.

    Args:
        contract_text (str): Full contract text

    Returns:
        dict: {
            "total_risk_score": float (0-100),
            "risk_level": str (Low/Medium/High/Critical),
            "category_breakdown": dict of category scores,
            "detailed_breakdown": dict with keyword details per category
        }
    """
    if not contract_text:
        return {
            "total_risk_score": 0,
            "risk_level": "Low",
            "category_breakdown": {},
            "detailed_breakdown": {}
        }

    category_scores = {}
    detailed_breakdown = {}
    total_score = 0

    for category_key, keywords in RISK_CATEGORIES.items():
        result = score_category(contract_text, keywords)
        score = result["score"]

        category_scores[category_key] = score
        detailed_breakdown[category_key] = {
            "display_name": CATEGORY_NAMES[category_key],
            "score": score,
            "keyword_hits": result["keyword_hits"],
            "found_keywords": result["found_keywords"][:5]  # Top 5 keywords for display
        }
        total_score += score

    risk_level = calculate_risk_level(total_score)

    return {
        "total_risk_score": round(total_score, 2),
        "risk_level": risk_level,
        "category_breakdown": category_scores,
        "detailed_breakdown": detailed_breakdown
    }


def get_top_risk_categories(category_breakdown, top_n=5):
    """
    Get top N risk categories by score.

    Args:
        category_breakdown (dict): Category scores
        top_n (int): Number of top categories to return

    Returns:
        list: List of tuples (category_name, score)
    """
    sorted_categories = sorted(
        category_breakdown.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return [
        (CATEGORY_NAMES[cat], score)
        for cat, score in sorted_categories[:top_n]
        if score > 0
    ]


def generate_risk_summary(risk_result):
    """
    Generate a human-readable risk summary.

    Args:
        risk_result (dict): Result from risk_scoring_algorithm

    Returns:
        str: Summary text
    """
    total_score = risk_result["total_risk_score"]
    risk_level = risk_result["risk_level"]
    top_risks = get_top_risk_categories(risk_result["category_breakdown"])

    summary = f"Overall Risk: {risk_level} (Score: {total_score}/100)\n\n"

    if top_risks:
        summary += "Top Risk Categories:\n"
        for i, (category, score) in enumerate(top_risks, 1):
            summary += f"{i}. {category}: {score}/5\n"
    else:
        summary += "No significant risks detected."

    return summary


# ============================================================================
# RULE-BASED RISK ENRICHMENT FOR INTENT MINING
# ============================================================================
"""
Rule-Based Risk Enrichment Model
=================================
Enriches LLM-generated risk scores with deterministic rule-based analysis
at the clause/obligation/right level.

Factors:
1. Clause Strength - Language severity (shall/must vs may/reasonable)
2. Party Bias - One-sided vs mutual obligations
3. Missing Safeguards - Liability caps, notice periods, cure provisions
4. Temporal Risk - Tight deadlines, perpetual obligations
5. Financial Exposure - Payment obligations, penalties

Formula:
Final Risk = Base Risk × Clause Strength × Party Bias × Missing Safeguards × Temporal Factor
"""

from typing import Dict, List, Tuple


class ClauseRiskEnricher:
    """Enriches LLM-generated risk scores with rule-based analysis"""

    # Language severity indicators
    STRONG_LANGUAGE = {
        "shall": 1.2,
        "must": 1.2,
        "required": 1.15,
        "mandatory": 1.15,
        "irrevocable": 1.3,
        "unlimited": 1.25,
        "perpetual": 1.25,
        "unconditional": 1.2,
        "absolute": 1.2,
        "solely": 1.15,
        "exclusively": 1.15,
    }

    WEAK_LANGUAGE = {
        "may": 0.85,
        "can": 0.85,
        "reasonable": 0.8,
        "best efforts": 0.75,
        "commercially reasonable": 0.8,
        "subject to": 0.85,
        "unless": 0.9,
        "except": 0.9,
        "provided that": 0.9,
    }

    # Party bias indicators
    ONE_SIDED_PATTERNS = [
        r"indemnify\s+(?:the\s+)?company",
        r"hold\s+(?:the\s+)?company\s+harmless",
        r"defend\s+(?:the\s+)?company",
        r"at\s+(?:the\s+)?(?:vendor|supplier|contractor)(?:'s|\s+)(?:sole\s+)?(?:cost|expense)",
        r"waive(?:s)?\s+(?:all\s+)?(?:claims|rights)\s+against\s+company",
    ]

    MUTUAL_PATTERNS = [
        r"mutual(?:ly)?\s+(?:agree|indemnif)",
        r"both\s+parties",
        r"each\s+party",
        r"reciprocal",
    ]

    # Safeguard patterns by intent type
    SAFEGUARDS = {
        "Liability": {
            "required": ["cap", "limit", "aggregate", "maximum"],
            "multiplier": 1.3,
        },
        "Termination": {
            "required": ["notice", "cure period", "days"],
            "multiplier": 1.2,
        },
        "Payment": {
            "required": ["invoice", "dispute", "written notice"],
            "multiplier": 1.15,
        },
        "Confidentiality": {
            "required": ["term", "duration", "return", "destroy"],
            "multiplier": 1.1,
        },
        "Indemnification": {
            "required": ["notice", "control", "settlement"],
            "multiplier": 1.25,
        },
    }

    def __init__(self):
        self.debug = False

    def enrich_risk(
        self,
        clause_text: str,
        intent_name: str,
        party: str,
        base_risk: float = 0.5,
        action: str = None,
        deadline: str = None,
    ) -> Dict:
        """
        Calculate enriched risk score with explainable factors.

        Args:
            clause_text: Full clause text
            intent_name: Legal intent (e.g., "Liability Limitation")
            party: YOUR_COMPANY, COUNTERPARTY, or BOTH
            base_risk: LLM-generated base risk (0-1)
            action: Obligation action text (if applicable)
            deadline: Deadline text (if applicable)

        Returns:
            {
                'final_risk': 0.85,
                'base_risk': 0.5,
                'clause_strength': 1.2,
                'party_bias': 1.3,
                'missing_safeguards': 1.15,
                'temporal_factor': 1.1,
                'explanation': "High risk due to...",
                'risk_factors': [...],
                'severity': 'HIGH'
            }
        """

        # Calculate individual factors
        strength_score, strength_factors = self._analyze_clause_strength(clause_text, action)
        bias_score, bias_factors = self._analyze_party_bias(clause_text, party)
        safeguard_score, safeguard_factors = self._analyze_missing_safeguards(
            clause_text, intent_name
        )
        temporal_score, temporal_factors = self._analyze_temporal_risk(clause_text, deadline)
        financial_score, financial_factors = self._analyze_financial_exposure(
            clause_text, intent_name
        )

        # Combined risk calculation
        final_risk = (
            base_risk
            * strength_score
            * bias_score
            * safeguard_score
            * temporal_score
            * financial_score
        )

        # Normalize to 0-1 range
        final_risk = min(max(final_risk, 0.0), 1.0)

        # Determine severity
        if final_risk >= 0.7:
            severity = "HIGH"
        elif final_risk >= 0.4:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        # Compile all risk factors
        all_factors = (
            strength_factors
            + bias_factors
            + safeguard_factors
            + temporal_factors
            + financial_factors
        )

        # Generate explanation
        explanation = self._generate_explanation(final_risk, base_risk, all_factors, severity)

        return {
            "final_risk": round(final_risk, 3),
            "base_risk": round(base_risk, 3),
            "clause_strength": round(strength_score, 3),
            "party_bias": round(bias_score, 3),
            "missing_safeguards": round(safeguard_score, 3),
            "temporal_factor": round(temporal_score, 3),
            "financial_factor": round(financial_score, 3),
            "explanation": explanation,
            "risk_factors": all_factors,
            "severity": severity,
        }

    def _analyze_clause_strength(self, text: str, action: str = None) -> Tuple[float, List[str]]:
        """Analyze language severity"""
        if not text:
            return 1.0, []

        combined_text = f"{text} {action or ''}".lower()
        strength = 1.0
        factors = []

        # Check for strong language
        for word, multiplier in self.STRONG_LANGUAGE.items():
            if word in combined_text:
                strength *= multiplier
                factors.append(f"Strong language: '{word}' (+{int((multiplier-1)*100)}% risk)")

        # Check for weak language
        for phrase, multiplier in self.WEAK_LANGUAGE.items():
            if phrase in combined_text:
                strength *= multiplier
                factors.append(f"Weak language: '{phrase}' ({int((1-multiplier)*100)}% reduction)")

        # Cap strength at reasonable bounds
        strength = min(max(strength, 0.5), 1.8)
        return strength, factors

    def _analyze_party_bias(self, text: str, party: str) -> Tuple[float, List[str]]:
        """Detect one-sided vs mutual obligations"""
        if not text:
            return 1.0, []

        text_lower = text.lower()
        bias = 1.0
        factors = []

        # Check for one-sided obligations
        one_sided_count = sum(
            1 for pattern in self.ONE_SIDED_PATTERNS if re.search(pattern, text_lower)
        )

        # Check for mutual obligations
        mutual_count = sum(
            1 for pattern in self.MUTUAL_PATTERNS if re.search(pattern, text_lower)
        )

        if one_sided_count > mutual_count:
            if party == "YOUR_COMPANY":
                bias = 1.3
                factors.append("One-sided obligation favoring counterparty (+30% risk)")
            else:
                bias = 0.8
                factors.append("One-sided obligation favoring your company (-20% risk)")
        elif mutual_count > 0:
            bias = 0.9
            factors.append("Mutual/balanced obligation (-10% risk)")

        return bias, factors

    def _analyze_missing_safeguards(self, text: str, intent_name: str) -> Tuple[float, List[str]]:
        """Check for missing protective clauses"""
        if not text or not intent_name:
            return 1.0, []

        text_lower = text.lower()
        safeguard_multiplier = 1.0
        factors = []

        for key, config in self.SAFEGUARDS.items():
            if key.lower() in intent_name.lower():
                required_terms = config["required"]
                base_multiplier = config["multiplier"]

                missing_count = 0
                missing_terms = []

                for term in required_terms:
                    if term not in text_lower:
                        missing_count += 1
                        missing_terms.append(term)

                if missing_count > 0:
                    ratio = missing_count / len(required_terms)
                    safeguard_multiplier = 1.0 + (base_multiplier - 1.0) * ratio
                    factors.append(
                        f"Missing safeguards: {', '.join(missing_terms)} "
                        f"(+{int((safeguard_multiplier-1)*100)}% risk)"
                    )
                    break

        return safeguard_multiplier, factors

    def _analyze_temporal_risk(self, text: str, deadline: str = None) -> Tuple[float, List[str]]:
        """Analyze time-based risk factors"""
        if not text and not deadline:
            return 1.0, []

        combined_text = f"{text} {deadline or ''}".lower()
        temporal_multiplier = 1.0
        factors = []

        # Check for immediate/urgent deadlines
        if any(word in combined_text for word in ["immediately", "forthwith", "without delay"]):
            temporal_multiplier = 1.2
            factors.append("Immediate deadline required (+20% risk)")

        # Extract numeric deadlines
        deadline_match = re.search(r"(?:within\s+)?(\d+)\s+(?:business\s+)?days?", combined_text)
        if deadline_match:
            days = int(deadline_match.group(1))
            if days <= 5:
                temporal_multiplier = 1.15
                factors.append(f"Tight deadline ({days} days) (+15% risk)")
            elif days <= 15:
                temporal_multiplier = 1.05
                factors.append(f"Moderate deadline ({days} days) (+5% risk)")

        # Check for perpetual obligations
        if any(word in combined_text for word in ["perpetual", "indefinite", "in perpetuity"]):
            temporal_multiplier *= 1.2
            factors.append("Perpetual obligation (+20% risk)")

        return temporal_multiplier, factors

    def _analyze_financial_exposure(self, text: str, intent_name: str) -> Tuple[float, List[str]]:
        """Analyze financial risk exposure"""
        if not text:
            return 1.0, []

        text_lower = text.lower()
        financial_multiplier = 1.0
        factors = []

        if any(
            keyword in intent_name.lower()
            for keyword in ["payment", "fee", "penalty", "damages", "indemnif", "liability"]
        ):
            if "unlimited" in text_lower or "without limit" in text_lower:
                financial_multiplier = 1.4
                factors.append("Unlimited financial exposure (+40% risk)")
            elif any(word in text_lower for word in ["penalty", "liquidated damages", "fine"]):
                financial_multiplier = 1.25
                factors.append("Financial penalties specified (+25% risk)")
            elif any(word in text_lower for word in ["cap", "limit", "maximum", "not exceed"]):
                financial_multiplier = 0.85
                factors.append("Financial liability capped (-15% risk)")

        return financial_multiplier, factors

    def _generate_explanation(
        self, final_risk: float, base_risk: float, factors: List[str], severity: str
    ) -> str:
        """Generate human-readable risk explanation"""

        if not factors:
            return f"{severity} risk based on AI analysis (score: {final_risk:.2f})"

        risk_change = final_risk - base_risk
        direction = "increased" if risk_change > 0 else "decreased"
        change_pct = abs(risk_change) * 100

        explanation = f"{severity} risk (score: {final_risk:.2f}). "
        explanation += f"Rule-based analysis {direction} risk by {change_pct:.0f}% from base. "

        if len(factors) > 0:
            explanation += f"Key factors: {'; '.join(factors[:3])}"

        return explanation


# Global instance for clause-level risk enrichment
clause_risk_enricher = ClauseRiskEnricher()
