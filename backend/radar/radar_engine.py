"""
Strategic Radar Engine
======================
Orchestrator that connects market signals → clause detection → exposure modeling → LLM narrative.
"""

import logging
from market.market_feed import get_signals_for_contract_type
from .clause_intelligence import has_price_adjustment_clause, get_clause_exposure_profile
from .exposure_engine import (
    calculate_commodity_exposure,
    calculate_interest_exposure,
    calculate_fx_exposure,
    aggregate_total_exposure,
)
from .strategic_rag import generate_strategic_alert

logger = logging.getLogger(__name__)


def _parse_contract_value(contract):
    """
    Extract contract value — tries field first, then full_text regex scan.
    Handles ?, ₹, $, €, Rs. symbols and Indian/US comma formatting.
    """
    import re

    def _clean(raw_str):
        cleaned = re.sub(r'[₹$€£¥?Rs\.INR\s]', '', str(raw_str))
        cleaned = cleaned.replace(',', '').strip()
        try:
            return float(cleaned) if cleaned else None
        except ValueError:
            return None

    raw = getattr(contract, 'contract_value', None)
    if raw:
        val = _clean(raw)
        if val and val > 0:
            return val

    full_text = getattr(contract, 'full_text', '') or ''
    if full_text:
        patterns = [
            r'(?:contract\s+value|total\s+value|contract\s+sum|total\s+amount)[^\d]{0,40}([\d,]+(?:\.\d+)?)',
            r'(?:\$|₹|€|Rs\.?|INR)\s*([\d,]+(?:\.\d+)?)',
            r'\b([\d]{1,3}(?:,[\d]{2,3})+(?:\.\d+)?)\b',
        ]
        for pattern in patterns:
            for m in re.findall(pattern, full_text, re.I):
                try:
                    val = float(m.replace(',', ''))
                    if val >= 10_000:
                        return val
                except ValueError:
                    continue

    return 0.0


