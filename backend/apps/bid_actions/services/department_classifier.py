"""
Department Classification Service
Hybrid rule-based + keyword matching for mega EPC projects
"""
import re
from typing import Dict, List


# Keywords mapped to departments for construction/infrastructure projects
DEPARTMENT_KEYWORDS = {
    'Civil': [
        'piling', 'foundation', 'viaduct', 'tunneling', 'tunnel', 'concrete',
        'station box', 'retaining wall', 'earthwork', 'excavation',
        'soil investigation', 'geotechnical', 'structural', 'rcc', 'pcc',
        'masonry', 'formwork', 'shuttering', 'reinforcement', 'rebar'
    ],
    'Mechanical': [
        'hvac', 'elevator', 'lift', 'escalator', 'rolling stock', 'ventilation',
        'air conditioning', 'chiller', 'boiler', 'pump', 'compressor',
        'diesel generator', 'dg set', 'mechanical equipment', 'piping'
    ],
    'Electrical': [
        'traction', 'substation', 'transformer', 'cable tray', 'cable laying',
        'power distribution', 'switchgear', 'panel', 'lighting', 'electrical',
        'hv cable', 'lv cable', 'earthing', 'grounding', 'ups', 'inverter'
    ],
    'MEP': [
        'fire fighting', 'sprinkler', 'fire alarm', 'plumbing', 'sanitary',
        'water supply', 'drainage', 'sewage', 'bms', 'building management',
        'scada', 'ibms', 'fire hydrant', 'fire pump'
    ],
    'Signaling': [
        'signaling', 'atc', 'telecom', 'fiber', 'fiber optic', 'communication',
        'train control', 'interlocking', 'track circuit', 'axle counter'
    ],
    'Planning': [
        'schedule', 'primavera', 'p6', 'baseline', 'critical path', 'cpm',
        'project plan', 'timeline', 'milestone', 'gantt', 'pert'
    ],
    'Procurement': [
        'procurement', 'vendor', 'supplier', 'purchase', 'material',
        'long lead', 'imported equipment', 'equipment procurement',
        'tender', 'quotation', 'rfq', 'bid evaluation'
    ],
    'Finance': [
        'bank guarantee', 'bg', 'advance payment', 'payment terms', 'cashflow',
        'retention money', 'mobilization advance', 'financial', 'costing',
        'budget', 'invoice', 'billing', 'price escalation'
    ],
    'Legal': [
        'liquidated damages', 'ld', 'penalty', 'arbitration', 'fidic',
        'contract', 'clause', 'indemnity', 'liability', 'force majeure',
        'termination', 'breach', 'dispute', 'legal'
    ],
    'HSE': [
        'safety', 'health', 'environment', 'hse', 'ehs', 'safety audit',
        'method statement', 'risk assessment', 'permit to work', 'ptw',
        'personal protective equipment', 'ppe', 'accident', 'incident'
    ],
    'QA/QC': [
        'quality', 'inspection', 'test', 'itp', 'inspection test plan',
        'qa', 'qc', 'quality assurance', 'quality control', 'testing',
        'acceptance', 'certification', 'iso', 'standards'
    ],
}


def classify_department(text: str, confidence_threshold: float = 0.3) -> str:
    """
    Classify text into a department using keyword matching

    Args:
        text: Text to classify (clause, BOQ item, etc.)
        confidence_threshold: Minimum confidence to return match

    Returns:
        Department name (defaults to 'Civil' if no match)
    """
    if not text:
        return 'Civil'

    text_lower = text.lower()

    # Score each department
    scores: Dict[str, int] = {}

    for dept, keywords in DEPARTMENT_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            # Count occurrences of each keyword
            pattern = r'\b' + re.escape(keyword) + r'\b'
            matches = len(re.findall(pattern, text_lower))
            score += matches

        if score > 0:
            scores[dept] = score

    # Return department with highest score
    if scores:
        best_dept = max(scores.items(), key=lambda x: x[1])
        return best_dept[0]

    # Default fallback
    return 'Civil'


def classify_by_category(category: str) -> str:
    """
    Map BOQ category codes to departments

    Args:
        category: BOQ category (e.g., 'CIVIL', 'MECHANICAL')

    Returns:
        Department name
    """
    category_map = {
        'CIVIL': 'Civil',
        'MECHANICAL': 'Mechanical',
        'ELECTRICAL': 'Electrical',
        'MEP': 'MEP',
        'PLUMBING': 'MEP',
        'HVAC': 'Mechanical',
        'SIGNALING': 'Signaling',
        'TELECOM': 'Signaling',
        'OTHER': 'Civil',
    }

    return category_map.get(category.upper(), 'Civil')


def classify_risk_type(risk_type: str) -> str:
    """
    Map risk types to departments

    Args:
        risk_type: Risk category

    Returns:
        Department name
    """
    risk_map = {
        'UNLIMITED_LIABILITY': 'Legal',
        'HIGH_LD': 'Legal',
        'TERMINATION': 'Legal',
        'PAYMENT_TERMS': 'Finance',
        'PRICE_ESCALATION': 'Finance',
        'FORCE_MAJEURE': 'Legal',
        'INDEMNITY': 'Legal',
        'INSURANCE': 'HSE',
        'SAFETY': 'HSE',
        'ENVIRONMENTAL': 'HSE',
        'TECHNICAL': 'QA/QC',
        'QUALITY': 'QA/QC',
    }

    return risk_map.get(risk_type.upper(), 'Legal')


def get_department_keywords() -> Dict[str, List[str]]:
    """Return all department keywords for reference"""
    return DEPARTMENT_KEYWORDS.copy()
