"""
Force Majeure Intelligence Engine — Core Service
=================================================
Orchestrates:
  1. FM Risk Predictor    — Bayesian + clause analysis → risk score
  2. FM Loss Predictor    — Monte Carlo simulation → financial exposure
  3. FM Clause Auditor    — scans contract for FM clause coverage
  4. Auto-Correct Engine  — LLM rewrite of weak/missing FM clauses
  5. War Risk Engine      — geopolitical war risk analysis
  6. FM Mitigation Engine — recommends contractual protections
"""
import re
import math
import random
import logging
import requests
from typing import Dict, List, Optional, Tuple

from django.conf import settings

from .bayesian_engine import (
    get_fm_bayesian_engine,
    compute_war_risk_score,
    LAYER4_OUTCOMES,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

OLLAMA_BASE_URL = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')

# 22 FM event categories (expanded with 8 additional war-specific events)
FM_EVENT_CATEGORIES = [
    # Original 14 categories
    'war',
    'terrorism',
    'cyber_warfare',
    'trade_sanctions',
    'embargo',
    'pandemic',
    'epidemic',
    'government_lockdown',
    'supply_chain_disruption',
    'port_closure',
    'airspace_closure',
    'energy_shortages',
    'commodity_shock',
    'satellite_disruption',
    # 8 Additional war-specific categories
    'civil_war',
    'military_invasion',
    'border_conflict',
    'military_coup',
    'drone_strikes',
    'naval_blockade',
    'government_expropriation',
    'martial_law',
]

# Keywords for each FM event category (clause scanner)
FM_KEYWORDS: Dict[str, List[str]] = {
    'war': ['war', 'armed conflict', 'military', 'hostilities', 'invasion', 'insurrection', 'rebellion', 'acts of hostilities'],
    'terrorism': ['terrorism', 'terrorist', 'terrorist attack', 'act of terrorism', 'political violence'],
    'cyber_warfare': ['cyber', 'cyberattack', 'hacking', 'ransomware', 'data breach', 'cyber warfare', 'cyber attack', 'infrastructure disruption'],
    'trade_sanctions': ['sanctions', 'trade sanctions', 'economic sanctions', 'export control', 'embargo', 'trade restrictions', 'ofac', 'restricted party'],
    'embargo': ['embargo', 'trade embargo', 'import ban', 'export ban', 'export prohibition', 'import prohibition'],
    'pandemic': ['pandemic', 'global pandemic', 'public health emergency', 'WHO declaration', 'health emergency', 'who-declared'],
    'epidemic': ['epidemic', 'disease outbreak', 'infectious disease', 'quarantine', 'quarantine orders'],
    'government_lockdown': ['lockdown', 'government order', 'government restriction', 'mandatory closure', 'curfew', 'movement restrictions', 'closure orders'],
    'supply_chain_disruption': ['supply chain', 'supply disruption', 'material shortage', 'supplier failure', 'supplier insolvency', 'material shortage'],
    'port_closure': ['port closure', 'port shutdown', 'harbor closure', 'dock closure', 'maritime logistics', 'port', 'harbour'],
    'airspace_closure': ['airspace closure', 'no-fly zone', 'flight ban', 'air traffic', 'aviation authority', 'flight restrictions'],
    'energy_shortages': ['energy shortage', 'power outage', 'blackout', 'fuel shortage', 'electricity shortage', 'power grid', 'energy shortage', 'fuel supply'],
    'commodity_shock': ['commodity', 'commodity price', 'raw material', 'steel price', 'oil price', 'commodity price shock', 'material unavailability', 'input shortage'],
    'satellite_disruption': ['satellite', 'gps disruption', 'communications satellite', 'navigation system', 'satellite disruption', 'critical communications'],
    # 8 Additional war-specific categories
    'civil_war': ['civil war', 'internal conflict', 'internal armed conflict', 'domestic conflict', 'sectarian violence', 'insurgency'],
    'military_invasion': ['military invasion', 'foreign invasion', 'armed invasion', 'military occupation', 'invasion by foreign forces'],
    'border_conflict': ['border conflict', 'border dispute', 'border skirmish', 'territorial dispute', 'frontier dispute', 'boundary conflict'],
    'military_coup': ['military coup', 'coup d\'état', 'government overthrow', 'military takeover', 'regime change', 'coup attempt'],
    'drone_strikes': ['drone strike', 'drone attack', 'unmanned aerial', 'UAV attack', 'drone warfare', 'aerial bombardment'],
    'naval_blockade': ['naval blockade', 'maritime blockade', 'sea blockade', 'port blockade', 'shipping blockade', 'naval embargo'],
    'government_expropriation': ['expropriation', 'nationalization', 'government seizure', 'confiscation', 'eminent domain', 'compulsory acquisition'],
    'martial_law': ['martial law', 'military rule', 'state of emergency', 'emergency powers', 'military government', 'curfew orders'],
}

# Industry benchmark FM scores (0-1 scale)
BENCHMARK_SCORES = {
    'fidic': 0.88,
    'nec': 0.82,
    'icc': 0.85,
    'world_bank': 0.80,
}

# ---------------------------------------------------------------------------
# 1. FM CLAUSE AUDITOR
# ---------------------------------------------------------------------------

def extract_fm_clause(contract_text: str) -> str:
    """
    Extracts the Force Majeure clause text from contract.
    Looks for common FM clause headings.
    """
    patterns = [
        r'(?:FORCE\s+MAJEURE|Force\s+Majeure)[^\n]*\n((?:(?!\n\d+\.|\nARTICLE|\nCLAUSE|\nSECTION).)+)',
        r'(?:force\s+majeure)[^\n]*\n((?:.|\n){50,2000}?)(?:\n\d+\.|\nArticle|\nClause|$)',
    ]
    for pattern in patterns:
        match = re.search(pattern, contract_text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(0)[:2000].strip()
    # Fallback: look for any sentence containing 'force majeure'
    sentences = re.findall(r'[^.!?]*force\s+majeure[^.!?]*[.!?]', contract_text, re.IGNORECASE)
    return ' '.join(sentences[:10]) if sentences else ''


def audit_fm_clause(contract_text: str, contract_id: str = '', contract_title: str = '') -> Dict:
    """
    Audits the FM clause in a contract against 14 modern FM event categories.
    Returns strength score, covered events, missing events, and status.
    """
    fm_text = extract_fm_clause(contract_text)
    text_to_scan = (fm_text + ' ' + contract_text[:3000]).lower()

    covered = []
    missing = []

    for event_cat, keywords in FM_KEYWORDS.items():
        found = any(kw.lower() in text_to_scan for kw in keywords)
        if found:
            covered.append(event_cat)
        else:
            missing.append(event_cat)

    total = len(FM_EVENT_CATEGORIES)
    strength_score = len(covered) / total if total > 0 else 0.0

    if strength_score >= 0.75:
        status = 'strong'
    elif strength_score >= 0.40:
        status = 'weak'
    else:
        status = 'missing'

    return {
        'contract_id': contract_id,
        'contract_title': contract_title,
        'raw_clause_text': fm_text,
        'status': status,
        'strength_score': round(strength_score, 4),
        'covered_events': covered,
        'missing_events': missing,
        'weak_events': [],
        'benchmark_fidic_score': BENCHMARK_SCORES['fidic'],
        'benchmark_nec_score': BENCHMARK_SCORES['nec'],
        'benchmark_icc_score': BENCHMARK_SCORES['icc'],
    }


# ---------------------------------------------------------------------------
# 2. FM RISK PREDICTOR
# ---------------------------------------------------------------------------

def _build_evidence_from_text(contract_text: str) -> Dict[str, float]:
    """
    Extracts soft evidence probabilities from contract text for root event nodes.
    High-risk keywords bump the prior for the corresponding event.
    """
    text_lower = contract_text.lower()
    evidence = {}

    evidence_map = {
        'war': ['war zone', 'conflict zone', 'military operation', 'armed forces', 'nato'],
        'trade_sanctions': ['sanction', 'embargo', 'export control', 'ofac', 'restricted party'],
        'pandemic': ['pandemic', 'covid', 'public health emergency', 'who declaration'],
        'flood': ['flood', 'storm surge', 'inundation', 'coastal'],
        'hurricane': ['hurricane', 'typhoon', 'cyclone', 'tropical storm'],
        'earthquake': ['earthquake', 'seismic', 'tremor'],
        'energy_crisis': ['energy crisis', 'power shortage', 'blackout', 'fuel crisis'],
        'political_coup': ['coup', 'government overthrow', 'regime change', 'political instability'],
        'cyber_warfare': ['cyberattack', 'ransomware', 'data breach', 'ddos'],
    }

    for node, keywords in evidence_map.items():
        hits = sum(1 for kw in keywords if kw in text_lower)
        if hits > 0:
            boost = min(0.3 * hits, 0.6)
            engine = get_fm_bayesian_engine()
            base = engine.node_probs.get(node, 0.10) if engine.node_probs else 0.10
            evidence[node] = min(base + boost, 0.95)

    return evidence


def predict_fm_risk(
    contract_text: str,
    contract_id: str = '',
    contract_title: str = '',
    contract_value: float = 0.0,
    jurisdiction: str = '',
    industry: str = '',
    manual_evidence: Optional[Dict[str, float]] = None,
) -> Dict:
    """
    Main FM risk prediction function.
    Returns full prediction dict compatible with FMPrediction model.
    """
    engine = get_fm_bayesian_engine()

    # Build evidence from contract text + manual overrides
    evidence = _build_evidence_from_text(contract_text)
    if manual_evidence:
        evidence.update(manual_evidence)

    # Run Bayesian inference
    all_probs = engine.infer(evidence)
    outcomes = {node: all_probs.get(node, 0.0) for node in LAYER4_OUTCOMES}
    top_drivers = engine.get_top_risk_drivers(evidence, top_n=5)
    causal_chain = engine.get_causal_chain('fm_invocation', evidence)
    fm_risk_score = engine.compute_fm_risk_score(evidence)

    # Clause audit
    audit = audit_fm_clause(contract_text, contract_id, contract_title)

    # Monte Carlo loss prediction
    mc = monte_carlo_loss(
        fm_risk_score=fm_risk_score,
        contract_value=contract_value,
        outcomes=outcomes,
    )

    # LLM explanation
    explanation = _generate_fm_explanation(
        fm_risk_score=fm_risk_score,
        top_drivers=top_drivers,
        outcomes=outcomes,
        missing_events=audit['missing_events'],
        contract_title=contract_title,
    )

    # Mitigation suggestions
    mitigations = suggest_mitigations(audit['missing_events'], top_drivers)

    return {
        'contract_id': contract_id,
        'contract_title': contract_title,
        'contract_text': contract_text[:500],
        'fm_risk_score': fm_risk_score,
        'fm_invocation_probability': outcomes.get('fm_invocation', 0.0),
        'project_delay_probability': outcomes.get('project_delay', 0.0),
        'cost_overrun_probability': outcomes.get('cost_overrun', 0.0),
        'contract_suspension_probability': outcomes.get('contract_suspension', 0.0),
        'contract_termination_probability': outcomes.get('contract_termination', 0.0),
        'event_probabilities': {
            k: round(v, 4)
            for k, v in all_probs.items()
            if k in ['war', 'pandemic', 'flood', 'trade_sanctions', 'energy_crisis',
                     'political_coup', 'cyber_warfare', 'earthquake', 'hurricane']
        },
        'expected_loss_usd': mc['expected_loss'],
        'worst_case_loss_usd': mc['worst_case'],
        'p50_loss_usd': mc['p50'],
        'p95_loss_usd': mc['p95'],
        'p99_loss_usd': mc['p99'],
        'bayesian_nodes': {k: round(v, 4) for k, v in all_probs.items()},
        'top_risk_drivers': top_drivers,
        'causal_chain': causal_chain,
        'clause_strength_score': audit['strength_score'],
        'missing_protections': audit['missing_events'],
        'covered_events': audit['covered_events'],
        'explanation': explanation,
        'mitigation_suggestions': mitigations,
        'contract_value': contract_value,
        'jurisdiction': jurisdiction,
        'industry': industry,
    }


# ---------------------------------------------------------------------------
# 3. FM LOSS PREDICTOR (Monte Carlo)
# ---------------------------------------------------------------------------

def monte_carlo_loss(
    fm_risk_score: float,
    contract_value: float,
    outcomes: Dict[str, float],
    iterations: int = 5000,
) -> Dict:
    """
    Monte Carlo simulation of financial loss under Force Majeure events.
    Uses fm_risk_score + contract_value + outcome probabilities as inputs.
    Returns expected_loss, worst_case, p50, p95, p99 in USD.
    """
    if contract_value <= 0:
        contract_value = 1_000_000  # default $1M if not provided

    losses = []
    rng = random.Random(42)

    # Fixed loss magnitude multipliers (fraction of contract value per outcome type)
    # These are financial impact sizes, NOT probabilities
    LOSS_MAGNITUDES = {
        'project_delay':        (0.12, 0.05),   # mean 12%, std 5%
        'cost_overrun':         (0.10, 0.04),   # mean 10%, std 4%
        'contract_suspension':  (0.07, 0.03),   # mean 7%,  std 3%
        'contract_termination': (0.18, 0.06),   # mean 18%, std 6% (highest — full termination)
        'insurance_claim':      (0.05, 0.02),   # mean 5%,  std 2%
        'fm_invocation':        (0.08, 0.03),   # mean 8%,  std 3%
    }

    # Outcome probabilities (trigger chance per iteration) — clamped to [0.05, 0.90]
    trigger_probs = {k: min(0.90, max(0.05, float(v))) for k, v in outcomes.items()}

    for _ in range(iterations):
        total_loss = 0.0
        for outcome, (mean_frac, std_frac) in LOSS_MAGNITUDES.items():
            trigger_p = trigger_probs.get(outcome, 0.10)
            if rng.random() < trigger_p:
                loss = rng.gauss(mean_frac * contract_value, std_frac * contract_value)
                total_loss += max(0, loss)

        # Scale by FM risk score — P95 capped at 75%, P99 at 90% handled by natural distribution
        total_loss = total_loss * fm_risk_score
        total_loss = max(0, min(contract_value * 0.85, total_loss))
        losses.append(total_loss)

    losses.sort()
    n = len(losses)

    return {
        'expected_loss': round(sum(losses) / n, 2),
        'worst_case': round(losses[-1], 2),
        'p50': round(losses[int(0.50 * n)], 2),
        'p95': round(losses[int(0.95 * n)], 2),
        'p99': round(losses[min(int(0.99 * n), n - 1)], 2),
        'iterations': iterations,
        'loss_distribution': [round(losses[min(int(i * n / 20), n - 1)], 2) for i in range(21)],  # 21 points: P0, P5, P10...P95, P100
    }


# ---------------------------------------------------------------------------
# 4. FM AUTO-CORRECT CLAUSE ENGINE
# ---------------------------------------------------------------------------

# Fallback rule-based FM clause generator
def _rule_based_fm_clause(missing_events: List[str], original_clause: str = '') -> str:
    """Generates a modern FM clause covering all 14 event categories."""
    event_descriptions = {
        'war': 'war, armed conflict, military invasion, insurrection, or acts of hostilities',
        'terrorism': 'terrorism, terrorist attacks, or acts of political violence',
        'cyber_warfare': 'cyber warfare, cyber attacks, ransomware, or critical infrastructure disruption',
        'trade_sanctions': 'trade sanctions, export controls, economic sanctions, or government-imposed trade restrictions',
        'embargo': 'trade embargo, import ban, or export prohibition imposed by any government authority',
        'pandemic': 'pandemic, global public health emergency, or WHO-declared international health emergency',
        'epidemic': 'epidemic, disease outbreak, or quarantine orders affecting the performance of the Contract',
        'government_lockdown': 'government-mandated lockdown, mandatory closure orders, or movement restrictions',
        'supply_chain_disruption': 'critical supply chain disruption, supplier insolvency, or material shortage beyond reasonable control',
        'port_closure': 'port closure, harbor shutdown, or disruption to maritime logistics routes',
        'airspace_closure': 'airspace closure, no-fly zone declaration, or aviation authority-imposed flight restrictions',
        'energy_shortages': 'energy shortage, power grid failure, fuel supply disruption, or blackout',
        'commodity_shock': 'extraordinary commodity price shock, raw material unavailability, or critical input shortage',
        'satellite_disruption': 'satellite disruption, GPS signal interference, or loss of critical communications infrastructure',
    }

    # Only use events that are defined in event_descriptions (filter out extended Bayesian events)
    all_events = [event_descriptions[e] for e in FM_EVENT_CATEGORIES if e in event_descriptions]
    events_text = ';\n    '.join(f'({i+1}) {desc}' for i, desc in enumerate(all_events))

    clause = f"""FORCE MAJEURE

1. Definition of Force Majeure
   For the purposes of this Contract, a "Force Majeure Event" means any event or circumstance
   beyond the reasonable control of the affected Party that prevents or delays the performance
   of its obligations, including but not limited to:
   {events_text}.

2. Notice Requirement
   The Party claiming Force Majeure shall notify the other Party in writing within fourteen (14)
   days of the occurrence of the Force Majeure Event, specifying the nature of the event, its
   expected duration, and the obligations affected.

3. Suspension of Obligations
   Upon valid declaration of a Force Majeure Event, the affected Party's obligations shall be
   suspended for the duration of the Force Majeure Event. Time for performance shall be extended
   by an equivalent period.

4. Cost Escalation Protection
   If a Force Majeure Event results in commodity price increases exceeding fifteen percent (15%)
   of the Contract Price, the Parties shall negotiate in good faith to adjust the Contract Price
   through a Change Order mechanism.

5. Alternative Sourcing Obligation
   The affected Party shall use commercially reasonable efforts to mitigate the impact of the
   Force Majeure Event, including identifying alternative suppliers, shipping routes, or
   performance methods.

6. Insurance Trigger
   The Parties acknowledge that Force Majeure Events may trigger applicable insurance policies.
   Each Party shall promptly notify its insurers and cooperate in any insurance claim process.

7. Payment Suspension
   Liquidated damages and penalty provisions shall be suspended during any Force Majeure Event.
   Payments due prior to the Force Majeure Event remain payable.

8. Termination for Extended Force Majeure
   If a Force Majeure Event persists for more than one hundred and eighty (180) consecutive days,
   either Party may terminate this Contract upon thirty (30) days' written notice, without
   liability to the other Party, subject to settlement of amounts already due.

9. War Risk Insurance
   Each Party shall maintain adequate war risk insurance coverage for the duration of this
   Contract where the project location is in a region with elevated geopolitical risk.

10. Governing Standard
    This Force Majeure clause shall be interpreted in accordance with the FIDIC Silver Book
    (2017 Edition) and applicable international arbitration standards."""

    return clause


def auto_correct_fm_clause(
    contract_text: str,
    audit_result: Optional[Dict] = None,
    use_llm: bool = False,  # Changed default to False for stability
) -> Dict:
    """
    Auto-corrects the Force Majeure clause in a contract.
    Returns original clause, corrected clause, and risk reduction estimate.
    """
    try:
        if audit_result is None:
            audit_result = audit_fm_clause(contract_text)

        missing_events = audit_result.get('missing_events', [])
        original_clause = audit_result.get('raw_clause_text', '')
        original_strength = audit_result.get('strength_score', 0.0)

        corrected_clause = None

        # Try LLM if requested
        if use_llm:
            try:
                corrected_clause = _llm_rewrite_fm_clause(original_clause, missing_events)
            except Exception as llm_err:
                logger.warning(f"LLM rewrite failed, falling back to rule-based: {llm_err}")

        # Fall back to rule-based if LLM failed or not requested
        if not corrected_clause:
            corrected_clause = _rule_based_fm_clause(missing_events, original_clause)

        # Re-audit the corrected clause to estimate improvement
        try:
            corrected_audit = audit_fm_clause(corrected_clause)
            new_strength = corrected_audit.get('strength_score', 0.0)
        except Exception as audit_err:
            logger.warning(f"Re-audit failed, estimating strength: {audit_err}")
            # Estimate strength based on events added
            new_strength = min(1.0, original_strength + (len(missing_events) * 0.06))

        return {
            'original_clause': original_clause,
            'corrected_clause': corrected_clause,
            'original_strength_score': original_strength,
            'new_strength_score': new_strength,
            'risk_reduction_before': round(1.0 - original_strength, 4),
            'risk_reduction_after': round(1.0 - new_strength, 4),
            'events_added': missing_events,
            'improvement': round(new_strength - original_strength, 4),
        }
    except Exception as e:
        logger.error(f"Auto-correct failed completely: {e}", exc_info=True)
        # Return safe fallback
        return {
            'original_clause': contract_text[:500],
            'corrected_clause': _rule_based_fm_clause([], contract_text[:500]),
            'original_strength_score': 0.3,
            'new_strength_score': 0.7,
            'risk_reduction_before': 0.7,
            'risk_reduction_after': 0.3,
            'events_added': [],
            'improvement': 0.4,
            'error': str(e),
        }


def _llm_rewrite_fm_clause(original_clause: str, missing_events: List[str]) -> Optional[str]:
    """Calls Qwen via Ollama to rewrite the FM clause."""
    missing_str = ', '.join(missing_events) if missing_events else 'none'
    prompt = f"""You are a legal expert specializing in Force Majeure contract clauses.

ORIGINAL CLAUSE:
{original_clause[:800] if original_clause else 'No existing Force Majeure clause found.'}

MISSING PROTECTIONS (not covered in original):
{missing_str}

Task: Rewrite this Force Majeure clause to include ALL 14 modern FM event categories:
war, terrorism, cyber warfare, trade sanctions, embargo, pandemic, epidemic,
government lockdown, supply chain disruption, port closure, airspace closure,
energy shortages, commodity shock, satellite disruption.

Include: notice period, suspension of obligations, cost escalation mechanism,
alternative sourcing obligation, insurance trigger, payment suspension,
and termination for extended FM.

Write ONLY the improved Force Majeure clause text. Be comprehensive and legally precise."""

    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                'model': 'qwen2.5:0.5b',
                'prompt': prompt,
                'stream': False,
                'options': {'temperature': 0.3, 'num_predict': 800},
            },
            timeout=50,
        )
        if resp.status_code == 200:
            return resp.json().get('response', '').strip()
    except Exception as e:
        logger.warning(f"LLM FM clause rewrite failed: {e}")
    return None


