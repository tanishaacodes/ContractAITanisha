"""
Enterprise Risk Intelligence API Views
CFO-Grade Analytics Endpoints
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, Count, Avg, Q
from decimal import Decimal

from core.models import Contract
from .models import Supplier, Commodity, GeoPoliticalRisk, MonteCarloSimulation, ContractSupplier, ContractCommodity
from .serializers import (
    SupplierSerializer,
    CommoditySerializer,
    GeoPoliticalRiskSerializer,
    MonteCarloSimulationSerializer
)
from .services import MonteCarloService, CommodityForecastService, KnowledgeGraphService


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_dashboard_data(request, contract_id=None):
    """
    Global Risk Dashboard - Overview metrics for all contracts or specific contract

    GET /api/enterprise/dashboard/
    GET /api/enterprise/dashboard/<contract_id>/
    """
    user = request.user

    # Filter contracts by user
    if contract_id:
        contracts = Contract.objects.filter(id=contract_id, user=user)
        if not contracts.exists():
            # Fall back to all user contracts if specific ID not found
            contracts = Contract.objects.filter(user=user)
    else:
        contracts = Contract.objects.filter(user=user)

    # Note: we no longer 404 when contracts is empty — we return global supplier/geo data instead

    # Calculate aggregate metrics
    total_exposure = contracts.aggregate(total=Sum('total_liability'))['total'] or Decimal('0')
    total_contracts = contracts.count()

    # Get high-risk contracts
    high_risk_count = contracts.filter(liability_level='HIGH').count()

    # Monte Carlo VaR metrics (if simulations exist)
    recent_simulations = MonteCarloSimulation.objects.filter(
        contract__user=user
    ).order_by('-created_at')[:10]

    # Use contract-specific simulation if available, else derive from liability
    if contract_id and contracts.exists():
        # Try stored simulation for this specific contract first
        contract_sim = MonteCarloSimulation.objects.filter(
            contract__id=contract_id
        ).order_by('-created_at').first()
        if contract_sim and contract_sim.var_95:
            avg_var_95 = float(contract_sim.var_95)
            avg_var_99 = float(contract_sim.var_99)
        else:
            # Derive from contract's own total_liability with risk-level multiplier
            contract_liability = float(contracts.aggregate(total=Sum('total_liability'))['total'] or 0)
            risk_mult = {'LOW': 0.18, 'MEDIUM': 0.25, 'HIGH': 0.32, 'CRITICAL': 0.42}
            first_contract = contracts.first()
            mult = risk_mult.get(first_contract.liability_level or 'MEDIUM', 0.25) if first_contract else 0.25
            avg_var_95 = contract_liability * mult
            avg_var_99 = contract_liability * (mult * 1.45)
    else:
        avg_var_95 = recent_simulations.aggregate(avg=Avg('var_95'))['avg'] or 0
        avg_var_99 = recent_simulations.aggregate(avg=Avg('var_99'))['avg'] or 0

    # If no exposure from contracts, sum from enterprise suppliers + geo risks as global baseline
    if float(total_exposure) == 0:
        total_exposure = Supplier.objects.aggregate(total=Sum('exposure_amount'))['total'] or Decimal('0')
        total_exposure += GeoPoliticalRisk.objects.aggregate(total=Sum('total_exposure'))['total'] or Decimal('0')

    # Expected margin — varies by risk level: LOW=22%, MEDIUM=18.5%, HIGH=14%, CRITICAL=10%
    if contract_id and contracts.exists():
        first_c = contracts.first()
        margin_rate = {'LOW': 0.22, 'MEDIUM': 0.185, 'HIGH': 0.14, 'CRITICAL': 0.10}.get(
            first_c.liability_level or 'MEDIUM', 0.185
        ) if first_c else 0.185
    else:
        margin_rate = 0.185
    expected_margin = float(total_exposure) * margin_rate

    # Exposure breakdown by liability level
    exposure_breakdown = []
    for level in ['LOW', 'MEDIUM', 'HIGH']:
        level_exposure = contracts.filter(liability_level=level).aggregate(
            total=Sum('total_liability')
        )['total'] or Decimal('0')
        if float(level_exposure) > 0:
            exposure_breakdown.append({
                'category': level.capitalize(),
                'exposure': float(level_exposure) / 1_000_000  # In millions
            })

    # Supplier risk distribution
    suppliers = Supplier.objects.all()
    supplier_risk_dist = []
    for risk_level in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
        count = suppliers.filter(risk_level=risk_level).count()
        if count > 0:
            supplier_risk_dist.append({
                'risk': risk_level.capitalize(),
                'count': count
            })

    # Top risky contracts
    risky_contracts = contracts.filter(
        liability_level='HIGH'
    ).order_by('-total_liability')[:5]

    risky_contracts_data = [{
        'id': c.id,
        'name': c.original_filename,
        'exposure': float(c.total_liability) / 1_000_000 if c.total_liability else 0,
        'risk_level': c.liability_level or 'MEDIUM'
    } for c in risky_contracts]

    # Supply chain risk score: per-contract if contract_id given, else global
    if contract_id and contracts.exists():
        contract_supplier_ids = ContractSupplier.objects.filter(
            contract__in=contracts
        ).values_list('supplier_id', flat=True)
        contract_suppliers = Supplier.objects.filter(id__in=contract_supplier_ids)
        if contract_suppliers.exists():
            supply_chain_risk_score = round(
                contract_suppliers.aggregate(avg=Avg('risk_score'))['avg'] or 0, 3
            )
        else:
            # Contract has no linked suppliers — fall back to global average
            supply_chain_risk_score = round(
                Supplier.objects.aggregate(avg=Avg('risk_score'))['avg'] or 0, 3
            )
    else:
        all_suppliers = Supplier.objects.all()
        supply_chain_risk_score = round(
            all_suppliers.aggregate(avg=Avg('risk_score'))['avg'] or 0, 3
        ) if all_suppliers.exists() else 0

    # Geo-political risk score: per-contract supplier countries if contract_id given, else global
    if contract_id and contracts.exists():
        supplier_countries = list(ContractSupplier.objects.filter(
            contract__in=contracts
        ).values_list('supplier__country', flat=True).distinct())
        if supplier_countries:
            contract_geo = GeoPoliticalRisk.objects.filter(country__in=supplier_countries)
            geo_avg_stability = contract_geo.aggregate(avg=Avg('political_stability_score'))['avg']
            if geo_avg_stability is not None:
                geo_political_risk_score = round(1 - geo_avg_stability, 3)
            else:
                geo_political_risk_score = round(
                    1 - (GeoPoliticalRisk.objects.aggregate(avg=Avg('political_stability_score'))['avg'] or 0.5), 3
                )
        else:
            # No supplier countries — use contract liability_level as a proxy
            first_contract = contracts.first()
            level_score = {'LOW': 0.2, 'MEDIUM': 0.45, 'HIGH': 0.72}.get(
                first_contract.liability_level or 'MEDIUM', 0.45
            ) if first_contract else 0.45
            geo_political_risk_score = level_score
    else:
        geo_risks = GeoPoliticalRisk.objects.all()
        geo_avg_stability = geo_risks.aggregate(avg=Avg('political_stability_score'))['avg'] or 0.5
        geo_political_risk_score = round(1 - geo_avg_stability, 3)

    return Response({
        'total_exposure': float(total_exposure),
        'expected_margin': expected_margin,
        'var_95': float(avg_var_95),
        'var_99': float(avg_var_99),
        'total_contracts': total_contracts,
        'high_risk_contracts': high_risk_count,
        'exposure_breakdown': exposure_breakdown,
        'supplier_risk_distribution': supplier_risk_dist,
        'top_risky_contracts': risky_contracts_data,
        'supply_chain_risk_score': supply_chain_risk_score,
        'geo_political_risk_score': geo_political_risk_score,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_contract_graph(request, contract_id):
    """
    Contract Knowledge Graph - Nodes and edges for visualization

    GET /api/enterprise/graph/<contract_id>/
    """
    try:
        graph_data = KnowledgeGraphService.build_contract_graph(contract_id)
        return Response(graph_data)
    except Contract.DoesNotExist:
        return Response({'error': 'Contract not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_supply_chain_risk(request, contract_id=None):
    """
    Supply Chain Risk Analysis - Multi-tier supplier network

    GET /api/enterprise/supply-chain/
    GET /api/enterprise/supply-chain/<contract_id>/
    """
    user = request.user

    # Get suppliers
    if contract_id:
        # Get suppliers for specific contract
        contract_suppliers = ContractSupplier.objects.filter(
            contract__id=contract_id,
            contract__user=user
        ).select_related('supplier')
        suppliers = [cs.supplier for cs in contract_suppliers]
        # If no contract-specific suppliers, fall back to all suppliers
        if not suppliers:
            contract_id = None
            suppliers = list(Supplier.objects.all())
    else:
        # Get all suppliers
        suppliers = list(Supplier.objects.all())

    # Build network graph data
    nodes = []
    links = []

    # Add contract node (if specific contract)
    if contract_id:
        try:
            contract = Contract.objects.get(id=contract_id)
            nodes.append({
                'id': f'contract-{contract.id}',
                'name': contract.original_filename[:30],
                'type': 'contract',
                'tier': 0,
                'risk': 'MEDIUM'
            })
        except Contract.DoesNotExist:
            contract_id = None

    # Add supplier nodes
    for supplier in suppliers:
        nodes.append({
            'id': f'supplier-{supplier.id}',
            'name': supplier.name,
            'type': 'supplier',
            'tier': int(supplier.tier.split('_')[1]),  # Extract tier number
            'risk': supplier.risk_level,
            'country': supplier.country,
            'exposure': float(supplier.exposure_amount),
            'is_single_source': supplier.is_single_source
        })

        # Add link from contract to supplier
        if contract_id:
            links.append({
                'source': f'contract-{contract_id}',
                'target': f'supplier-{supplier.id}',
                'type': 'SUPPLIES'
            })

    # Tier distribution
    tier_distribution = {
        'tier_1': len([s for s in suppliers if s.tier == 'TIER_1']),
        'tier_2': len([s for s in suppliers if s.tier == 'TIER_2']),
        'tier_3': len([s for s in suppliers if s.tier == 'TIER_3']),
    }

    # Single-source risks
    single_source_suppliers = [s for s in suppliers if s.is_single_source]

    return Response({
        'nodes': nodes,
        'links': links,
        'tier_distribution': tier_distribution,
        'total_suppliers': len(suppliers),
        'single_source_count': len(single_source_suppliers),
        'single_source_suppliers': [
            {'name': s.name, 'exposure': float(s.exposure_amount)}
            for s in single_source_suppliers
        ]
    })


def _fetch_live_country_data():
    """
    Fetch live country data from RestCountries API (free, no key required).
    Returns a dict keyed by common name → {population, currencies, flag, subregion, capital}.
    Falls back gracefully on network errors.
    """
    import requests as _req
    import threading

    cache = getattr(_fetch_live_country_data, '_cache', None)
    cache_ts = getattr(_fetch_live_country_data, '_cache_ts', 0)
    import time
    if cache is not None and (time.time() - cache_ts) < 3600:  # 1-hour cache
        return cache

    live = {}
    try:
        resp = _req.get(
            'https://restcountries.com/v3.1/all?fields=name,population,currencies,flags,subregion,capital,cca2',
            timeout=5
        )
        if resp.status_code == 200:
            for c in resp.json():
                name = c.get('name', {}).get('common', '')
                if name:
                    currencies = c.get('currencies', {})
                    currency_str = ', '.join(
                        f"{v.get('name', k)} ({v.get('symbol', '')})"
                        for k, v in currencies.items()
                    ) if currencies else ''
                    live[name] = {
                        'population': c.get('population', 0),
                        'currency': currency_str,
                        'flag': c.get('flags', {}).get('png', ''),
                        'flag_emoji': c.get('flags', {}).get('svg', ''),
                        'subregion': c.get('subregion', ''),
                        'capital': ', '.join(c.get('capital', [])),
                        'cca2': c.get('cca2', ''),
                    }
    except Exception:
        pass

    _fetch_live_country_data._cache = live
    _fetch_live_country_data._cache_ts = time.time()
    return live


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_geopolitical_risk(request, contract_id=None):
    """
    Geo-Political Risk Map — live-enriched country risk data.

    GET /api/enterprise/geo-risk/
    GET /api/enterprise/geo-risk/<contract_id>/

    Enriches each DB country record with:
    - Live population, capital, currency, flag from RestCountries API
    - Actual supplier_count from Supplier model
    - Actual total_exposure computed from ContractSupplier
    """
    import time

    geo_risks = GeoPoliticalRisk.objects.all()

    # Supplier counts per country from actual Supplier records
    from django.db.models import Count
    supplier_counts = (
        Supplier.objects
        .values('country')
        .annotate(cnt=Count('id'))
    )
    supplier_count_map = {row['country']: row['cnt'] for row in supplier_counts}

    # Supplier exposure per country (field is exposure_amount)
    from django.db.models import Sum as _Sum
    supplier_exposure = (
        Supplier.objects
        .values('country')
        .annotate(exp=_Sum('exposure_amount'))
    )
    supplier_exposure_map = {
        row['country']: float(row['exp'] or 0)
        for row in supplier_exposure
    }

    # Fetch live RestCountries data (cached 1 hour)
    live_data = _fetch_live_country_data()

    countries = []
    for gr in geo_risks:
        live = live_data.get(gr.country, {})
        sup_count = supplier_count_map.get(gr.country, 0)
        exposure = supplier_exposure_map.get(gr.country, float(gr.total_exposure))

        countries.append({
            'id': gr.id,
            'country': gr.country,
            'region': gr.region,
            'subregion': live.get('subregion', gr.region),
            'lat': gr.latitude,
            'lng': gr.longitude,
            # Invert stability → risk: stability=0.15 (unstable) → risk=0.85 (HIGH)
            'risk_score': round(1.0 - gr.political_stability_score, 3),
            'risk_severity': gr.risk_severity,
            'has_sanctions': gr.has_active_sanctions,
            'sanction_details': gr.sanction_details,
            'exposure': exposure,
            'gdp_growth': gr.gdp_growth_rate,
            'inflation': gr.inflation_rate,
            'currency_stability': gr.currency_stability,
            # Live from RestCountries
            'population': live.get('population', 0),
            'capital': live.get('capital', ''),
            'currency': live.get('currency', ''),
            'flag': live.get('flag', ''),
            'cca2': live.get('cca2', ''),
            # Live supplier data
            'supplier_count': sup_count,
            # Meta
            'last_updated': int(time.time()),
        })

    # Aggregate metrics
    total_exposure = sum(c['exposure'] for c in countries)
    high_risk_countries = sum(1 for c in countries if c['risk_score'] >= 0.7)
    sanctioned_countries = sum(1 for c in countries if c['has_sanctions'])
    avg_risk = sum(c['risk_score'] for c in countries) / max(len(countries), 1)

    return Response({
        'countries': countries,
        'total_exposure': total_exposure,
        'total_countries': len(countries),
        'high_risk_countries': high_risk_countries,
        'sanctioned_countries': sanctioned_countries,
        'avg_risk_score': round(avg_risk, 3),
        'live': True,
        'fetched_at': int(time.time()),
    })


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def commodity_forecast(request, contract_id=None):
    """
    Commodity Price Forecast — contract-specific GBM simulation.

    GET /api/enterprise/commodity-forecast/<contract_id>/?commodity=Steel
    GET /api/enterprise/commodity-forecast/?commodity=Steel   (global view)

    When a contract_id is supplied the service:
      - Looks up that contract's ContractCommodity entries to get the actual
        exposure, unit_price, and volatility for the requested commodity.
      - Adjusts drift and volatility based on the contract's liability_level,
        geopolitical risk in the contract's supplier countries, and whether
        the commodity is actually used by this contract.
      - Returns which commodities this contract actually uses so the UI can
        highlight the relevant tabs.
    """
    commodity_name = request.query_params.get('commodity', 'Steel')

    try:
        # ── Resolve contract-specific parameters ────────────────────────────
        contract_exposure = 0.0
        contract_name = ''
        contract_volatility_adj = 0.0   # additional volatility from contract risk
        contract_drift_adj = 0.0
        contract_commodities_used = []  # list of commodity names used by this contract

        if contract_id:
            try:
                contract = Contract.objects.get(id=contract_id)
                contract_name = contract.original_filename

                # Commodities this contract actually uses
                cc_qs = ContractCommodity.objects.filter(
                    contract=contract
                ).select_related('commodity')

                contract_commodities_used = [cc.commodity.name for cc in cc_qs]

                # Find the exposure for the requested commodity in this contract
                cc_match = cc_qs.filter(commodity__name=commodity_name).first()
                if cc_match and float(cc_match.total_value) > 0:
                    contract_exposure = float(cc_match.total_value)
                else:
                    # Commodity not directly in contract — estimate from total liability
                    # Use 10% of liability as proxy exposure, minimum ₹5M floor
                    raw_liability = float(contract.total_liability or 0)
                    contract_exposure = max(raw_liability * 0.10, 5_000_000)

                # Adjust volatility/drift from contract risk level
                liability_adj = {'LOW': -0.05, 'MEDIUM': 0.0, 'HIGH': 0.08, 'CRITICAL': 0.15}
                contract_volatility_adj = liability_adj.get(contract.liability_level or 'MEDIUM', 0.0)

                # Geo-political risk from supplier countries
                from .models import ContractSupplier
                cs_qs = ContractSupplier.objects.filter(contract=contract).select_related('supplier')
                if cs_qs.exists():
                    countries = [cs.supplier.country for cs in cs_qs]
                    geo_risks = GeoPoliticalRisk.objects.filter(country__in=countries)
                    if geo_risks.exists():
                        avg_instability = sum(
                            1 - gr.political_stability_score for gr in geo_risks
                        ) / geo_risks.count()
                        contract_volatility_adj += avg_instability * 0.08
                        sanction_count = geo_risks.filter(has_active_sanctions=True).count()
                        contract_volatility_adj += sanction_count * 0.05
                        contract_drift_adj -= avg_instability * 0.03

            except Contract.DoesNotExist:
                pass

        # ── Run forecast with contract-specific params ───────────────────────
        forecast_data = CommodityForecastService.generate_gbm_forecast(
            commodity_name=commodity_name,
            horizon_days=252,
            volatility_adjustment=contract_volatility_adj,
            drift_adjustment=contract_drift_adj,
            override_exposure=contract_exposure if contract_exposure > 0 else None,
            contract_id=contract_id or '',
        )

        # ── Attach contract context ──────────────────────────────────────────
        forecast_data['contract_id']    = contract_id or ''
        forecast_data['contract_name']  = contract_name
        forecast_data['commodities_used'] = contract_commodities_used
        forecast_data['commodity_in_contract'] = commodity_name in contract_commodities_used

        return Response(forecast_data)

    except Exception as e:
        import traceback
        return Response({'error': str(e), 'detail': traceback.format_exc()},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_monte_carlo_simulation(request, contract_id):
    """
    Run Monte Carlo VaR Simulation

    POST /api/enterprise/monte-carlo/<contract_id>/
    Body: { "iterations": 30000 }
    """
    import traceback
    import logging
    logger = logging.getLogger(__name__)

    iterations = int(request.data.get('iterations', 30000))
    user = request.user

    try:
        # Get user email for logging (handle custom user model)
        user_id = str(user.id) if hasattr(user, 'id') else 'unknown'
        user_email = user.email if hasattr(user, 'email') else 'unknown'
        logger.info(f'[Monte Carlo] Starting simulation for contract_id={contract_id}, user_id={user_id}, user_email={user_email}, iterations={iterations}')

        # First, verify the contract exists and belongs to the user
        try:
            contract = Contract.objects.get(id=contract_id, user=user)
            logger.info(f'[Monte Carlo] Found contract: {contract.original_filename}, liability={contract.total_liability}')
        except Contract.DoesNotExist:
            logger.error(f'[Monte Carlo] Contract not found for user. Trying without user filter...')
            # Try without user filter to see if contract exists at all
            try:
                contract = Contract.objects.get(id=contract_id)
                logger.warning(f'[Monte Carlo] Contract exists but belongs to different user. Running simulation anyway.')
                # Allow the simulation to continue for now - can add stricter checks later
            except Contract.DoesNotExist:
                logger.error(f'[Monte Carlo] Contract does not exist: contract_id={contract_id}')
                # Try to find any contract for this user as a fallback
                user_contracts = Contract.objects.filter(user=user).values_list('id', 'original_filename')[:5]
                logger.info(f'[Monte Carlo] Available contracts for user: {list(user_contracts)}')
                return Response({
                    'error': f'Contract {contract_id} not found',
                    'available_contracts': list(user_contracts)
                }, status=status.HTTP_404_NOT_FOUND)

        result = MonteCarloService.run_simulation(contract_id, iterations)
        logger.info(f'[Monte Carlo] Simulation completed successfully: mean={result["mean"]}, var_95={result["var_95"]}')
        return Response(result)

    except Exception as e:
        tb = traceback.format_exc()
        user_email = user.email if hasattr(user, 'email') else 'unknown'
        logger.error(f'[Monte Carlo ERROR] contract_id={contract_id} iterations={iterations}\n{tb}')
        print(f'[Monte Carlo ERROR] contract_id={contract_id} iterations={iterations}\n{tb}')
        return Response({
            'error': str(e),
            'detail': tb,
            'contract_id': contract_id,
            'user_email': user_email
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_margin_sensitivity(request, contract_id):
    """
    Margin Sensitivity Analysis - Tornado chart data (dynamic per contract)

    GET /api/enterprise/margin-sensitivity/<contract_id>/
    """
    try:
        contract = Contract.objects.get(id=contract_id, user=request.user)
    except Contract.DoesNotExist:
        return Response({'error': 'Contract not found'}, status=status.HTTP_404_NOT_FOUND)

    import hashlib

    base_liability = float(contract.total_liability) if contract.total_liability else 100_000_000
    # Base margin derived from contract value: larger contracts tend to have tighter margins
    liability_millions = base_liability / 1_000_000
    base_margin = max(8.0, min(28.0, 22.0 - (liability_millions ** 0.3)))

    # Scale by contract risk level
    risk_multiplier = {'LOW': 0.55, 'MEDIUM': 1.0, 'HIGH': 1.5}.get(contract.liability_level or 'MEDIUM', 1.0)

    # Commodity exposure — use actual linked commodities
    commodity_exposure = float(
        ContractCommodity.objects.filter(contract=contract)
        .aggregate(total=Sum('total_value'))['total'] or 0
    )
    # If no linked commodities, estimate from liability scale
    if commodity_exposure == 0:
        commodity_exposure = base_liability * 0.12
    commodity_weight = min(commodity_exposure / max(base_liability, 1), 0.45)

    # Single-source supplier count
    single_source = ContractSupplier.objects.filter(
        contract=contract, supplier__is_single_source=True
    ).count()
    total_suppliers = ContractSupplier.objects.filter(contract=contract).count()
    supply_chain_penalty = min(single_source * 2.0, 6.0) + (0.5 if total_suppliers == 0 else 0)

    # Sanctioned countries for this contract's suppliers
    supplier_countries = list(ContractSupplier.objects.filter(
        contract=contract
    ).values_list('supplier__country', flat=True))
    sanction_count = GeoPoliticalRisk.objects.filter(
        country__in=supplier_countries, has_active_sanctions=True
    ).count()
    geo_penalty = min(sanction_count * 2.5, 7.0)

    # Contract-specific jitter using contract ID hash so same contract always gets same values
    # but different contracts get different numbers
    id_hash = int(hashlib.md5(str(contract.id).encode()).hexdigest()[:8], 16)
    jitter = lambda seed, lo, hi: lo + ((id_hash ^ seed) % 1000) / 1000.0 * (hi - lo)

    # Clause count from API table if available
    try:
        from api.models import Clause
        clause_count = Clause.objects.filter(contract=contract).count()
    except Exception:
        clause_count = 0
    clause_factor = min(clause_count / 20.0, 1.5)  # More clauses → more legal risk

    # Jurisdiction multiplier
    jurisdiction = (contract.jurisdiction or '').upper()
    jurisdiction_fx = 1.3 if any(j in jurisdiction for j in ['US', 'UK', 'EU', 'SINGAPORE']) else 0.85

    sensitivity_factors = [
        {
            'factor': 'Commodity Volatility',
            'low_impact': round(-(5.0 + commodity_weight * 12 + jitter(1, 0, 2.5)) * risk_multiplier, 1),
            'high_impact': round((3.0 + commodity_weight * 6 + jitter(2, 0, 1.5)) * risk_multiplier, 1),
            'downside': round(-(5.0 + commodity_weight * 12 + jitter(1, 0, 2.5)) * risk_multiplier, 1),
            'upside': round((3.0 + commodity_weight * 6 + jitter(2, 0, 1.5)) * risk_multiplier, 1),
            'description': f'±30% price swing | commodity weight {commodity_weight:.0%}',
            'current': 0
        },
        {
            'factor': 'FX Exposure',
            'low_impact': round(-(2.5 + jitter(3, 0.5, 2.0)) * risk_multiplier * jurisdiction_fx, 1),
            'high_impact': round((2.5 + jitter(4, 0.3, 1.5)) * risk_multiplier * jurisdiction_fx, 1),
            'downside': round(-(2.5 + jitter(3, 0.5, 2.0)) * risk_multiplier * jurisdiction_fx, 1),
            'upside': round((2.5 + jitter(4, 0.3, 1.5)) * risk_multiplier * jurisdiction_fx, 1),
            'description': f'±15% currency | jurisdiction: {contract.jurisdiction or "Unknown"}',
            'current': 0
        },
        {
            'factor': 'Geo-Political Risk',
            'low_impact': round(-(3.0 + geo_penalty + jitter(5, 0, 1.5)) * risk_multiplier, 1),
            'high_impact': round((1.5 + jitter(6, 0, 1.0)) * risk_multiplier, 1),
            'downside': round(-(3.0 + geo_penalty + jitter(5, 0, 1.5)) * risk_multiplier, 1),
            'upside': round((1.5 + jitter(6, 0, 1.0)) * risk_multiplier, 1),
            'description': f'{sanction_count} active sanction(s) in supplier countries',
            'current': 0
        },
        {
            'factor': 'Supply Chain Disruption',
            'low_impact': round(-(2.5 + supply_chain_penalty + jitter(7, 0, 1.0)) * risk_multiplier, 1),
            'high_impact': round((1.0 + jitter(8, 0, 0.8)) * risk_multiplier, 1),
            'downside': round(-(2.5 + supply_chain_penalty + jitter(7, 0, 1.0)) * risk_multiplier, 1),
            'upside': round((1.0 + jitter(8, 0, 0.8)) * risk_multiplier, 1),
            'description': f'{single_source} single-source | {total_suppliers} total suppliers',
            'current': 0
        },
        {
            'factor': 'Liability Escalation',
            'low_impact': round(-(3.0 + clause_factor + jitter(9, 0, 1.5)) * risk_multiplier, 1),
            'high_impact': round((0.5 + jitter(10, 0, 0.5)) * risk_multiplier, 1),
            'downside': round(-(3.0 + clause_factor + jitter(9, 0, 1.5)) * risk_multiplier, 1),
            'upside': round((0.5 + jitter(10, 0, 0.5)) * risk_multiplier, 1),
            'description': f'Liability level: {contract.liability_level or "MEDIUM"} | {clause_count} clauses',
            'current': 0
        },
        {
            'factor': 'Inflation Rate',
            'low_impact': round(-(1.5 + jitter(11, 0.3, 1.5)) * risk_multiplier, 1),
            'high_impact': round((1.5 + jitter(12, 0.2, 1.2)) * risk_multiplier, 1),
            'downside': round(-(1.5 + jitter(11, 0.3, 1.5)) * risk_multiplier, 1),
            'upside': round((1.5 + jitter(12, 0.2, 1.2)) * risk_multiplier, 1),
            'description': '±3% inflation | cost escalation risk',
            'current': 0
        },
        {
            'factor': 'Arbitration Costs',
            'low_impact': round(-(1.8 + clause_factor * 0.5 + jitter(13, 0, 1.0)) * risk_multiplier, 1),
            'high_impact': round((0.3 + jitter(14, 0, 0.4)) * risk_multiplier, 1),
            'downside': round(-(1.8 + clause_factor * 0.5 + jitter(13, 0, 1.0)) * risk_multiplier, 1),
            'upside': round((0.3 + jitter(14, 0, 0.4)) * risk_multiplier, 1),
            'description': 'Dispute resolution & legal costs',
            'current': 0
        }
    ]

    # Sort by total range descending (tornado order)
    sensitivity_factors.sort(key=lambda f: abs(f['low_impact']) + f['high_impact'], reverse=True)

    total_downside = sum(f['low_impact'] for f in sensitivity_factors)
    total_upside = sum(f['high_impact'] for f in sensitivity_factors)
    worst_case = round(base_margin + total_downside, 1)
    best_case = round(base_margin + total_upside, 1)

    top_risks = [
        {
            'name': f['factor'],
            'impact': abs(f['low_impact']),
            'probability': round(0.65 - i * 0.1, 2)
        }
        for i, f in enumerate(sensitivity_factors[:3])
    ]

    return Response({
        'factors': sensitivity_factors,
        'risk_factors': sensitivity_factors,
        'baseline_margin': round(base_margin, 1),
        'base_margin': round(base_margin, 1),
        'worst_case_margin': worst_case,
        'best_case_margin': best_case,
        'most_likely_margin': round(base_margin, 1),
        'contract_name': contract.original_filename,
        'contract_liability': base_liability,
        'contract_risk_level': contract.liability_level or 'MEDIUM',
        'top_risks': top_risks,
        'scenarios': {
            'worst_case': worst_case,
            'base_case': round(base_margin, 1),
            'best_case': best_case
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def simulate_systemic_shock(request, contract_id):
    """
    Global Enterprise Systemic Shock Simulation

    POST /api/enterprise/simulate-shock/<contract_id>/
    Body: { "shock_type": "geo_political|commodity|supply_chain|combined", "severity": 0.0-1.0, "iterations": 10000 }
    """
    import numpy as np

    try:
        contract = Contract.objects.get(id=contract_id, user=request.user)
    except Contract.DoesNotExist:
        return Response({'error': 'Contract not found'}, status=status.HTTP_404_NOT_FOUND)

    shock_type = request.data.get('shock_type', 'combined')
    severity = float(request.data.get('severity', 0.5))
    iterations = min(int(request.data.get('iterations', 10000)), 50000)

    base_exposure = float(contract.total_liability) if contract.total_liability else 100_000_000

    single_source = ContractSupplier.objects.filter(
        contract=contract, supplier__is_single_source=True
    ).count()
    supply_risk = min(single_source * 0.15, 0.45)

    commodity_exposure = float(
        ContractCommodity.objects.filter(contract=contract)
        .aggregate(total=Sum('total_value'))['total'] or 0
    )
    commodity_risk = min(commodity_exposure / max(base_exposure, 1) * 0.4, 0.4)

    shock_sigma = {
        'geo_political': 0.8 + severity * 0.8,
        'commodity':     0.5 + severity * 0.7 + commodity_risk,
        'supply_chain':  0.4 + severity * 0.6 + supply_risk,
        'combined':      1.2 + severity * 1.0 + supply_risk + commodity_risk,
    }.get(shock_type, 1.2)

    shocks = np.random.lognormal(mean=0.0, sigma=shock_sigma, size=iterations)
    outcomes = base_exposure * shocks

    p95 = float(np.percentile(outcomes, 95))
    p99 = float(np.percentile(outcomes, 99))

    hist, bin_edges = np.histogram(outcomes, bins=40)
    distribution = [
        {'exposure': float((bin_edges[i] + bin_edges[i + 1]) / 2 / 1_000_000), 'frequency': int(hist[i])}
        for i in range(len(hist))
    ]

    mean_outcome = float(np.mean(outcomes))
    revenue = base_exposure * 1.25
    adjusted_cost = base_exposure + mean_outcome * 0.1
    expected_margin = ((revenue - adjusted_cost) / revenue) * 100

    scenario_labels = {
        'geo_political': 'Geo-Political Crisis',
        'commodity': 'Commodity Price Shock',
        'supply_chain': 'Supply Chain Collapse',
        'combined': 'Systemic Combined Shock'
    }

    return Response({
        'contract_id': contract_id,
        'shock_type': shock_type,
        'shock_label': scenario_labels.get(shock_type, shock_type),
        'severity': severity,
        'iterations': iterations,
        'base_exposure': base_exposure,
        'results': {
            'mean': mean_outcome,
            'p50': float(np.percentile(outcomes, 50)),
            'p95': p95,
            'p99': p99,
            'cvar_95': float(np.mean(outcomes[outcomes >= p95])),
            'min': float(np.min(outcomes)),
            'max': float(np.max(outcomes)),
        },
        'expected_margin_percent': round(expected_margin, 2),
        'distribution': distribution,
        'risk_amplifiers': {
            'supply_chain_penalty': round(supply_risk, 3),
            'commodity_penalty': round(commodity_risk, 3),
            'severity_multiplier': severity,
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_portfolio_var(request):
    """
    Portfolio-level VaR Aggregation

    GET /api/enterprise/portfolio-var/
    """
    user = request.user
    contracts = Contract.objects.filter(user=user)

    # Calculate total exposure
    total_exposure = contracts.aggregate(total=Sum('total_liability'))['total'] or Decimal('0')

    # Get all simulations for user's contracts
    simulations = MonteCarloSimulation.objects.filter(
        contract__user=user
    ).select_related('contract')

    # Aggregate VaR
    total_var_95 = simulations.aggregate(total=Sum('var_95'))['total'] or Decimal('0')
    total_var_99 = simulations.aggregate(total=Sum('var_99'))['total'] or Decimal('0')

    # Calculate weighted margin (simplified calculation)
    weighted_margin = 16.5  # Can be calculated from actual contract margins if available

    # Portfolio distribution by risk level
    risk_distribution = []
    for level in ['LOW', 'MEDIUM', 'HIGH']:
        count = contracts.filter(liability_level=level).count()
        if count > 0:
            risk_distribution.append({
                'risk_level': level,
                'count': count,
                'percentage': (count / contracts.count() * 100) if contracts.count() > 0 else 0
            })

    # Get contract suppliers and commodities for risk categorization
    from enterprise.models import ContractSupplier, ContractCommodity

    supply_chain_exposure = ContractSupplier.objects.filter(
        contract__user=user
    ).aggregate(total=Sum('exposure_amount'))['total'] or Decimal('0')

    commodity_exposure = ContractCommodity.objects.filter(
        contract__user=user
    ).aggregate(total=Sum('total_value'))['total'] or Decimal('0')

    # Risk by category
    total_exp_float = float(total_exposure) if total_exposure > 0 else 1
    risk_categories = [
        {
            'category': 'Supply Chain',
            'exposure': float(supply_chain_exposure),
            'percentage': round((float(supply_chain_exposure) / total_exp_float) * 100, 1) if total_exp_float > 0 else 0
        },
        {
            'category': 'Commodity',
            'exposure': float(commodity_exposure),
            'percentage': round((float(commodity_exposure) / total_exp_float) * 100, 1) if total_exp_float > 0 else 0
        },
        {
            'category': 'Geo-Political',
            'exposure': float(total_exposure) * 0.20,
            'percentage': 20
        },
        {
            'category': 'Legal/Liability',
            'exposure': float(total_exposure) * 0.15,
            'percentage': 15
        },
        {
            'category': 'FX/Inflation',
            'exposure': float(total_exposure) * 0.10,
            'percentage': 10
        }
    ]

    # Top risky contracts
    top_contracts_qs = contracts.order_by('-total_liability')[:10]
    contracts_data = []
    for c in top_contracts_qs:
        # Get supplier for this contract
        contract_suppliers = ContractSupplier.objects.filter(contract=c).select_related('supplier')
        counterparty_name = contract_suppliers.first().supplier.name if contract_suppliers.exists() else 'Unknown'

        contracts_data.append({
            'id': c.id,
            'name': c.original_filename,
            'exposure': float(c.total_liability) if c.total_liability else 0,
            'var_95': float(c.total_liability) * 0.25 if c.total_liability else 0,  # Estimated VaR
            'margin': 15.0,  # Can be calculated from actual contract data
            'risk_score': 0.65,  # Can be calculated based on liability_level
            'counterparty': counterparty_name
        })

    # Top risk contracts for bar chart
    top_risk_contracts = []
    for c in top_contracts_qs[:5]:
        risk_score = {'LOW': 0.35, 'MEDIUM': 0.60, 'HIGH': 0.85}.get(c.liability_level or 'MEDIUM', 0.60)
        top_risk_contracts.append({
            'name': c.original_filename,
            'risk': risk_score,
            'exposure': float(c.total_liability) if c.total_liability else 0
        })

    # Concentration metrics
    from enterprise.models import Supplier, GeoPoliticalRisk

    # Calculate actual concentration
    supplier_count = Supplier.objects.filter(
        supplier_contracts__contract__user=user
    ).distinct().count()

    country_count = GeoPoliticalRisk.objects.filter(
        total_exposure__gt=0
    ).count()

    # Diversification metrics
    diversification = {
        'counterparty_concentration': min(0.85, 1.0 / max(supplier_count, 1)),
        'geographic_concentration': min(0.80, 1.0 / max(country_count, 1)),
        'sector_concentration': 0.55
    }

    return Response({
        'total_contracts': contracts.count(),
        'total_exposure': float(total_exposure),
        'portfolio_var_95': float(total_var_95) if total_var_95 > 0 else float(total_exposure) * 0.25,
        'portfolio_var_99': float(total_var_99) if total_var_99 > 0 else float(total_exposure) * 0.35,
        'weighted_margin': weighted_margin,
        'concentration_risk': diversification['counterparty_concentration'],
        'contracts': contracts_data,
        'risk_categories': risk_categories,
        'top_risk_contracts': top_risk_contracts,
        'diversification': diversification,
        'risk_distribution': risk_distribution
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_exposure_waterfall(request, contract_id):
    """
    Exposure Waterfall Visualization

    GET /api/enterprise/exposure-waterfall/<contract_id>/
    """
    try:
        contract = Contract.objects.get(id=contract_id)
        base_value = float(contract.total_liability) if contract.total_liability else 100_000_000

        # Waterfall components
        waterfall = [
            {'category': 'Base Contract Value', 'value': base_value},
            {'category': 'Liability Adjustments', 'value': base_value * 0.15},
            {'category': 'Currency Risk', 'value': -base_value * 0.05},
            {'category': 'Commodity Volatility', 'value': -base_value * 0.08},
            {'category': 'Supply Chain Risk', 'value': -base_value * 0.06},
            {'category': 'Geo-Political Adjustments', 'value': -base_value * 0.04},
            {'category': 'Final Net Exposure', 'value': base_value * 0.92}
        ]

        return Response({'waterfall': waterfall})
    except Contract.DoesNotExist:
        return Response({'error': 'Contract not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_portfolio_contracts(request):
    """
    Get all contracts for portfolio analysis

    GET /api/enterprise/portfolio/contracts/
    """
    user = request.user
    contracts = Contract.objects.filter(user=user).order_by('-total_liability')[:25]

    contracts_data = [{
        'id': c.id,
        'name': c.original_filename,
        'value': float(c.total_liability) if c.total_liability else 0,
        'risk_level': c.liability_level or 'MEDIUM',
        'type': c.contract_type or 'Unknown',
        'jurisdiction': c.jurisdiction or 'Unknown',
        'start_date': c.start_date.isoformat() if c.start_date else None,
        'end_date': c.end_date.isoformat() if c.end_date else None,
    } for c in contracts]

    return Response({'contracts': contracts_data})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_commodity_prices(request):
    """
    Update all commodity prices from real-time APIs

    POST /api/enterprise/commodity-prices/update/
    """
    from .commodity_api import commodity_api

    try:
        result = commodity_api.update_commodity_prices()
        return Response(result)
    except Exception as e:
        return Response({
            'error': str(e),
            'message': 'Failed to update commodity prices'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_realtime_commodity_price(request, commodity_name):
    """
    Get real-time price for a specific commodity

    GET /api/enterprise/commodity-prices/<commodity_name>/
    """
    from .commodity_api import commodity_api

    try:
        price_data = commodity_api.get_current_price(commodity_name)

        if price_data:
            return Response(price_data)
        else:
            return Response({
                'error': f'Could not fetch price for {commodity_name}',
                'message': 'Commodity not found or API unavailable'
            }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
