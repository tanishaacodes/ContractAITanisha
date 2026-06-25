"""
Legal Contract Extraction Prompt Templates

Structured prompts for extracting legal intelligence from contracts.
Uses Chain of Verification style to ensure accuracy and reduce hallucinations.
"""


def get_extraction_prompt(context: str) -> str:
    """
    Generate legal extraction prompt with contract context.

    This prompt forces the LLM to:
    1. Act as a legal expert
    2. Extract specific clauses with precision
    3. Return machine-readable JSON
    4. Indicate when information is not found

    Args:
        context: Relevant contract text (from RAG retrieval)

    Returns:
        Formatted prompt string
    """
    prompt = f"""[INST] <<SYS>>
You are an expert Legal Counsel AI specialized in contract analysis. Your task is to extract specific legal clauses from the provided contract text.

IMPORTANT INSTRUCTIONS:
1. Return ONLY valid JSON - no explanations, no markdown
2. If a clause is not found, return "Not specified"
3. Be precise and concise in summaries
4. Do not hallucinate or infer information not present in the text
5. Base all extractions on the CONTRACT CONTEXT below
<</SYS>>

### CONTRACT CONTEXT:
{context}

### EXTRACTION TASK:
Extract the following information and summarize each concisely:

1. **party_names**: Identify all entities entering the agreement (list full legal names)
2. **termination_clause**: Summary of how and when the contract can be ended
3. **liability_limitation**: Limits on damages, caps, or responsibility disclaimers
4. **governing_law**: Which jurisdiction's laws apply to this contract
5. **confidentiality**: Obligations regarding sensitive information (duration, scope)
6. **payment_terms**: Payment schedule, amounts, and conditions
7. **contract_duration**: Start date, end date, or term length
8. **arbitration**: Whether dispute resolution includes arbitration
9. **indemnification**: Indemnification obligations and scope
10. **force_majeure**: Force majeure provisions

### OUTPUT FORMAT (JSON ONLY):
{{
  "parties": "Party A, Party B",
  "termination": {{
    "summary": "Either party may terminate with 30 days written notice",
    "notice_period": "30 days"
  }},
  "liability": "Liability capped at total fees paid in preceding 12 months",
  "jurisdiction": "State of Delaware, USA",
  "confidentiality_duration": "5 years from contract termination",
  "payment_terms": "NET 30 upon receipt of invoice",
  "contract_duration": "2 years from effective date (January 1, 2024 to December 31, 2025)",
  "has_arbitration": true,
  "arbitration_details": "Binding arbitration under AAA rules",
  "indemnification": "Mutual indemnification for third-party claims",
  "force_majeure": "Excuses performance during acts of God, war, pandemic"
}}

Return ONLY the JSON object above with your extracted data. Do not include any explanations.
[/INST]"""

    return prompt


def get_qwen_extraction_prompt(context: str) -> str:
    """
    Qwen-optimized extraction prompt.

    Qwen models work better with more structured instructions.

    Args:
        context: Contract text

    Returns:
        Qwen-formatted prompt
    """
    prompt = f"""You are a legal contract analyzer. Extract key information from the contract below.

CONTRACT TEXT:
{context}

TASK:
Extract these details in JSON format:
- parties: List of contracting parties
- termination: How contract can be ended
- liability: Liability limitations
- jurisdiction: Governing law
- confidentiality: Confidentiality terms
- payment_terms: Payment details
- duration: Contract term
- arbitration: Dispute resolution method

If any field is not found, write "Not specified".

OUTPUT (JSON only):"""

    return prompt


def get_clause_verification_prompt(clause_data: dict, original_text: str) -> str:
    """
    Verification prompt to check if extracted clauses are accurate.

    This implements Chain of Verification to reduce hallucinations.

    Args:
        clause_data: Previously extracted clause data
        original_text: Original contract text

    Returns:
        Verification prompt
    """
    prompt = f"""You are a legal verification expert. Review the extracted contract data below and verify its accuracy.

EXTRACTED DATA:
{clause_data}

ORIGINAL CONTRACT:
{original_text[:3000]}

TASK:
For each extracted field, verify:
1. Is the information actually present in the contract?
2. Is the summary accurate?
3. Are there any hallucinations or incorrect inferences?

Return a JSON object with corrections:
{{
  "verified": true/false,
  "corrections": {{
    "field_name": "corrected value or reason for error"
  }},
  "confidence_score": 0.0 to 1.0
}}

OUTPUT (JSON only):"""

    return prompt