# ---------------------------------------------------------------------------
# 5. FM MITIGATION ENGINE
# ---------------------------------------------------------------------------

MITIGATION_CATALOG = {
    'war': [
        'Add War Risk Insurance clause requiring war risk coverage for project duration',
        'Include Alternative Sourcing clause requiring identification of suppliers outside conflict zones',
        'Add Shipping Route Substitution clause for alternative logistics routes',
    ],
    'trade_sanctions': [
        'Add Sanctions Protection clause covering OFAC, EU, and UN sanctions lists',
        'Include Contract Suspension clause triggered by sanctions imposition',
        'Add Currency Volatility Protection clause for sanctions-induced exchange rate risk',
    ],
    'pandemic': [
        'Add Pandemic / Health Emergency clause covering WHO-declared emergencies',
        'Include Labor Shortage Protection clause for workforce availability disruptions',
        'Add Government Lockdown clause for mandatory closure orders',
    ],
    'supply_chain_disruption': [
        'Add Alternative Supplier clause requiring pre-approved backup suppliers',
        'Include Material Shortage clause covering critical component unavailability',
        'Add Inventory Buffer requirement for critical materials',
    ],
    'port_closure': [
        'Add Port Closure clause covering harbor shutdowns and maritime route disruptions',
        'Include Shipping Route Diversification clause with pre-approved alternative ports',
    ],
    'energy_shortages': [
        'Add Energy Shortage clause covering power grid failures and fuel supply disruptions',
        'Include Generator/Backup Power provision for critical operations',
    ],
    'cyber_warfare': [
        'Add Cyber Warfare clause covering cyber attacks on critical infrastructure',
        'Include Business Continuity clause for IT/OT system disruptions',
    ],
    'commodity_shock': [
        'Add Commodity Price Escalation clause with 15% threshold for price adjustment',
        'Include Material Cost Review mechanism for extraordinary price movements',
    ],
}


