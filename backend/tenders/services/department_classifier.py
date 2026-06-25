"""
Department Classifier — Hybrid Rule + Keyword Engine
Maps tender clauses / BOQ items / risk descriptions to departments.
Uses a tiered approach:
  1. METRO_KEYWORDS exact match (fastest)
  2. BOQ category shortcodes (CIVIL, MEP, ELECTRICAL …)
  3. Risk category shortcodes
  4. Fallback: 'Civil'
"""

# ─── Keyword Map ────────────────────────────────────────────────────────────
METRO_KEYWORDS = {
    'Civil': [
        'piling', 'viaduct', 'tunneling', 'tunnel', 'concrete', 'station box',
        'retaining wall', 'excavation', 'earthwork', 'foundation', 'structure',
        'reinforcement', 'formwork', 'masonry', 'rcc', 'pcc', 'brickwork',
        'plastering', 'waterproofing', 'road', 'pavement', 'drainage', 'culvert',
        'bridge', 'deck slab', 'pile cap', 'footing', 'column', 'beam',
        'shuttering', 'grouting', 'soil investigation', 'geotechnical',
    ],
    'Mechanical': [
        'hvac', 'elevator', 'rolling stock', 'ventilation shaft', 'escalator',
        'lift', 'compressor', 'pump', 'valve', 'chiller', 'ahu', 'fcu',
        'cooling tower', 'boiler', 'ductwork', 'mechanical ventilation',
        'air handling unit', 'fan coil unit', 'pressurization', 'refrigeration',
    ],
    'Electrical': [
        'traction', 'substation', 'transformer', 'cable tray', 'hv cable',
        'lv cable', 'switchgear', 'power distribution', 'earthing', 'lightning',
        'ups', 'generator', 'lighting', 'street lighting', 'busduct',
        'panel board', 'mcc', 'pcc panel', 'vfd', 'power factor',
        'overhead line', 'catenary', 'third rail', 'traction supply',
    ],
    'MEP': [
        'fire fighting', 'sprinkler', 'plumbing', 'bms', 'building management',
        'hydrant', 'fire alarm', 'sanitary', 'sewage', 'water supply',
        'drainage system', 'gas supply', 'lpg', 'mep coordination',
        'pipe work', 'flushing', 'testing and commissioning', 'fcas',
    ],
    'Signaling': [
        'signaling', 'atc', 'telecom fiber', 'cctv', 'scada', 'occ',
        'automatic train control', 'communication system', 'pa system',
        'passenger information', 'ops', 'platform screen door', 'psd',
        'train management', 'interlocking', 'signal',
    ],
    'Planning': [
        'primavera', 'schedule baseline', 'program of works', 'gantt',
        'critical path', 'milestone', 'baseline program', 'resource planning',
        'look ahead', 'master schedule', 'eot', 'extension of time',
        'time impact analysis', 'float analysis', 'pert',
    ],
    'Procurement': [
        'long lead', 'imported equipment', 'procurement schedule',
        'purchase order', 'vendor approval', 'pre-qualification',
        'material approval', 'submittal', 'approved vendor list',
        'subcontractor', 'supply chain', 'logistics', 'customs clearance',
    ],
    'Finance': [
        'bank guarantee', 'advance payment', 'cashflow', 'retention',
        'payment milestone', 'progress payment', 'invoice', 'mobilization',
        'demobilization', 'insurance', 'performance bond', 'warranty bond',
        'letter of credit', 'forex', 'currency risk', 'escalation',
    ],
    'Legal': [
        'liquidated damages', 'arbitration', 'fidic', 'dispute', 'claim',
        'force majeure', 'indemnity', 'liability', 'penalty clause',
        'termination', 'breach', 'warranty', 'defect liability period',
        'dlp', 'governing law', 'jurisdiction', 'ip rights',
        'intellectual property', 'confidentiality', 'unlimited liability',
    ],
    'HSE': [
        'safety audit', 'method statement', 'risk assessment', 'hira',
        'ppe', 'personal protective equipment', 'ohs', 'health and safety',
        'environmental compliance', 'hazmat', 'hazardous material',
        'emergency response', 'evacuation', 'near miss', 'incident report',
        'toolbox talk', 'permit to work', 'hot work', 'excavation permit',
    ],
    'QA/QC': [
        'inspection test plan', 'itp', 'quality assurance', 'quality control',
        'non conformance', 'ncr', 'audit', 'material test report', 'mtr',
        'third party inspection', 'type test', 'factory acceptance test', 'fat',
        'site acceptance test', 'sat', 'calibration', 'certification',
        'iso 9001', 'holdpoint', 'witness point',
    ],
}

# ── BOQ category → department mapping ────────────────────────────────────────
BOQ_CATEGORY_MAP = {
    'CIVIL':       'Civil',
    'MECHANICAL':  'Mechanical',
    'ELECTRICAL':  'Electrical',
    'MEP':         'MEP',
    'PLUMBING':    'MEP',
    'HVAC':        'Mechanical',
    'OTHER':       'Civil',
}

# ── Risk category → department mapping ───────────────────────────────────────
RISK_CATEGORY_MAP = {
    'UNLIMITED_LIABILITY':   'Legal',
    'HIGH_LD':               'Legal',
    'PAYMENT_TERMS':         'Finance',
    'BANK_GUARANTEE':        'Finance',
    'SAFETY':                'HSE',
    'TECHNICAL':             'QA/QC',
    'SCHEDULE':              'Planning',
    'PROCUREMENT':           'Procurement',
    'SCOPE_AMBIGUITY':       'Civil',
    'FORCE_MAJEURE':         'Legal',
    'INDEMNITY':             'Legal',
    'CURRENCY_RISK':         'Finance',
}


def classify_from_text(text: str) -> str:
    """
    Returns department name from free text using keyword matching.
    Falls back to 'Civil' if no match.
    """
    if not text:
        return 'Civil'

    text_lower = text.lower()

    for dept, keywords in METRO_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return dept

    return 'Civil'


def classify_from_boq_category(category: str) -> str:
    """Returns department from BOQ category shortcode."""
    return BOQ_CATEGORY_MAP.get(category.upper(), 'Civil')


def classify_from_risk_category(risk_category: str) -> str:
    """Returns department from risk category enum."""
    return RISK_CATEGORY_MAP.get(risk_category, 'Legal')


def classify(text: str = '', boq_category: str = None,
             risk_category: str = None) -> str:
    """
    Master classifier — prefers explicit category keys,
    falls back to keyword scan.
    """
    if boq_category:
        return classify_from_boq_category(boq_category)
    if risk_category:
        return classify_from_risk_category(risk_category)
    return classify_from_text(text)
