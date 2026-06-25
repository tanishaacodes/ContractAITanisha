"""
Legal Explainability Engine
===========================
Provides court-safe, legally defensible explanations for clause risks.
Generates:
- Legal doctrine identification
- Court reasoning patterns
- Litigation risk assessment
- Judicial treatment predictions
"""

import json
import re
from typing import Dict, Any, Optional
import requests
from django.conf import settings


# Legal doctrines and their descriptions
LEGAL_DOCTRINES = {
    'UNCONSCIONABILITY': {
        'name': 'Unconscionability',
        'description': 'A contract or clause is so one-sided that it shocks the conscience of the court.',
        'elements': ['Procedural unfairness', 'Substantive unfairness', 'Unequal bargaining power'],
        'jurisdictions': ['Common Law', 'US', 'UK', 'Canada', 'Australia']
    },
    'PENALTY_DOCTRINE': {
        'name': 'Penalty Doctrine',
        'description': 'Clauses that impose penalties disproportionate to actual damages are unenforceable.',
        'elements': ['Disproportionate to likely loss', 'Punitive rather than compensatory'],
        'jurisdictions': ['UK', 'Common Law', 'Australia']
    },
    'RESTRAINT_OF_TRADE': {
        'name': 'Restraint of Trade',
        'description': 'Restrictions on a party\'s ability to conduct business must be reasonable.',
        'elements': ['Unreasonable scope', 'Unreasonable duration', 'Unreasonable geography'],
        'jurisdictions': ['Common Law', 'US', 'UK', 'EU']
    },
    'GOOD_FAITH': {
        'name': 'Implied Duty of Good Faith',
        'description': 'Parties must act honestly and fairly in performing contractual obligations.',
        'elements': ['Honesty in performance', 'Fair dealing', 'No abuse of discretion'],
        'jurisdictions': ['US', 'Civil Law', 'Canada', 'Australia']
    },
    'PUBLIC_POLICY': {
        'name': 'Public Policy',
        'description': 'Clauses that violate fundamental public interests are void.',
        'elements': ['Illegal purpose', 'Harm to third parties', 'Against public interest'],
        'jurisdictions': ['Universal']
    },
    'CONTRA_PROFERENTEM': {
        'name': 'Contra Proferentem',
        'description': 'Ambiguous terms are construed against the party who drafted them.',
        'elements': ['Ambiguity', 'Drafted by one party', 'Unequal bargaining'],
        'jurisdictions': ['Common Law', 'Civil Law']
    },
    'LIQUIDATED_DAMAGES': {
        'name': 'Liquidated Damages',
        'description': 'Pre-agreed damages must be a genuine pre-estimate of loss.',
        'elements': ['Reasonable estimate', 'Difficulty calculating actual damages'],
        'jurisdictions': ['US', 'UK', 'Common Law']
    },
    'LIMITATION_OF_LIABILITY': {
        'name': 'Limitation of Liability',
        'description': 'Limits on liability may be struck down if unreasonable or against policy.',
        'elements': ['Gross negligence exclusion', 'Fraud exclusion', 'Reasonableness test'],
        'jurisdictions': ['Common Law', 'EU', 'US']
    }
}

# Risk keywords mapped to legal doctrines
DOCTRINE_KEYWORDS = {
    'UNCONSCIONABILITY': [
        'sole discretion', 'without limitation', 'any and all', 'unlimited',
        'waive all rights', 'forfeit', 'absolute', 'unilateral'
    ],
    'PENALTY_DOCTRINE': [
        'penalty', 'liquidated damages', 'predetermined damages', 'fixed amount',
        'per day penalty', 'daily penalty'
    ],
    'RESTRAINT_OF_TRADE': [
        'non-compete', 'non-solicitation', 'exclusive', 'worldwide',
        'perpetual', 'indefinite', 'all industries'
    ],
    'GOOD_FAITH': [
        'sole judgment', 'absolute discretion', 'may terminate at will',
        'without cause', 'for any reason'
    ],
    'LIMITATION_OF_LIABILITY': [
        'shall not be liable', 'in no event', 'under no circumstances',
        'maximum liability', 'aggregate liability', 'cap', 'exclude'
    ],
    'LIQUIDATED_DAMAGES': [
        'liquidated damages', 'agreed damages', 'predetermined sum',
        'fixed compensation'
    ]
}