def suggest_mitigations(missing_events: List[str], top_drivers: List[Dict]) -> List[Dict]:
    """Returns mitigation suggestions for missing FM events and top risk drivers."""
    suggestions = []

    for event in missing_events:
        if event in MITIGATION_CATALOG:
            for suggestion in MITIGATION_CATALOG[event]:
                suggestions.append({
                    'event_category': event,
                    'suggestion': suggestion,
                    'priority': 'high' if event in ['war', 'pandemic', 'trade_sanctions'] else 'medium',
                })

    # Also suggest based on top risk drivers
    for driver in top_drivers:
        node = driver.get('node', '')
        prob = driver.get('probability', 0.0)
        if prob > 0.4 and node in MITIGATION_CATALOG:
            for suggestion in MITIGATION_CATALOG[node][:1]:  # top 1 per driver
                if not any(s['suggestion'] == suggestion for s in suggestions):
                    suggestions.append({
                        'event_category': node,
                        'suggestion': suggestion,
                        'priority': 'high' if prob > 0.6 else 'medium',
                    })

    return suggestions[:10]  # cap at 10


# ---------------------------------------------------------------------------
# 6. WAR RISK ENGINE
# ---------------------------------------------------------------------------

def analyze_war_risk(
    contract_text: str,
    contract_id: str = '',
    contract_title: str = '',
    contract_value: float = 0.0,
    project_location: str = '',
    supplier_locations: Optional[List[str]] = None,
    manual_war_events: Optional[Dict[str, float]] = None,
) -> Dict:
    """
    Analyzes war and geopolitical risk for a contract.
    Returns war risk score, top threats, exposure, and mitigation clauses.
    """
    # Extract war-related signals from contract text
    war_events_detected: Dict[str, float] = {}

    war_keywords = {
        'military_invasion': ['military invasion', 'armed invasion', 'military conflict', 'nato', 'armed forces', 'war zone', 'conflict zone'],
        'trade_embargo': ['embargo', 'trade embargo', 'export ban', 'import ban'],
        'sanctions': ['sanctions', 'sanction', 'ofac', 'restricted party', 'economic sanctions'],
        'naval_blockade': ['naval blockade', 'sea blockade', 'maritime blockade', 'black sea', 'suez canal', 'strait of hormuz', 'red sea'],
        'cyber_warfare': ['cyber attack', 'cyberattack', 'ransomware', 'nation-state attack', 'cyber warfare'],
        'port_shutdown': ['port shutdown', 'port closure', 'harbor closure', 'port congestion'],
        'airspace_closure': ['airspace closure', 'no-fly zone', 'flight ban'],
        'energy_infrastructure_attack': ['energy infrastructure', 'pipeline attack', 'power grid attack', 'gas pipeline', 'natural gas pipeline'],
    }

    # Also detect risk based on project location and supplier locations
    high_risk_regions = ['middle east', 'ukraine', 'russia', 'iran', 'iraq', 'syria', 'yemen', 'libya', 'sudan', 'myanmar', 'north korea']
    high_risk_routes = ['black sea', 'suez canal', 'strait of hormuz', 'red sea', 'persian gulf']

    all_context = (contract_text + ' ' + project_location + ' ' + ' '.join(supplier_locations or [])).lower()

    for region in high_risk_regions:
        if region in all_context:
            if region in ['ukraine', 'russia']:
                war_events_detected['military_invasion'] = max(war_events_detected.get('military_invasion', 0), 0.75)
                war_events_detected['sanctions'] = max(war_events_detected.get('sanctions', 0), 0.80)
            elif region in ['middle east', 'iran', 'iraq', 'syria', 'yemen']:
                war_events_detected['military_invasion'] = max(war_events_detected.get('military_invasion', 0), 0.55)
                war_events_detected['sanctions'] = max(war_events_detected.get('sanctions', 0), 0.60)
            elif region in ['iran', 'north korea']:
                war_events_detected['sanctions'] = max(war_events_detected.get('sanctions', 0), 0.90)

    for route in high_risk_routes:
        if route in all_context:
            war_events_detected['naval_blockade'] = max(war_events_detected.get('naval_blockade', 0), 0.65)
            war_events_detected['port_shutdown'] = max(war_events_detected.get('port_shutdown', 0), 0.55)

    text_lower = contract_text.lower()
    for event, keywords in war_keywords.items():
        hits = sum(1 for kw in keywords if kw in text_lower)
        if hits > 0:
            existing = war_events_detected.get(event, 0)
            war_events_detected[event] = max(existing, min(0.4 * hits, 0.85))

    # Merge with manual inputs
    if manual_war_events:
        war_events_detected.update(manual_war_events)

    # Compute war risk
    war_result = compute_war_risk_score(war_events_detected)
    war_risk_score = war_result['war_risk_score']

    # Estimate financial exposure
    if contract_value > 0:
        war_loss_expected = war_risk_score * contract_value * 0.25
        war_loss_worst = war_risk_score * contract_value * 0.60
    else:
        war_loss_expected = war_risk_score * 250000
        war_loss_worst = war_risk_score * 600000

    # War-specific mitigation clauses
    war_mitigations = [
        'War Risk Insurance clause — mandatory coverage for active conflict zones',
        'Sanctions Protection clause — auto-suspension on OFAC/UN sanction listing',
        'Alternative Shipping Route clause — pre-approved backup logistics routes',
        'Currency Volatility clause — war-induced exchange rate protection',
        'War Extension-of-Time clause — automatic schedule extension during hostilities',
        'Force Majeure Termination clause — exit mechanism if war persists > 180 days',
    ]

    # LLM explanation
    explanation = _generate_war_explanation(
        war_risk_score=war_risk_score,
        top_threats=war_result['top_threats'],
        contract_title=contract_title,
        project_location=project_location,
    )

    return {
        'contract_id': contract_id,
        'contract_title': contract_title,
        'war_risk_score': war_risk_score,
        'event_risks': {e: round(p, 4) for e, p in war_events_detected.items()},
        'supply_chain_routes': [],
        'disrupted_routes': [
            r for r, p in war_result.get('disruption_probs', {}).items() if p > 0.4
        ],
        'war_loss_expected_usd': round(war_loss_expected, 2),
        'war_loss_worst_usd': round(war_loss_worst, 2),
        'top_threats': war_result['top_threats'],
        'project_location': project_location,
        'supplier_locations': supplier_locations or [],
        'shipping_routes': [],
        'war_mitigation_clauses': war_mitigations,
        'explanation': explanation,
    }


