"""
Exculpatory Clause Pattern Library
Construction-specific patterns for identifying unfair risk allocation
Based on NLP pattern detection approach
"""

EXCULPATORY_PATTERNS = [
    {
        "id": "EXP_01",
        "label": "No Liability Clause",
        "text": "The employer shall not be liable for any loss, damage or delay whatsoever arising from site conditions or unforeseen circumstances.",
        "risk_category": "SITE_CONDITIONS",
        "controlled_by": "employer",
        "explanation": "Employer controls site access and information, but disclaims all liability"
    },
    {
        "id": "EXP_02",
        "label": "Contractor Bears All Risk",
        "text": "All risks arising from site conditions, subsurface conditions, or ground water shall be deemed to have been assumed by the contractor.",
        "risk_category": "SITE_CONDITIONS",
        "controlled_by": "employer",
        "explanation": "Contractor assumes risks they cannot investigate or control"
    },
    {
        "id": "EXP_03",
        "label": "Indemnity Expansion",
        "text": "The contractor shall indemnify and hold harmless the employer against all claims, losses, damages, and expenses arising from the works.",
        "risk_category": "INDEMNITY",
        "controlled_by": "both",
        "explanation": "Broad indemnity clause shifts all liability to contractor"
    },
    {
        "id": "EXP_04",
        "label": "Waiver of Claims",
        "text": "The contractor waives all claims arising from delays, disruptions, or variations caused by the employer or third parties.",
        "risk_category": "DELAY",
        "controlled_by": "employer",
        "explanation": "Contractor waives claims for events outside their control"
    },
    {
        "id": "EXP_05",
        "label": "Statutory Approval Risk Transfer",
        "text": "All statutory approvals, permits, and permissions required shall be the responsibility of the contractor at their own cost and risk.",
        "risk_category": "STATUTORY_APPROVALS",
        "controlled_by": "employer",
        "explanation": "Employer has more influence with authorities but shifts approval risk to contractor"
    },
    {
        "id": "EXP_06",
        "label": "Deemed Site Inspection",
        "text": "The contractor shall be deemed to have inspected the site and satisfied itself as to all matters affecting the execution of the works.",
        "risk_category": "SITE_CONDITIONS",
        "controlled_by": "employer",
        "explanation": "Creates legal fiction that contractor knew about site conditions they couldn't access"
    },
    {
        "id": "EXP_07",
        "label": "No Time Extension",
        "text": "No time extension shall be granted for delays arising from utilities, traffic restrictions, or actions of third parties.",
        "risk_category": "DELAY",
        "controlled_by": "employer",
        "explanation": "Contractor cannot control third-party delays but bears full consequence"
    },
    {
        "id": "EXP_08",
        "label": "Absolute Performance Obligation",
        "text": "The contractor shall complete the works regardless of any difficulties, obstacles, or impediments encountered.",
        "risk_category": "PERFORMANCE",
        "controlled_by": "employer",
        "explanation": "Contractor must perform even when employer-controlled factors prevent completion"
    },
    {
        "id": "EXP_09",
        "label": "Design Risk Transfer",
        "text": "The contractor shall be responsible for all design errors, omissions, or deficiencies, whether in the employer's specifications or not.",
        "risk_category": "DESIGN",
        "controlled_by": "employer",
        "explanation": "Contractor liable for employer's design defects they had no control over"
    },
    {
        "id": "EXP_10",
        "label": "Payment Withholding",
        "text": "The employer may withhold payment for any reason deemed necessary without providing justification or timeline for release.",
        "risk_category": "PAYMENT",
        "controlled_by": "employer",
        "explanation": "Employer has unilateral payment control without accountability"
    },
    {
        "id": "EXP_11",
        "label": "Variation Without Adjustment",
        "text": "The employer reserves the right to vary the works without adjusting the contract price or time.",
        "risk_category": "VARIATION",
        "controlled_by": "employer",
        "explanation": "Employer can change scope without compensating contractor"
    },
    {
        "id": "EXP_12",
        "label": "Force Majeure Exclusion",
        "text": "Events of force majeure shall not entitle the contractor to any extension of time or additional payment.",
        "risk_category": "FORCE_MAJEURE",
        "controlled_by": "neither",
        "explanation": "Contractor bears risk of unforeseeable events beyond anyone's control"
    },
    {
        "id": "EXP_13",
        "label": "Unlimited Warranty",
        "text": "The contractor warrants the works against all defects for the lifetime of the structure, regardless of cause.",
        "risk_category": "WARRANTY",
        "controlled_by": "both",
        "explanation": "Unlimited warranty including defects from employer's design or use"
    },
    {
        "id": "EXP_14",
        "label": "Unilateral Contract Termination",
        "text": "The employer may terminate the contract at any time for convenience without compensation for loss of profit.",
        "risk_category": "TERMINATION",
        "controlled_by": "employer",
        "explanation": "Employer can terminate without contractor recourse"
    },
    {
        "id": "EXP_15",
        "label": "Contractor's Knowledge Presumption",
        "text": "The contractor acknowledges complete knowledge of all local conditions, regulations, and requirements affecting the works.",
        "risk_category": "LOCAL_CONDITIONS",
        "controlled_by": "employer",
        "explanation": "Presumes contractor knowledge of conditions only employer can access or knows"
    }
]

# Risk category mapping for classification
RISK_CATEGORIES = {
    "SITE_CONDITIONS": "Site Conditions",
    "STATUTORY_APPROVALS": "Statutory Approvals",
    "DELAY": "Delay",
    "WORKMANSHIP": "Workmanship",
    "PAYMENT": "Payment",
    "INDEMNITY": "Indemnity",
    "PERFORMANCE": "Performance",
    "DESIGN": "Design",
    "VARIATION": "Variation",
    "FORCE_MAJEURE": "Force Majeure",
    "WARRANTY": "Warranty",
    "TERMINATION": "Termination",
    "LOCAL_CONDITIONS": "Local Conditions"
}

# Keyword patterns for quick classification
EXCULPATORY_KEYWORDS = [
    "shall not be liable",
    "no responsibility",
    "at contractor's risk",
    "indemnify",
    "hold harmless",
    "waives all claims",
    "deemed to have",
    "acknowledges and accepts",
    "all risks shall be borne",
    "no extension of time",
    "no additional payment",
    "without compensation",
    "at their own cost",
    "regardless of",
    "sole responsibility",
    "exclusive risk"
]
