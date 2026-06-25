"""
Force Majeure Intelligence Engine — API Views
==============================================
Endpoints:
  POST  /api/force-majeure/predict/              — FM risk prediction for a contract
  POST  /api/force-majeure/audit-clause/          — FM clause audit
  POST  /api/force-majeure/auto-correct/          — Auto-correct FM clause
  POST  /api/force-majeure/war-risk/              — War & geopolitical risk analysis
  POST  /api/force-majeure/simulate-scenario/     — Monte Carlo scenario simulation
  POST  /api/force-majeure/bulk-audit/            — Bulk portfolio FM clause audit
  GET   /api/force-majeure/predictions/           — List all FM predictions
  GET   /api/force-majeure/predictions/<id>/      — Get FM prediction detail
  GET   /api/force-majeure/clause-audits/         — List all clause audits
  GET   /api/force-majeure/alerts/                — List global FM alerts
  POST  /api/force-majeure/alerts/create/         — Create a global FM alert
  GET   /api/force-majeure/bayesian-graph/        — Bayesian network graph data (for viz)
  GET   /api/force-majeure/portfolio-summary/     — Portfolio-wide FM risk summary
"""
import logging
from typing import Any, Dict

from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from .models import FMPrediction, FMClauseAudit, FMScenario, FMWarRisk, FMGlobalAlert
from .fm_service import (
    predict_fm_risk,
    audit_fm_clause,
    auto_correct_fm_clause,
    analyze_war_risk,
    monte_carlo_loss,
    bulk_audit_contracts,
    suggest_mitigations,
    FM_EVENT_CATEGORIES,
)
from .bayesian_engine import (
    get_fm_bayesian_engine,
    LAYER1_EVENTS,
    LAYER2_DISRUPTIONS,
    LAYER3_SUPPLY,
    LAYER4_OUTCOMES,
    ALL_NODES,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. FM RISK PREDICT
# ---------------------------------------------------------------------------
class FMPredictView(APIView):
    """
    POST /api/force-majeure/predict/
    Body:
      {
        "contract_text": "...",
        "contract_id": "uuid",        (optional)
        "contract_title": "...",      (optional)
        "contract_value": 5000000,    (optional, USD)
        "jurisdiction": "India",      (optional)
        "industry": "EPC",            (optional)
        "evidence": {                 (optional manual evidence override)
          "war": 0.8,
          "trade_sanctions": 0.6
        }
      }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        data = request.data
        contract_text = data.get('contract_text', '')
        if not contract_text:
            return Response({'error': 'contract_text is required'}, status=status.HTTP_400_BAD_REQUEST)

        contract_id = data.get('contract_id', '')
        contract_title = data.get('contract_title', '')
        contract_value = float(data.get('contract_value', 0))
        jurisdiction = data.get('jurisdiction', '')
        industry = data.get('industry', '')
        manual_evidence = data.get('evidence', None)

        try:
            result = predict_fm_risk(
                contract_text=contract_text,
                contract_id=contract_id,
                contract_title=contract_title,
                contract_value=contract_value,
                jurisdiction=jurisdiction,
                industry=industry,
                manual_evidence=manual_evidence,
            )

            # Persist to DB
            try:
                with transaction.atomic():
                    pred = FMPrediction.objects.create(
                        contract_id=contract_id,
                        contract_title=contract_title,
                        contract_text=contract_text[:500],
                        fm_risk_score=result['fm_risk_score'],
                        fm_invocation_probability=result['fm_invocation_probability'],
                        project_delay_probability=result['project_delay_probability'],
                        cost_overrun_probability=result['cost_overrun_probability'],
                        contract_suspension_probability=result['contract_suspension_probability'],
                        contract_termination_probability=result['contract_termination_probability'],
                        event_probabilities=result['event_probabilities'],
                        expected_loss_usd=result['expected_loss_usd'],
                        worst_case_loss_usd=result['worst_case_loss_usd'],
                        p50_loss_usd=result['p50_loss_usd'],
                        p95_loss_usd=result['p95_loss_usd'],
                        p99_loss_usd=result['p99_loss_usd'],
                        bayesian_nodes=result['bayesian_nodes'],
                        top_risk_drivers=result['top_risk_drivers'],
                        causal_chain=result['causal_chain'],
                        clause_strength_score=result['clause_strength_score'],
                        missing_protections=result['missing_protections'],
                        covered_events=result['covered_events'],
                        explanation=result['explanation'],
                        mitigation_suggestions=result['mitigation_suggestions'],
                        contract_value=contract_value,
                        jurisdiction=jurisdiction,
                        industry=industry,
                    )
                    result['prediction_id'] = pred.id
            except Exception as db_err:
                logger.warning(f"FM prediction DB save failed: {db_err}")
                result['prediction_id'] = None

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"FM predict error: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ---------------------------------------------------------------------------
# 2. FM CLAUSE AUDIT
# ---------------------------------------------------------------------------
class FMAuditClauseView(APIView):
    """
    POST /api/force-majeure/audit-clause/
    Body:
      {
        "contract_text": "...",
        "contract_id": "uuid",
        "contract_title": "..."
      }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        data = request.data
        contract_text = data.get('contract_text', '')
        if not contract_text:
            return Response({'error': 'contract_text is required'}, status=status.HTTP_400_BAD_REQUEST)

        contract_id = data.get('contract_id', '')
        contract_title = data.get('contract_title', '')

        try:
            result = audit_fm_clause(contract_text, contract_id, contract_title)

            # Persist
            try:
                with transaction.atomic():
                    audit_obj = FMClauseAudit.objects.create(
                        contract_id=contract_id,
                        contract_title=contract_title,
                        raw_clause_text=result.get('raw_clause_text', ''),
                        status=result['status'],
                        strength_score=result['strength_score'],
                        covered_events=result['covered_events'],
                        missing_events=result['missing_events'],
                        benchmark_fidic_score=result.get('benchmark_fidic_score'),
                        benchmark_nec_score=result.get('benchmark_nec_score'),
                        benchmark_icc_score=result.get('benchmark_icc_score'),
                    )
                    result['audit_id'] = audit_obj.id
            except Exception as db_err:
                logger.warning(f"FM audit DB save failed: {db_err}")
                result['audit_id'] = None

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"FM audit error: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ---------------------------------------------------------------------------
# 3. FM AUTO-CORRECT CLAUSE
# ---------------------------------------------------------------------------
class FMAutoCorrectView(APIView):
    """
    POST /api/force-majeure/auto-correct/
    Body:
      {
        "contract_text": "...",
        "contract_id": "uuid",
        "use_llm": true
      }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        data = request.data
        contract_text = data.get('contract_text', '')
        contract_id = data.get('contract_id', '')
        use_llm = data.get('use_llm', False)  # Default False — use full rule-based clause

        if not contract_text:
            return Response({'error': 'contract_text is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            audit_result = audit_fm_clause(contract_text, contract_id)
            correction = auto_correct_fm_clause(contract_text, audit_result, use_llm=use_llm)

            # Update DB audit record if exists
            try:
                audit_qs = FMClauseAudit.objects.filter(contract_id=contract_id)
                if audit_qs.exists():
                    audit_obj = audit_qs.latest('created_at')
                    audit_obj.corrected_clause = correction['corrected_clause']
                    audit_obj.original_clause = correction['original_clause']
                    audit_obj.correction_applied = True
                    audit_obj.risk_reduction_before = correction['risk_reduction_before']
                    audit_obj.risk_reduction_after = correction['risk_reduction_after']
                    audit_obj.save()
            except Exception as db_err:
                logger.warning(f"FM auto-correct DB update failed: {db_err}")

            return Response(correction, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"FM auto-correct error: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ---------------------------------------------------------------------------
# 4. WAR RISK ANALYSIS
# ---------------------------------------------------------------------------
class FMWarRiskView(APIView):
    """
    POST /api/force-majeure/war-risk/
    Body:
      {
        "contract_text": "...",
        "contract_id": "uuid",
        "contract_title": "...",
        "contract_value": 5000000,
        "project_location": "Middle East",
        "supplier_locations": ["Turkey", "Ukraine"],
        "war_events": {                 (optional manual evidence)
          "military_invasion": 0.8,
          "trade_embargo": 0.6
        }
      }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        data = request.data
        contract_text = data.get('contract_text', '')
        contract_id = data.get('contract_id', '')
        contract_title = data.get('contract_title', '')
        contract_value = float(data.get('contract_value', 0))
        project_location = data.get('project_location', '')
        supplier_locations = data.get('supplier_locations', [])
        manual_war_events = data.get('war_events', None)

        try:
            result = analyze_war_risk(
                contract_text=contract_text,
                contract_id=contract_id,
                contract_title=contract_title,
                contract_value=contract_value,
                project_location=project_location,
                supplier_locations=supplier_locations,
                manual_war_events=manual_war_events,
            )

            # Persist
            try:
                with transaction.atomic():
                    war_obj = FMWarRisk.objects.create(
                        contract_id=contract_id,
                        contract_title=contract_title,
                        war_risk_score=result['war_risk_score'],
                        event_risks=result['event_risks'],
                        supply_chain_routes=result['supply_chain_routes'],
                        disrupted_routes=result['disrupted_routes'],
                        war_loss_expected_usd=result['war_loss_expected_usd'],
                        war_loss_worst_usd=result['war_loss_worst_usd'],
                        top_threats=result['top_threats'],
                        project_location=project_location,
                        supplier_locations=supplier_locations,
                        shipping_routes=result['shipping_routes'],
                        war_mitigation_clauses=result['war_mitigation_clauses'],
                        explanation=result['explanation'],
                    )
                    result['war_risk_id'] = war_obj.id
            except Exception as db_err:
                logger.warning(f"FM war risk DB save failed: {db_err}")
                result['war_risk_id'] = None

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"FM war risk error: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ---------------------------------------------------------------------------
# 5. SCENARIO SIMULATION (Monte Carlo)
# ---------------------------------------------------------------------------
class FMSimulateScenarioView(APIView):
    """
    POST /api/force-majeure/simulate-scenario/
    Body:
      {
        "contract_id": "uuid",
        "contract_value": 5000000,
        "scenario_type": "war",
        "scenario_name": "Red Sea Conflict Escalation",
        "description": "...",
        "input_params": {
          "war_probability": 0.7,
          "port_shutdown_probability": 0.8,
          "sanctions": true
        },
        "iterations": 5000
      }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        data = request.data
        contract_id = data.get('contract_id', '')
        contract_value = float(data.get('contract_value', 1_000_000))
        scenario_type = data.get('scenario_type', 'custom')
        scenario_name = data.get('scenario_name', 'Custom Scenario')
        description = data.get('description', '')
        input_params = data.get('input_params', {})
        iterations = int(data.get('iterations', 5000))

        # Build Bayesian evidence from scenario params
        evidence = {}
        if input_params.get('war_probability'):
            evidence['war'] = float(input_params['war_probability'])
        if input_params.get('sanctions'):
            evidence['trade_sanctions'] = 0.85
        if input_params.get('pandemic_probability'):
            evidence['pandemic'] = float(input_params['pandemic_probability'])
        if input_params.get('port_shutdown_probability'):
            evidence['port_closure'] = float(input_params['port_shutdown_probability'])

        # Pre-built scenario templates
        scenario_templates = {
            'war_escalation': {'war': 0.80, 'trade_sanctions': 0.70, 'energy_crisis': 0.65, 'political_coup': 0.40},
            'financial_crisis': {'economic_collapse': 0.75, 'currency_volatility': 0.80, 'financial_market_crash': 0.70},
            'supply_chain': {'supplier_failure': 0.70, 'port_closure': 0.65, 'transport_shutdown': 0.60},
            'supply_chain_collapse': {'supplier_failure': 0.70, 'port_closure': 0.65, 'transport_shutdown': 0.60},
            'commodity_shock': {'commodity_price_shock': 0.75, 'energy_price_spike': 0.70},
            'pandemic': {'pandemic': 0.80, 'labor_shortage': 0.70, 'factory_shutdown': 0.60},
            'cyber_attack': {'cyber_warfare': 0.75, 'infrastructure_failure': 0.65, 'telecom_disruption': 0.60},
            'climate_disaster': {'flood': 0.70, 'hurricane': 0.65, 'wildfire': 0.50, 'extreme_weather': 0.70},
            'base_case': {},
        }

        template_name = data.get('scenario_template', '')
        if template_name in scenario_templates:
            evidence.update(scenario_templates[template_name])

        try:
            engine = get_fm_bayesian_engine()
            all_probs = engine.infer(evidence)
            outcomes = {node: all_probs.get(node, 0.0) for node in LAYER4_OUTCOMES}
            fm_risk_score = engine.compute_fm_risk_score(evidence)

            mc = monte_carlo_loss(
                fm_risk_score=fm_risk_score,
                contract_value=contract_value,
                outcomes=outcomes,
                iterations=iterations,
            )

            # Build loss breakdown
            loss_breakdown = {
                'delay_penalties': round(mc['expected_loss'] * 0.30, 2),
                'idle_labour': round(mc['expected_loss'] * 0.18, 2),
                'equipment_rental': round(mc['expected_loss'] * 0.12, 2),
                'commodity_price_spike': round(mc['expected_loss'] * 0.22, 2),
                'insurance_premiums': round(mc['expected_loss'] * 0.08, 2),
                'supply_chain_rerouting': round(mc['expected_loss'] * 0.10, 2),
            }

            result = {
                'contract_id': contract_id,
                'scenario_name': scenario_name,
                'scenario_type': scenario_type,
                'description': description,
                'input_params': input_params,
                'fm_risk_score': fm_risk_score,
                'fm_invocation_prob': outcomes.get('fm_invocation', 0.0),
                'project_delay_prob': outcomes.get('project_delay', 0.0),
                'cost_overrun_prob': outcomes.get('cost_overrun', 0.0),
                'contract_suspension_prob': outcomes.get('contract_suspension', 0.0),
                'contract_termination_prob': outcomes.get('contract_termination', 0.0),
                'expected_loss_usd': mc['expected_loss'],
                'p50_loss_usd': mc['p50'],
                'p95_loss_usd': mc['p95'],
                'p99_loss_usd': mc['p99'],
                'worst_case_loss_usd': mc['worst_case'],
                'delay_days_expected': round(outcomes.get('project_delay', 0) * 180, 1),
                'delay_days_worst': round(outcomes.get('project_delay', 0) * 365, 1),
                'loss_breakdown': loss_breakdown,
                'loss_distribution': mc['loss_distribution'],
                'iterations': iterations,
            }

            # Persist scenario
            try:
                with transaction.atomic():
                    scenario_obj = FMScenario.objects.create(
                        contract_id=contract_id,
                        name=scenario_name,
                        scenario_type=scenario_type,
                        description=description,
                        input_params=input_params,
                        iterations=iterations,
                        expected_loss_usd=mc['expected_loss'],
                        p50_loss_usd=mc['p50'],
                        p95_loss_usd=mc['p95'],
                        p99_loss_usd=mc['p99'],
                        worst_case_loss_usd=mc['worst_case'],
                        delay_days_expected=result['delay_days_expected'],
                        delay_days_worst=result['delay_days_worst'],
                        fm_invocation_prob=outcomes.get('fm_invocation', 0.0),
                        project_delay_prob=outcomes.get('project_delay', 0.0),
                        contract_termination_prob=outcomes.get('contract_termination', 0.0),
                        loss_breakdown=loss_breakdown,
                    )
                    result['scenario_id'] = scenario_obj.id
            except Exception as db_err:
                logger.warning(f"FM scenario DB save failed: {db_err}")
                result['scenario_id'] = None

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"FM scenario simulate error: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ---------------------------------------------------------------------------
# 6. BULK PORTFOLIO AUDIT
# ---------------------------------------------------------------------------
class FMBulkAuditView(APIView):
    """
    POST /api/force-majeure/bulk-audit/
    Audits all contracts in a portfolio for FM clause coverage.
    Body:
      {
        "contracts": [
          {"contract_id": "...", "contract_title": "...", "contract_text": "..."},
          ...
        ]
      }
    Or omit contracts to auto-fetch from DB.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        data = request.data
        contracts = data.get('contracts', None)

        if not contracts:
            # Auto-fetch from existing contracts DB
            try:
                from api.models import Contract
                qs = Contract.objects.all().values('id', 'title', 'content')[:50]
                contracts = [
                    {
                        'contract_id': str(c.get('id', '')),
                        'contract_title': c.get('title', ''),
                        'contract_text': c.get('content', ''),
                    }
                    for c in qs
                ]
            except Exception:
                return Response({'error': 'No contracts provided and auto-fetch failed'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            results = bulk_audit_contracts(contracts)

            # Summary stats
            strong = sum(1 for r in results if r.get('status') == 'strong')
            weak = sum(1 for r in results if r.get('status') == 'weak')
            missing = sum(1 for r in results if r.get('status') == 'missing')

            return Response({
                'total_contracts': len(results),
                'strong_clause_count': strong,
                'weak_clause_count': weak,
                'missing_clause_count': missing,
                'audit_results': results,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"FM bulk audit error: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ---------------------------------------------------------------------------
# 7. LIST PREDICTIONS
# ---------------------------------------------------------------------------
class FMPredictionListView(APIView):
    """GET /api/force-majeure/predictions/"""
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        qs = FMPrediction.objects.all().order_by('-created_at')[:50]
        data = [
            {
                'id': p.id,
                'contract_id': p.contract_id,
                'contract_title': p.contract_title,
                'fm_risk_score': p.fm_risk_score,
                'fm_invocation_probability': p.fm_invocation_probability,
                'expected_loss_usd': p.expected_loss_usd,
                'clause_strength_score': p.clause_strength_score,
                'missing_protections_count': len(p.missing_protections),
                'created_at': p.created_at.isoformat(),
            }
            for p in qs
        ]
        return Response({'predictions': data, 'total': len(data)})


class FMPredictionDetailView(APIView):
    """GET /api/force-majeure/predictions/<prediction_id>/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, prediction_id: str) -> Response:
        try:
            p = FMPrediction.objects.get(id=prediction_id)
            return Response({
                'id': p.id,
                'contract_id': p.contract_id,
                'contract_title': p.contract_title,
                'fm_risk_score': p.fm_risk_score,
                'fm_invocation_probability': p.fm_invocation_probability,
                'project_delay_probability': p.project_delay_probability,
                'cost_overrun_probability': p.cost_overrun_probability,
                'contract_suspension_probability': p.contract_suspension_probability,
                'contract_termination_probability': p.contract_termination_probability,
                'event_probabilities': p.event_probabilities,
                'expected_loss_usd': p.expected_loss_usd,
                'worst_case_loss_usd': p.worst_case_loss_usd,
                'p50_loss_usd': p.p50_loss_usd,
                'p95_loss_usd': p.p95_loss_usd,
                'p99_loss_usd': p.p99_loss_usd,
                'bayesian_nodes': p.bayesian_nodes,
                'top_risk_drivers': p.top_risk_drivers,
                'causal_chain': p.causal_chain,
                'clause_strength_score': p.clause_strength_score,
                'missing_protections': p.missing_protections,
                'covered_events': p.covered_events,
                'explanation': p.explanation,
                'mitigation_suggestions': p.mitigation_suggestions,
                'contract_value': p.contract_value,
                'jurisdiction': p.jurisdiction,
                'industry': p.industry,
                'created_at': p.created_at.isoformat(),
            })
        except FMPrediction.DoesNotExist:
            return Response({'error': 'Prediction not found'}, status=status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# 8. CLAUSE AUDITS LIST
# ---------------------------------------------------------------------------
class FMClauseAuditListView(APIView):
    """GET /api/force-majeure/clause-audits/"""
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        qs = FMClauseAudit.objects.all().order_by('-created_at')[:50]
        data = [
            {
                'id': a.id,
                'contract_id': a.contract_id,
                'contract_title': a.contract_title,
                'status': a.status,
                'strength_score': a.strength_score,
                'covered_events': a.covered_events,
                'missing_events': a.missing_events,
                'correction_applied': a.correction_applied,
                'created_at': a.created_at.isoformat(),
            }
            for a in qs
        ]
        return Response({'audits': data, 'total': len(data)})


# ---------------------------------------------------------------------------
# 9. GLOBAL FM ALERTS
# ---------------------------------------------------------------------------
class FMAlertListView(APIView):
    """GET /api/force-majeure/alerts/"""
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        qs = FMGlobalAlert.objects.filter(is_active=True).order_by('-detected_at')[:20]
        data = [
            {
                'id': a.id,
                'event_type': a.event_type,
                'event_title': a.event_title,
                'event_location': a.event_location,
                'severity': a.severity,
                'affected_contracts_count': a.affected_contracts_count,
                'total_portfolio_exposure_usd': a.total_portfolio_exposure_usd,
                'suggested_actions': a.suggested_actions,
                'clause_updates_required': a.clause_updates_required,
                'detected_at': a.detected_at.isoformat(),
            }
            for a in qs
        ]
        return Response({'alerts': data, 'total': len(data)})


class FMAlertCreateView(APIView):
    """POST /api/force-majeure/alerts/create/"""
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        data = request.data
        try:
            alert = FMGlobalAlert.objects.create(
                event_type=data.get('event_type', 'supply_disruption'),
                event_title=data.get('event_title', 'New FM Event'),
                event_description=data.get('event_description', ''),
                event_location=data.get('event_location', ''),
                severity=data.get('severity', 'medium'),
                affected_contract_ids=data.get('affected_contract_ids', []),
                affected_contracts_count=len(data.get('affected_contract_ids', [])),
                total_portfolio_exposure_usd=float(data.get('total_portfolio_exposure_usd', 0)),
                suggested_actions=data.get('suggested_actions', []),
                clause_updates_required=int(data.get('clause_updates_required', 0)),
            )
            return Response({'alert_id': alert.id, 'status': 'created'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ---------------------------------------------------------------------------
# 10. BAYESIAN GRAPH DATA (for visualization)
# ---------------------------------------------------------------------------
class FMBayesianGraphView(APIView):
    """
    GET /api/force-majeure/bayesian-graph/
    Returns nodes and edges for React Flow / Cytoscape rendering of the
    35-node Bayesian causal network.
    Optional query params: evidence=war:0.8,sanctions:0.7
    """
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        # Parse optional evidence from query params
        evidence_str = request.query_params.get('evidence', '')
        evidence = {}
        if evidence_str:
            for part in evidence_str.split(','):
                if ':' in part:
                    k, v = part.split(':', 1)
                    try:
                        evidence[k.strip()] = float(v.strip())
                    except ValueError:
                        pass

        engine = get_fm_bayesian_engine()
        all_probs = engine.infer(evidence if evidence else None)

        # Build React Flow compatible nodes
        nodes = []
        x_positions = {1: 100, 2: 500, 3: 900, 4: 1300}
        layer_map = {}
        for node in LAYER1_EVENTS:
            layer_map[node] = 1
        for node in LAYER2_DISRUPTIONS:
            layer_map[node] = 2
        for node in LAYER3_SUPPLY:
            layer_map[node] = 3
        for node in LAYER4_OUTCOMES:
            layer_map[node] = 4

        layer_y_counters = {1: 0, 2: 0, 3: 0, 4: 0}

        for node in ALL_NODES:
            layer = layer_map.get(node, 1)
            prob = all_probs.get(node, 0.0)
            y_idx = layer_y_counters[layer]
            layer_y_counters[layer] += 1

            color = '#F16667' if prob > 0.6 else '#F79767' if prob > 0.35 else '#68BC00'
            layer_labels = {1: 'Root Event', 2: 'Disruption', 3: 'Supply Impact', 4: 'Outcome'}

            nodes.append({
                'id': node,
                'data': {
                    'label': node.replace('_', ' ').title(),
                    'probability': round(prob, 4),
                    'layer': layer,
                    'layer_label': layer_labels.get(layer, ''),
                },
                'position': {'x': x_positions[layer], 'y': y_idx * 80 + 50},
                'style': {
                    'background': color,
                    'color': '#fff',
                    'border': '2px solid rgba(255,255,255,0.3)',
                    'borderRadius': '8px',
                    'padding': '8px',
                    'fontSize': '11px',
                    'width': 160,
                },
            })

        # Build edges from CPT relationships
        from .bayesian_engine import CPT_LAYER2, CPT_LAYER3, CPT_LAYER4
        edges = []
        edge_id = 0

        for child, parents in {**CPT_LAYER2, **CPT_LAYER3, **CPT_LAYER4}.items():
            for parent, weight in parents.items():
                if parent in layer_map:  # skip virtual nodes
                    parent_prob = all_probs.get(parent, 0.0)
                    child_prob = all_probs.get(child, 0.0)
                    edge_active = parent_prob > 0.3 and child_prob > 0.2

                    edges.append({
                        'id': f'e{edge_id}',
                        'source': parent,
                        'target': child,
                        'label': f'{weight:.0%}',
                        'animated': edge_active,
                        'style': {
                            'stroke': '#F16667' if edge_active else '#555',
                            'strokeWidth': 2 if edge_active else 1,
                        },
                    })
                    edge_id += 1

        return Response({
            'nodes': nodes,
            'edges': edges,
            'node_probabilities': {k: round(v, 4) for k, v in all_probs.items()},
            'evidence_used': evidence,
        })


# ---------------------------------------------------------------------------
# 11. PORTFOLIO SUMMARY
# ---------------------------------------------------------------------------
class FMPortfolioSummaryView(APIView):
    """GET /api/force-majeure/portfolio-summary/"""
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        predictions = FMPrediction.objects.all().order_by('-created_at')[:100]
        audits = FMClauseAudit.objects.all().order_by('-created_at')[:100]
        alerts = FMGlobalAlert.objects.filter(is_active=True)[:10]

        total_preds = predictions.count()
        avg_risk = (
            sum(p.fm_risk_score for p in predictions) / total_preds
            if total_preds > 0 else 0.0
        )
        total_exposure = sum(p.expected_loss_usd for p in predictions)

        strong = sum(1 for a in audits if a.status == 'strong')
        weak = sum(1 for a in audits if a.status == 'weak')
        missing = sum(1 for a in audits if a.status == 'missing')

        high_risk = [
            {
                'id': p.id,
                'contract_id': p.contract_id,
                'contract_title': p.contract_title,
                'fm_risk_score': p.fm_risk_score,
                'expected_loss_usd': p.expected_loss_usd,
            }
            for p in predictions
            if p.fm_risk_score > 0.6
        ][:5]

        active_alerts = [
            {
                'id': a.id,
                'event_type': a.event_type,
                'event_title': a.event_title,
                'severity': a.severity,
                'affected_contracts_count': a.affected_contracts_count,
            }
            for a in alerts
        ]

        return Response({
            'portfolio_summary': {
                'total_contracts_analyzed': total_preds,
                'average_fm_risk_score': round(avg_risk, 4),
                'total_portfolio_exposure_usd': round(total_exposure, 2),
                'clause_audit_summary': {
                    'strong': strong,
                    'weak': weak,
                    'missing': missing,
                    'total_audited': strong + weak + missing,
                },
                'high_risk_contracts': high_risk,
                'active_alerts': active_alerts,
                'alert_count': len(active_alerts),
            }
        })