def run_strategic_radar(contract_id):
    """
    Full Strategic Intelligence Radar pipeline for a contract.

    1. Load contract + clauses
    2. Fetch all market signals
    3. Detect clause types (price adjustment, fx, etc.)
    4. Calculate exposure for each active signal
    5. Generate LLM narrative for highest-impact opportunity
    6. Return full radar report

    Returns:
        dict — complete radar report
    """
    from core.models import Contract, Clause

    try:
        contract = Contract.objects.get(id=contract_id)
    except Contract.DoesNotExist:
        return {"error": f"Contract {contract_id} not found"}

    contract_value = _parse_contract_value(contract)
    clauses = Clause.objects.filter(contract_id=contract_id)
    clause_profile = get_clause_exposure_profile(clauses)
    has_adjustment = has_price_adjustment_clause(clauses)

    # Contract type detection (must happen before signal fetch)
    filename_lower = (getattr(contract, 'filename', '') or '').lower()
    full_text_lower = (getattr(contract, 'full_text', '') or '').lower()
    scan_text = filename_lower + ' ' + full_text_lower[:3000]

    SOFTWARE_INDICATORS = [
        'software', 'it service', 'information technology', 'web development',
        'mobile app', 'saas', 'application development', 'digital service',
        'software development', 'software agreement', 'technology service',
        'support agreement', 'outsourcing agreement',
    ]
    PHYSICAL_INDICATORS = [
        'construction', 'supply of goods', 'manufacturing',
        'engineering', 'civil work', 'erection',
        'works contract', 'epc contract', 'supply contract', 'fabrication',
    ]
    LEASE_INDICATORS = [
        'lease', 'rental', 'tenancy', 'landlord', 'tenant', 'rent',
        'premises', 'property', 'real estate', 'office space', 'commercial space',
        'lease agreement', 'lease deed', 'letting',
    ]
    LOGISTICS_INDICATORS = [
        'logistics', 'transport', 'freight', 'shipping', 'delivery',
        'fleet', 'cargo', 'courier', 'warehousing', 'distribution',
    ]
    FINANCIAL_INDICATORS = [
        'loan agreement', 'credit agreement', 'facility agreement',
        'debenture', 'bond', 'mortgage', 'hypothecation',
    ]

    is_software  = any(k in scan_text for k in SOFTWARE_INDICATORS)
    is_physical  = any(k in scan_text for k in PHYSICAL_INDICATORS)
    is_lease     = any(k in scan_text for k in LEASE_INDICATORS)
    is_logistics = any(k in scan_text for k in LOGISTICS_INDICATORS)
    is_financial = any(k in scan_text for k in FINANCIAL_INDICATORS)

    # Priority order: software > lease > financial > logistics > physical > default
    if is_software and not is_physical:
        contract_type = 'Software/IT/Service'
    elif is_lease:
        contract_type = 'Real Estate/Lease'
    elif is_financial:
        contract_type = 'Financial/Loan'
    elif is_logistics:
        contract_type = 'Logistics/Transport'
    elif is_physical:
        contract_type = 'Physical/Procurement'
    else:
        contract_type = 'default'

    # Fetch market signals tailored to this contract type
    market_signals = get_signals_for_contract_type(contract_type)

    has_commodity_clauses = clause_profile.get('commodity', 0) > 0 or clause_profile.get('price_adjustment', 0) > 0
    has_fx_clauses = clause_profile.get('fx', 0) > 0
    has_financing_clauses = clause_profile.get('financing', 0) > 0

    STEEL_KEYWORDS = ['steel', 'metal', 'iron', 'construction', 'civil', 'infrastructure',
                      'raw material', 'material cost', 'procurement', 'fabrication',
                      'structural', 'building', 'copper', 'aluminum']
    CRUDE_KEYWORDS = ['fuel', 'crude', 'oil', 'petroleum', 'diesel', 'energy',
                      'transport', 'logistics', 'freight', 'shipping', 'power']
    FX_KEYWORDS = ['usd', 'dollar', 'foreign currency', 'forex', 'import', 'export',
                   'overseas', 'offshore', 'international', 'cross-border', 'currency']
    FINANCE_KEYWORDS = ['interest', 'loan', 'credit', 'financing', 'debenture',
                        'floating rate', 'base rate', 'repo rate', 'libor', 'sofr']

    fx_relevant = has_fx_clauses or any(k in scan_text for k in FX_KEYWORDS)
    ir_relevant = has_financing_clauses or any(k in scan_text for k in FINANCE_KEYWORDS)

    if contract_type == 'Physical/Procurement':
        steel_relevant = has_commodity_clauses or any(k in scan_text for k in STEEL_KEYWORDS)
        crude_relevant = has_commodity_clauses or any(k in scan_text for k in CRUDE_KEYWORDS)
    else:
        steel_relevant = False
        crude_relevant = False

    steel_weight = 1.0 if steel_relevant else 0.0
    crude_weight = 1.0 if crude_relevant else 0.0
    fx_weight    = 1.0 if fx_relevant else 0.0
    ir_weight    = 1.0 if ir_relevant else 0.0

    # Signal relevance must match the actual signal keys returned by get_signals_for_contract_type
    if contract_type == 'Software/IT/Service':
        signal_relevance = {
            'nasdaq':        {'relevant': True, 'weight': 1.0,
                              'reason': 'Tech sector health — directly impacts IT contract valuations'},
            'usd_inr':       {'relevant': True, 'weight': 1.0,
                              'reason': 'USD/INR — IT services typically billed in USD'},
            'interest_rate': {'relevant': True, 'weight': 1.0,
                              'reason': 'US 10Y — benchmark for payment risk and cost of capital'},
            'nifty50':       {'relevant': True, 'weight': 1.0,
                              'reason': 'Nifty 50 — Indian market sentiment affects contract confidence'},
        }
    elif contract_type == 'Real Estate/Lease':
        signal_relevance = {
            'nifty_bank':    {'relevant': True, 'weight': 1.0,
                              'reason': 'RBI rate moves — directly impact EMI, rent escalation clauses'},
            'nifty_realty':  {'relevant': True, 'weight': 1.0,
                              'reason': 'Real estate sector health — DLF index tracks property valuations'},
            'usd_inr':       {'relevant': fx_relevant, 'weight': fx_weight or 1.0,
                              'reason': ('FX exposure — foreign tenant or overseas funding detected'
                                         if fx_relevant else 'No cross-border FX exposure found')},
            'interest_rate': {'relevant': True, 'weight': 1.0,
                              'reason': 'US 10Y — benchmark financing rate affects lease pricing'},
        }
    elif contract_type == 'Financial/Loan':
        signal_relevance = {
            'interest_rate': {'relevant': True, 'weight': 1.0,
                              'reason': 'US 10Y — core benchmark rate for loan/facility pricing'},
            'nifty_bank':    {'relevant': True, 'weight': 1.0,
                              'reason': 'India Bank Nifty — RBI policy proxy, affects lending rates'},
            'usd_inr':       {'relevant': fx_relevant, 'weight': fx_weight or 1.0,
                              'reason': ('FX exposure — USD-denominated loan detected'
                                         if fx_relevant else 'No cross-border FX exposure found')},
            'nifty50':       {'relevant': True, 'weight': 1.0,
                              'reason': 'Nifty 50 — credit risk proxy for counterparty health'},
        }
    elif contract_type == 'Logistics/Transport':
        signal_relevance = {
            'crude_oil':     {'relevant': True, 'weight': 1.0,
                              'reason': 'WTI Crude — fuel cost is the primary logistics cost driver'},
            'usd_inr':       {'relevant': fx_relevant, 'weight': fx_weight or 1.0,
                              'reason': ('USD/INR — import/export cost exposure detected'
                                         if fx_relevant else 'No cross-border FX exposure found')},
            'interest_rate': {'relevant': ir_relevant, 'weight': ir_weight or 1.0,
                              'reason': ('Working capital financing rate exposure detected'
                                         if ir_relevant else 'No financing rate clauses found')},
            'nifty50':       {'relevant': True, 'weight': 1.0,
                              'reason': 'Nifty 50 — demand proxy for freight and logistics volume'},
        }
    elif contract_type == 'Physical/Procurement':
        signal_relevance = {
            'steel': {
                'relevant': steel_relevant,
                'weight': steel_weight,
                'reason': ('Steel/material cost exposure detected'
                           if steel_relevant else 'No steel or material supply keywords in contract'),
            },
            'crude_oil': {
                'relevant': crude_relevant,
                'weight': crude_weight,
                'reason': ('Fuel/energy/logistics cost exposure detected'
                           if crude_relevant else 'No fuel or transport cost keywords in contract'),
            },
            'usd_inr': {
                'relevant': fx_relevant,
                'weight': fx_weight,
                'reason': ('Foreign currency / cross-border exposure detected'
                           if fx_relevant else 'No foreign currency exposure in contract'),
            },
            'interest_rate': {
                'relevant': ir_relevant,
                'weight': ir_weight,
                'reason': ('Financing / rate-linked clauses detected'
                           if ir_relevant else 'No interest rate-linked clauses found'),
            },
        }
    else:  # default
        signal_relevance = {
            'usd_inr':       {'relevant': fx_relevant, 'weight': fx_weight or 1.0,
                              'reason': ('FX exposure detected' if fx_relevant else 'General USD/INR rate monitor')},
            'interest_rate': {'relevant': ir_relevant, 'weight': ir_weight or 1.0,
                              'reason': ('Rate-linked clauses detected' if ir_relevant else 'General interest rate monitor')},
            'nifty50':       {'relevant': True, 'weight': 1.0,
                              'reason': 'Nifty 50 — overall market conditions proxy'},
            'crude_oil':     {'relevant': True, 'weight': 1.0,
                              'reason': 'Crude oil — general energy/inflation cost indicator'},
        }

    # Calculate exposures dynamically for whatever signals were fetched
    exposures = []
    FX_SIGNAL_KEYS = {'usd_inr', 'eur_inr', 'gbp_inr'}
    IR_SIGNAL_KEYS = {'interest_rate', 'nifty_bank', 'india_repo'}

    for sig_key, sig_data in market_signals.items():
        daily_pct = sig_data.get('percent_change', 0) or 0
        avg_vol   = sig_data.get('avg_volatility', 0.5) or 0.5
        # Use whichever is larger: today's actual move, or 5-day average volatility
        # This ensures meaningful exposure even on flat market days
        effective_pct = daily_pct if abs(daily_pct) >= avg_vol * 0.5 else avg_vol

        rel = signal_relevance.get(sig_key, {'relevant': True, 'weight': 1.0})
        weight = rel.get('weight', 1.0)

        if sig_key in FX_SIGNAL_KEYS:
            exp = calculate_fx_exposure(contract_value * weight, effective_pct, sig_data.get('signal_name', 'FX'))
        elif sig_key in IR_SIGNAL_KEYS:
            exp = calculate_interest_exposure(contract_value * weight, effective_pct * 100)
        else:
            exp = calculate_commodity_exposure(contract_value * weight, effective_pct, has_adjustment)
            exp['exposure_type'] = sig_key

        exp['signal'] = sig_data
        exp['effective_pct_used'] = round(effective_pct, 4)
        exp['relevance'] = rel
        exposures.append(exp)

    total_exposure = aggregate_total_exposure(exposures)

    # Find highest-impact opportunity
    best_opportunity = None
    best_impact = 0
    for exp in exposures:
        impact = exp.get('estimated_impact') or exp.get('annual_financing_impact', 0) or 0
        if impact > best_impact and not exp.get('protected', False):
            best_impact = impact
            best_opportunity = exp

    # Generate LLM narrative
    alerts = []
    if best_opportunity and best_impact > 0:
        narrative = generate_strategic_alert(
            contract_title=getattr(contract, 'filename', 'Contract'),
            signal=best_opportunity.get('signal', {}),
            estimated_impact=best_impact,
            exposure_type=best_opportunity.get('exposure_type', 'commodity'),
        )
        alerts.append({
            "alert_type": "strategic_opportunity" if best_opportunity.get('opportunity_type') == 'savings' else "cost_risk",
            "estimated_value": best_impact,
            "exposure_type": best_opportunity.get('exposure_type'),
            "message": narrative,
        })

    return {
        "contract_id": str(contract.id),
        "contract_title": getattr(contract, 'filename', 'Unknown'),
        "contract_value": contract_value,
        "contract_type": contract_type,
        "clause_exposure_profile": clause_profile,
        "has_price_adjustment_clause": has_adjustment,
        "signal_relevance": signal_relevance,
        "market_signals": {
            k: {
                "signal_name": v.get("signal_name"),
                "current_value": v.get("current_value"),
                "percent_change": v.get("percent_change"),
                "status": v.get("status"),
                "ticker": v.get("ticker"),
                "relevant": signal_relevance.get(k, {}).get("relevant", False),
                "relevance_reason": signal_relevance.get(k, {}).get("reason", ""),
            }
            for k, v in market_signals.items()
        },
        "exposures": [
            {k: v for k, v in e.items() if k != 'signal'}
            for e in exposures
        ],
        "total_exposure": total_exposure,
        "alerts": alerts,
        "has_alerts": len(alerts) > 0,
    }