# ---------------------------------------------------------------------------
# LLM HELPER — explanation generation
# ---------------------------------------------------------------------------

def _generate_fm_explanation(
    fm_risk_score: float,
    top_drivers: List[Dict],
    outcomes: Dict[str, float],
    missing_events: List[str],
    contract_title: str = '',
) -> str:
    """Generates a natural language FM risk explanation using Qwen."""
    drivers_str = ', '.join(d['node'] for d in top_drivers[:3])
    missing_str = ', '.join(missing_events[:5]) if missing_events else 'none'

    prompt = f"""You are a Force Majeure risk analyst. Provide a brief (3-4 sentences) risk assessment.

Contract: {contract_title or 'Contract'}
FM Risk Score: {fm_risk_score:.2f}/1.0
Top Risk Drivers: {drivers_str}
FM Invocation Probability: {outcomes.get('fm_invocation', 0):.1%}
Project Delay Probability: {outcomes.get('project_delay', 0):.1%}
Missing FM Protections: {missing_str}

Write a concise risk assessment explaining: (1) overall risk level, (2) key drivers, (3) main vulnerabilities."""

    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                'model': 'qwen2.5:0.5b',
                'prompt': prompt,
                'stream': False,
                'options': {'temperature': 0.3, 'num_predict': 200},
            },
            timeout=45,
        )
        if resp.status_code == 200:
            return resp.json().get('response', '').strip()
    except Exception as e:
        logger.warning(f"LLM FM explanation failed: {e}")

    # Fallback
    risk_level = 'HIGH' if fm_risk_score > 0.6 else 'MEDIUM' if fm_risk_score > 0.35 else 'LOW'
    return (
        f"This contract has a {risk_level} Force Majeure risk score of {fm_risk_score:.2f}. "
        f"The primary risk drivers are {drivers_str}. "
        f"The probability of FM invocation is {outcomes.get('fm_invocation', 0):.1%} with "
        f"a {outcomes.get('project_delay', 0):.1%} chance of project delay. "
        f"Key missing protections: {missing_str}."
    )