def get_ollama_response(prompt: str, temperature: float = 0.1) -> str:
    """Call Ollama API for LLM responses with low temperature for consistency."""
    ollama_url = getattr(settings, 'OLLAMA_URL', 'http://localhost:11434/api/generate')
    model = getattr(settings, 'OLLAMA_MODEL', 'qwen2.5:0.5b')

    try:
        response = requests.post(
            ollama_url,
            json={
                'model': model,
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': temperature,
                    'num_predict': 1500
                }
            },
            timeout=90
        )

        if response.status_code == 200:
            return response.json().get('response', '')
        return ''
    except Exception as e:
        print(f"[LEGAL_EXPLAINABILITY] Ollama error: {e}")
        return ''


def identify_legal_doctrine(clause_text: str) -> str:
    """
    Identify the primary legal doctrine relevant to a clause.
    Uses keyword matching as a first pass.
    """
    clause_lower = clause_text.lower()
    scores = {}

    for doctrine, keywords in DOCTRINE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in clause_lower)
        if score > 0:
            scores[doctrine] = score

    if scores:
        return max(scores, key=scores.get)

    return 'UNCONSCIONABILITY'  # Default fallback


def get_legal_explainability(
    clause_text: str,
    jurisdiction: str = "Common Law",
    risk_type: str = "LIABILITY"
) -> Dict[str, Any]:
    """
    Generate comprehensive legal explainability for a clause.
    Returns court-safe explanations suitable for legal review.
    """
    # Identify doctrine via keyword matching first
    initial_doctrine = identify_legal_doctrine(clause_text)
    doctrine_info = LEGAL_DOCTRINES.get(initial_doctrine, LEGAL_DOCTRINES['UNCONSCIONABILITY'])

    # Build LLM prompt for detailed legal analysis
    prompt = f"""You are a senior commercial court judge and contract law expert.

Clause under review:
"{clause_text}"

Jurisdiction: {jurisdiction}

Analyze this clause from a legal enforceability perspective. Respond in JSON:
{{
    "doctrine": "<primary legal doctrine at issue>",
    "court_reasoning": "<2-3 sentences explaining why courts might modify or reject this clause>",
    "litigation_risk": "<one of: Very High, High, Moderate, Low>",
    "judicial_treatment": "<how courts typically handle such clauses>",
    "enforceability_issues": ["<issue 1>", "<issue 2>"],
    "recommended_revision": "<specific revision to improve enforceability>"
}}

Focus on legal reasoning patterns, not specific case citations. Be concise and legally precise.
Respond ONLY with valid JSON."""

    response = get_ollama_response(prompt)

    try:
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            result = json.loads(json_match.group())
            return {
                'doctrine': result.get('doctrine', doctrine_info['name']),
                'doctrine_description': doctrine_info['description'],
                'court_reasoning': result.get('court_reasoning',
                    f"Courts have historically scrutinized {doctrine_info['name'].lower()} provisions. "
                    f"This clause may face challenges based on {', '.join(doctrine_info['elements'][:2])}."),
                'litigation_risk': result.get('litigation_risk', 'Moderate'),
                'judicial_treatment': result.get('judicial_treatment',
                    f"Courts typically require such clauses to pass a reasonableness test under {jurisdiction} law."),
                'enforceability_issues': result.get('enforceability_issues', doctrine_info['elements'][:2]),
                'recommended_revision': result.get('recommended_revision', '')
            }
    except (json.JSONDecodeError, ValueError) as e:
        print(f"[LEGAL_EXPLAINABILITY] JSON parse error: {e}")

    # Fallback to rule-based explanation
    return generate_fallback_explanation(clause_text, doctrine_info, jurisdiction)