def get_risk_assessment_prompt(clause_text: str, clause_type: str) -> str:
    """
    Prompt for assessing risk in a specific clause.

    Args:
        clause_text: Text of the clause
        clause_type: Type of clause (e.g., "Termination", "Liability")

    Returns:
        Risk assessment prompt
    """
    prompt = f"""You are a legal risk analyst. Assess the risk level of this contract clause.

CLAUSE TYPE: {clause_type}

CLAUSE TEXT:
{clause_text}

TASK:
Analyze the clause and provide:
1. Risk level (LOW, MEDIUM, HIGH, CRITICAL)
2. Risk factors (list specific concerns)
3. Recommendation (how to mitigate risk)
4. Likelihood score (1-5, probability of risk materializing)
5. Impact score (1-5, severity if risk occurs)

OUTPUT (JSON only):
{{
  "risk_level": "MEDIUM",
  "risk_score": 0.65,
  "risk_factors": [
    "Unilateral termination without cause",
    "Short notice period"
  ],
  "recommendation": "Negotiate 60-day notice period and add cause requirement",
  "likelihood_score": 3,
  "impact_score": 4,
  "rationale": "Brief explanation of risk assessment"
}}

OUTPUT (JSON only):"""

    return prompt


def get_compliance_check_prompt(contract_text: str, framework: str) -> str:
    """
    Prompt for checking compliance with specific frameworks (GDPR, SOX, etc).

    Args:
        contract_text: Contract text
        framework: Compliance framework (e.g., "GDPR", "SOX", "HIPAA")

    Returns:
        Compliance check prompt
    """
    framework_requirements = {
        "GDPR": [
            "Lawful basis for data processing (Article 6)",
            "Data subject rights (Article 15-22)",
            "Data retention and deletion",
            "Data breach notification",
            "Cross-border data transfer safeguards"
        ],
        "SOX": [
            "Financial reporting controls",
            "Audit trail requirements",
            "Record retention (7 years)",
            "Internal control certification"
        ],
        "HIPAA": [
            "Protected Health Information (PHI) handling",
            "Business Associate Agreement (BAA)",
            "Breach notification procedures",
            "Security safeguards"
        ],
        "GST": [
            "Tax compliance clauses",
            "Reverse charge mechanism",
            "Place of supply determination",
            "Invoice requirements"
        ]
    }

    requirements = framework_requirements.get(framework, ["General compliance requirements"])

    prompt = f"""You are a compliance auditor. Check if this contract complies with {framework} requirements.

CONTRACT TEXT:
{contract_text[:3000]}

{framework} REQUIREMENTS TO CHECK:
{chr(10).join(f'{i+1}. {req}' for i, req in enumerate(requirements))}

TASK:
For each requirement, determine:
1. Is it addressed in the contract? (COMPLIANT, PARTIAL, NON_COMPLIANT, NOT_APPLICABLE)
2. Specific clause reference (if found)
3. Gap description (if non-compliant)
4. Recommendation for compliance

OUTPUT (JSON only):
{{
  "framework": "{framework}",
  "overall_compliance_score": 0.0 to 1.0,
  "status": "COMPLIANT/PARTIAL/NON_COMPLIANT",
  "requirements": [
    {{
      "requirement": "Requirement name",
      "status": "COMPLIANT",
      "clause_reference": "Section 5.2",
      "gap": "Not specified if compliant",
      "recommendation": "Not specified if compliant",
      "risk_score": 0.0 to 1.0
    }}
  ],
  "critical_violations": 0,
  "executive_summary": "Brief compliance overview"
}}

OUTPUT (JSON only):"""

    return prompt


def get_obligation_extraction_prompt(contract_text: str) -> str:
    """
    Prompt for extracting obligations and rights from contract.

    Args:
        contract_text: Contract text

    Returns:
        Obligation extraction prompt
    """
    prompt = f"""You are a legal obligations analyst. Extract all obligations and rights from this contract.

CONTRACT TEXT:
{contract_text}

TASK:
Identify all:
1. Obligations (what parties MUST do)
2. Rights (what parties MAY do)
3. Responsible party (YOUR_COMPANY, COUNTERPARTY, or BOTH)
4. Conditions and triggers
5. Deadlines or timeframes

OUTPUT (JSON only):
{{
  "obligations": [
    {{
      "party": "YOUR_COMPANY",
      "action": "What must be done",
      "condition": "Under what conditions (if any)",
      "deadline": "When it must be done",
      "priority": "HIGH/MEDIUM/LOW",
      "risk_score": 0.0 to 1.0,
      "clause_reference": "Section/Article reference"
    }}
  ],
  "rights": [
    {{
      "party": "YOUR_COMPANY",
      "entitlement": "What the party may do",
      "trigger": "What triggers this right",
      "risk_score": 0.0 to 1.0,
      "clause_reference": "Section/Article reference"
    }}
  ]
}}

OUTPUT (JSON only):"""

    return prompt