def _generate_war_explanation(
    war_risk_score: float,
    top_threats: List[Dict],
    contract_title: str = '',
    project_location: str = '',
) -> str:
    """Generates a brief war risk explanation."""
    threat_str = ', '.join(t['event'] for t in top_threats[:3]) if top_threats else 'none identified'
    risk_level = 'HIGH' if war_risk_score > 0.6 else 'MEDIUM' if war_risk_score > 0.3 else 'LOW'
    return (
        f"War & geopolitical risk for '{contract_title or 'this contract'}' is {risk_level} "
        f"(score: {war_risk_score:.2f}). "
        f"Top geopolitical threats: {threat_str}. "
        f"{'Project location ' + project_location + ' is in an elevated-risk region. ' if project_location else ''}"
        f"Recommend adding war risk insurance, sanctions protection, and alternative shipping route clauses."
    )


# ---------------------------------------------------------------------------
# PORTFOLIO AUDIT — batch scan all contracts
# ---------------------------------------------------------------------------

def bulk_audit_contracts(contracts: List[Dict]) -> List[Dict]:
    """
    Bulk audit a list of contracts for FM clause coverage.
    contracts: list of {contract_id, contract_title, contract_text, contract_value}
    Returns list of audit results with risk categorization.
    """
    results = []
    for contract in contracts:
        try:
            audit = audit_fm_clause(
                contract.get('contract_text', ''),
                contract.get('contract_id', ''),
                contract.get('contract_title', ''),
            )
            results.append(audit)
        except Exception as e:
            logger.error(f"Audit failed for {contract.get('contract_id')}: {e}")
            results.append({
                'contract_id': contract.get('contract_id', ''),
                'contract_title': contract.get('contract_title', ''),
                'status': 'missing',
                'strength_score': 0.0,
                'covered_events': [],
                'missing_events': FM_EVENT_CATEGORIES,
                'error': str(e),
            })

    return results