def generate_fallback_explanation(
    clause_text: str,
    doctrine_info: Dict,
    jurisdiction: str
) -> Dict[str, Any]:
    """
    Generate fallback legal explanation when LLM is unavailable.
    Uses rule-based analysis.
    """
    clause_lower = clause_text.lower()

    # Detect specific issues
    issues = []

    if 'unlimited' in clause_lower or 'any and all' in clause_lower:
        issues.append("Unlimited scope may be deemed unreasonable")
    if 'sole discretion' in clause_lower:
        issues.append("Sole discretion clauses may violate good faith duties")
    if 'perpetual' in clause_lower or 'indefinite' in clause_lower:
        issues.append("Perpetual obligations may be unenforceable")
    if 'waive' in clause_lower:
        issues.append("Waiver provisions require clear and knowing consent")
    if 'no liability' in clause_lower or 'not liable' in clause_lower:
        issues.append("Broad liability exclusions may be struck down")

    if not issues:
        issues = doctrine_info['elements'][:2]

    # Determine litigation risk
    high_risk_count = sum([
        'unlimited' in clause_lower,
        'sole discretion' in clause_lower,
        'any and all' in clause_lower,
        'perpetual' in clause_lower,
        'no liability' in clause_lower
    ])

    if high_risk_count >= 3:
        litigation_risk = "Very High"
    elif high_risk_count >= 2:
        litigation_risk = "High"
    elif high_risk_count >= 1:
        litigation_risk = "Moderate"
    else:
        litigation_risk = "Low"

    return {
        'doctrine': doctrine_info['name'],
        'doctrine_description': doctrine_info['description'],
        'court_reasoning': (
            f"Under {jurisdiction} principles, courts scrutinize clauses that appear "
            f"one-sided or unconscionable. This clause implicates the doctrine of "
            f"{doctrine_info['name']}, which requires {doctrine_info['elements'][0].lower()}."
        ),
        'litigation_risk': litigation_risk,
        'judicial_treatment': (
            f"Courts in {jurisdiction} jurisdictions typically modify or sever "
            f"problematic provisions rather than void entire contracts. This clause "
            f"would likely be subject to a reasonableness inquiry."
        ),
        'enforceability_issues': issues,
        'recommended_revision': (
            f"Consider adding protective language such as caps, mutual obligations, "
            f"or reasonableness qualifiers to improve enforceability."
        )
    }


def get_jurisdiction_specific_guidance(
    clause_text: str,
    jurisdiction: str
) -> Dict[str, Any]:
    """
    Provide jurisdiction-specific legal guidance.
    """
    jurisdiction_rules = {
        'US': {
            'key_statutes': ['UCC', 'Restatement (Second) of Contracts'],
            'standard': 'Reasonableness and public policy',
            'notable_approach': 'Courts balance freedom of contract against fairness'
        },
        'UK': {
            'key_statutes': ['UCTA 1977', 'Consumer Rights Act 2015'],
            'standard': 'Reasonableness test under UCTA',
            'notable_approach': 'Strong protection against unfair terms in B2C contracts'
        },
        'EU': {
            'key_statutes': ['Unfair Contract Terms Directive', 'GDPR'],
            'standard': 'Good faith and significant imbalance test',
            'notable_approach': 'Pro-consumer interpretation mandated'
        },
        'Common Law': {
            'key_statutes': ['Common law principles'],
            'standard': 'Unconscionability and public policy',
            'notable_approach': 'Case-by-case analysis of fairness'
        },
        'UAE': {
            'key_statutes': ['UAE Civil Code'],
            'standard': 'Good faith (Article 246)',
            'notable_approach': 'Sharia principles may influence interpretation'
        }
    }

    guidance = jurisdiction_rules.get(jurisdiction, jurisdiction_rules['Common Law'])

    return {
        'jurisdiction': jurisdiction,
        'applicable_law': guidance['key_statutes'],
        'legal_standard': guidance['standard'],
        'judicial_approach': guidance['notable_approach'],
        'compliance_note': (
            f"Ensure clause complies with {', '.join(guidance['key_statutes'])} "
            f"under the {guidance['standard']} standard."
        )
    }


def generate_full_legal_analysis(
    clause_text: str,
    jurisdiction: str = "Common Law",
    risk_type: str = "LIABILITY"
) -> Dict[str, Any]:
    """
    Generate complete legal analysis combining:
    - Legal doctrine identification
    - Court reasoning
    - Litigation risk assessment
    - Jurisdiction-specific guidance
    """
    # Get core legal explainability
    legal_analysis = get_legal_explainability(clause_text, jurisdiction, risk_type)

    # Add jurisdiction-specific guidance
    jurisdiction_guidance = get_jurisdiction_specific_guidance(clause_text, jurisdiction)

    return {
        **legal_analysis,
        'jurisdiction_guidance': jurisdiction_guidance,
        'analysis_type': 'Legal Explainability Analysis',
        'disclaimer': (
            'This analysis is provided for informational purposes and does not '
            'constitute legal advice. Consult qualified legal counsel for specific matters.'
        )
    }
