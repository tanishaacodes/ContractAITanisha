"""
Intelligent Clustering Map APIs
Provides 5 Gartner-style quadrant visualizations for contract portfolio analysis
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from core.models import Contract, Clause, ContractRiskHistory
from ai.normalize import normalize, parse_contract_value
from ai.geography import geography_risk
from ai.ip_risk import ip_risk
from ai.liability import liability_risk
from ai.colors import get_bu_color
from ai.risk_engine import score_clause_risk, calculate_overall_risk
from decimal import Decimal


def get_contract_overall_risk(contract_id, full_text='', version=None):
    """
    Helper to calculate overall risk for a contract
    If version is provided, tries to fetch from ContractRiskHistory first
    Falls back to real-time calculation if history not available
    Returns: Risk score 0-100
    """
    # Try to get from history if version specified
    if version:
        try:
            history = ContractRiskHistory.objects.get(contract_id=contract_id, version=version)
            return history.overall_risk
        except ContractRiskHistory.DoesNotExist:
            pass

    # Fallback: calculate from clauses
    clauses = Clause.objects.filter(contract_id=contract_id).values('extracted_text')

    if clauses.exists():
        # Score each clause
        clauses_data = []
        for clause in clauses:
            risk_score, _ = score_clause_risk(clause['extracted_text'] or '')
            clauses_data.append({'risk_score': risk_score})

        # Calculate overall risk (returns 0-100)
        return calculate_overall_risk(clauses_data)
    elif full_text:
        # Fallback: score the full text
        risk_score, _ = score_clause_risk(full_text)
        return round(risk_score * 100, 2)
    else:
        # Default if no data available
        return 50


def get_contract_dimension_risks(contract_id, contract_value, total_liability, full_text='', version=None):
    """
    Get dimension-specific risks (IP, liability, geography) for a contract
    If version is provided, tries to fetch from ContractRiskHistory first
    Returns: dict with ip_risk, liability_risk, geography_risk
    """
    # Try to get from history if version specified
    if version:
        try:
            history = ContractRiskHistory.objects.get(contract_id=contract_id, version=version)
            return {
                'ip_risk': history.ip_risk,
                'liability_risk': history.liability_risk,
                'geography_risk': history.geography_risk
            }
        except ContractRiskHistory.DoesNotExist:
            pass

    # Fallback: calculate on the fly
    ip_score, _ = ip_risk(full_text or '')
    geo_score, _ = geography_risk(full_text or '')

    contract_val = parse_contract_value(contract_value)
    liability_val = float(total_liability) if total_liability else 0

    liability_score, _ = liability_risk(liability_val, contract_val)

    return {
        'ip_risk': ip_score,
        'liability_risk': liability_score,
        'geography_risk': geo_score
    }


@require_http_methods(["GET"])
def risk_value_map(request):
    """
    MAP 1: Risk vs Contract Value
    X-axis: Contract Value (normalized 0-100)
    Y-axis: Overall Risk Score (0-100)

    Identifies: "Big money, big danger?"
    """
    user_id = request.GET.get('user_id')
    version = request.GET.get('version')

    # Convert version to int if provided
    if version:
        try:
            version = int(version)
        except (ValueError, TypeError):
            version = None

    if not user_id:
        return JsonResponse({'error': 'user_id required'}, status=400)

    contracts = Contract.objects.filter(user_id=user_id).values(
        'id', 'filename', 'contract_value', 'business_unit', 'full_text'
    )

    data = []
    contract_values = []

    # First pass: collect values for normalization
    for c in contracts:
        contract_values.append(parse_contract_value(c['contract_value']))

    # Get min/max for normalization
    min_val = min(contract_values) if contract_values else 0
    max_val = max(contract_values) if contract_values else 0

    # Second pass: calculate risk and normalize
    for c in contracts:
        value = parse_contract_value(c['contract_value'])

        # Calculate overall risk (use history if version provided)
        risk_score = get_contract_overall_risk(c['id'], c['full_text'], version=version)

        data.append({
            'x': normalize(value, min_val, max_val),
            'y': risk_score,
            'label': c['filename'],
            'contract_id': c['id'],
            'business_unit': c['business_unit'] or 'Others',
            'color': get_bu_color(c['business_unit'] or 'Others')
        })

    return JsonResponse(data, safe=False)


@require_http_methods(["GET"])
def risk_liability_map(request):
    """
    MAP 2: Risk vs Liability Exposure
    X-axis: Risk Score (0-100)
    Y-axis: Liability % (0-100)

    Identifies: "Is risk backed by real financial pain?"
    """
    user_id = request.GET.get('user_id')
    version = request.GET.get('version')

    # Convert version to int if provided
    if version:
        try:
            version = int(version)
        except (ValueError, TypeError):
            version = None

    if not user_id:
        return JsonResponse({'error': 'user_id required'}, status=400)

    contracts = Contract.objects.filter(user_id=user_id).values(
        'id', 'filename', 'contract_value', 'total_liability', 'business_unit', 'full_text'
    )

    data = []

    for c in contracts:
        # Calculate risks (use history if version provided)
        overall_risk = get_contract_overall_risk(c['id'], c['full_text'], version=version)
        dimension_risks = get_contract_dimension_risks(
            c['id'], c['contract_value'], c['total_liability'], c['full_text'], version=version
        )

        data.append({
            'x': overall_risk,
            'y': dimension_risks['liability_risk'],
            'label': c['filename'],
            'contract_id': c['id'],
            'business_unit': c['business_unit'] or 'Others',
            'color': get_bu_color(c['business_unit'] or 'Others')
        })

    return JsonResponse(data, safe=False)


@require_http_methods(["GET"])
def geo_value_map(request):
    """
    MAP 3: Geography Risk vs Contract Value
    X-axis: Geography Risk (0-100)
    Y-axis: Contract Value (normalized 0-100)

    Identifies: "Are we exposed in dangerous regions?"
    """
    user_id = request.GET.get('user_id')
    version = request.GET.get('version')

    # Convert version to int if provided
    if version:
        try:
            version = int(version)
        except (ValueError, TypeError):
            version = None

    if not user_id:
        return JsonResponse({'error': 'user_id required'}, status=400)

    contracts = Contract.objects.filter(user_id=user_id).values(
        'id', 'filename', 'contract_value', 'total_liability', 'business_unit', 'full_text'
    )

    data = []
    contract_values = []

    # First pass: collect values
    for c in contracts:
        contract_values.append(parse_contract_value(c['contract_value']))

    min_val = min(contract_values) if contract_values else 0
    max_val = max(contract_values) if contract_values else 0

    # Second pass: analyze geography
    for c in contracts:
        value = parse_contract_value(c['contract_value'])

        # Get geography risk (use history if version provided)
        dimension_risks = get_contract_dimension_risks(
            c['id'], c['contract_value'], c['total_liability'], c['full_text'], version=version
        )
        geo_score = dimension_risks['geography_risk']

        # Get detected locations for tooltip (only available when calculating on-the-fly)
        detected_geos = []
        if not version:
            _, detected_geos = geography_risk(c['full_text'] or '')

        data.append({
            'x': geo_score,
            'y': normalize(value, min_val, max_val),
            'label': c['filename'],
            'contract_id': c['id'],
            'business_unit': c['business_unit'] or 'Others',
            'color': get_bu_color(c['business_unit'] or 'Others'),
            'detected_locations': [g[0] for g in detected_geos] if detected_geos else []
        })

    return JsonResponse(data, safe=False)


@require_http_methods(["GET"])
def ip_liability_map(request):
    """
    MAP 4: IP Risk vs Liability
    X-axis: IP Risk (0-100)
    Y-axis: Liability Exposure (0-100)

    Identifies: "Could IP issues bankrupt us?"
    """
    user_id = request.GET.get('user_id')
    version = request.GET.get('version')

    # Convert version to int if provided
    if version:
        try:
            version = int(version)
        except (ValueError, TypeError):
            version = None

    if not user_id:
        return JsonResponse({'error': 'user_id required'}, status=400)

    contracts = Contract.objects.filter(user_id=user_id).values(
        'id', 'filename', 'contract_value', 'total_liability', 'business_unit', 'full_text'
    )

    data = []

    for c in contracts:
        # Get dimension risks (use history if version provided)
        dimension_risks = get_contract_dimension_risks(
            c['id'], c['contract_value'], c['total_liability'], c['full_text'], version=version
        )

        # Get detected IP terms for tooltip (only available when calculating on-the-fly)
        detected_terms = []
        if not version:
            _, detected_terms = ip_risk(c['full_text'] or '')

        data.append({
            'x': dimension_risks['ip_risk'],
            'y': dimension_risks['liability_risk'],
            'label': c['filename'],
            'contract_id': c['id'],
            'business_unit': c['business_unit'] or 'Others',
            'color': get_bu_color(c['business_unit'] or 'Others'),
            'ip_terms': [t[0] for t in detected_terms] if detected_terms else []
        })

    return JsonResponse(data, safe=False)


@require_http_methods(["GET"])
def strategic_quadrant_map(request):
    """
    MAP 5: Composite Strategic Risk Quadrant
    X-axis: Financial Exposure (Contract Value + Liability, normalized 0-100)
    Y-axis: Legal/IP Risk (Average of overall + IP risk, 0-100)

    Identifies: "Portfolio health at a glance" - The CXO hero slide
    """
    user_id = request.GET.get('user_id')
    version = request.GET.get('version')

    # Convert version to int if provided
    if version:
        try:
            version = int(version)
        except (ValueError, TypeError):
            version = None

    if not user_id:
        return JsonResponse({'error': 'user_id required'}, status=400)

    contracts = Contract.objects.filter(user_id=user_id).values(
        'id', 'filename', 'contract_value', 'total_liability', 'business_unit', 'full_text'
    )

    data = []
    financial_exposures = []

    # First pass: collect financial exposures
    for c in contracts:
        contract_val = parse_contract_value(c['contract_value'])
        liability_val = float(c['total_liability']) if c['total_liability'] else 0
        financial_exposures.append(contract_val + liability_val)

    min_exp = min(financial_exposures) if financial_exposures else 0
    max_exp = max(financial_exposures) if financial_exposures else 0

    # Second pass: calculate all risks
    for c in contracts:
        contract_val = parse_contract_value(c['contract_value'])
        liability_val = float(c['total_liability']) if c['total_liability'] else 0

        # Get risks (use history if version provided)
        overall_risk = get_contract_overall_risk(c['id'], c['full_text'], version=version)
        dimension_risks = get_contract_dimension_risks(
            c['id'], c['contract_value'], c['total_liability'], c['full_text'], version=version
        )

        # Combined legal/IP risk
        legal_ip_risk = round((overall_risk + dimension_risks['ip_risk']) / 2, 2)

        # Financial exposure
        financial_exposure = contract_val + liability_val

        data.append({
            'x': normalize(financial_exposure, min_exp, max_exp),
            'y': legal_ip_risk,
            'label': c['filename'],
            'contract_id': c['id'],
            'business_unit': c['business_unit'] or 'Others',
            'color': get_bu_color(c['business_unit'] or 'Others')
        })

    return JsonResponse(data, safe=False)


@require_http_methods(["GET"])
def contract_risk_timeline(request, contract_id):
    """
    Get risk timeline for a specific contract across versions
    Used for time-slider visualization
    """
    records = ContractRiskHistory.objects.filter(
        contract_id=contract_id
    ).order_by('version').values(
        'version', 'overall_risk', 'ip_risk', 'liability_risk', 'geography_risk', 'recorded_at'
    )

    data = list(records)
    return JsonResponse(data, safe=False)


@require_http_methods(["GET"])
def get_available_versions(request):
    """
    Get list of available contract versions for time slider
    Queries ContractRiskHistory to get actual versioned data
    """
    user_id = request.GET.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'user_id required'}, status=400)

    # Get contract IDs for this user
    contract_ids = Contract.objects.filter(user_id=user_id).values_list('id', flat=True)

    # Get versions from ContractRiskHistory table
    versions = ContractRiskHistory.objects.filter(
        contract_id__in=contract_ids
    ).values_list('version', flat=True).distinct().order_by('version')

    versions_list = list(versions)

    return JsonResponse({
        'versions': versions_list,
        'min': min(versions_list) if versions_list else 1,
        'max': max(versions_list) if versions_list else 1
    })
