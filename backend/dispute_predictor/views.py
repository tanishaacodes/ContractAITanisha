"""
Dispute Predictor API Views
============================
Endpoints:
  POST   /api/dispute-predictor/predict/                          → Full dispute prediction
  POST   /api/dispute-predictor/simulate/                         → Scenario simulation
  GET    /api/dispute-predictor/graph/                            → 60-node Bayesian graph structure
  GET    /api/dispute-predictor/predictions/                      → List saved predictions
  GET    /api/dispute-predictor/predictions/<id>/                 → Single prediction detail
  DELETE /api/dispute-predictor/predictions/<id>/                 → Delete prediction
  POST   /api/dispute-predictor/predict-from-contract/<id>/       → Analyse existing contract
  POST   /api/dispute-predictor/similar-clauses/                  → BM25+BERT RAG clause retrieval
  GET    /api/dispute-predictor/ai-status/                        → GNN / LegalBERT / RAG availability
"""

import logging
from typing import Any, Dict

from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from .dispute_service import predict_dispute
from .bayesian_engine import get_bayesian_engine
from .models import DisputePrediction, DisputeScenario

logger = logging.getLogger(__name__)


class DisputePredictView(APIView):
    """
    POST /api/dispute-predictor/predict/
    Body:
      {
        "contract_text": "...",
        "contract_value": 5000000,
        "contract_id": "optional-uuid",
        "contract_title": "Optional title",
        "manual_signals": {"WarRisk": 0.8, "CommodityPriceShock": 0.7},
        "generate_explanation": true
      }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        data = request.data
        contract_text = data.get('contract_text', '')
        contract_value = float(data.get('contract_value', 1_000_000))
        contract_id = data.get('contract_id', '')
        contract_title = data.get('contract_title', '')
        manual_signals = data.get('manual_signals', {})
        generate_explanation = bool(data.get('generate_explanation', True))

        if not contract_text and not manual_signals:
            return Response(
                {'error': 'Either contract_text or manual_signals must be provided.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = predict_dispute(
                contract_text=contract_text,
                contract_value=contract_value,
                manual_signals=manual_signals if manual_signals else None,
                generate_explanation=generate_explanation,
            )

            # Derive title from first line of contract text if not provided
            import uuid as _uuid
            if not contract_title and contract_text:
                first_line = next((l.strip() for l in contract_text.split('\n') if l.strip()), '')
                contract_title = first_line[:60] if first_line else 'Manual Analysis'
            effective_contract_id = contract_id or f'manual-{_uuid.uuid4().hex[:8]}'

            # Persist to DB
            prediction = DisputePrediction.objects.create(
                contract_id=effective_contract_id,
                contract_title=contract_title or 'Manual Analysis',
                contract_text=contract_text or '',
                dispute_probability=result['dispute_probability'],
                arbitration_probability=result['arbitration_probability'],
                litigation_probability=result['litigation_probability'],
                settlement_probability=result['settlement_probability'],
                predicted_cost_usd=result['predicted_cost_usd'],
                legal_cost_exposure_usd=result['legal_cost_exposure_usd'],
                contract_risk_score=result['contract_risk_score'],
                financial_stress_score=result['financial_stress_score'],
                operational_risk_score=result['operational_risk_score'],
                geopolitical_risk_score=result['geopolitical_risk_score'],
                bayesian_risk_nodes=result['all_node_posteriors'],
                risk_propagation_path=result['risk_propagation_path'],
                top_risk_drivers=result['top_risk_drivers'],
                explanation=result['explanation'],
                mitigation_recommendations=result['mitigation_recommendations'],
                input_signals=result['input_signals'],
            )

            return Response({
                'success': True,
                'prediction_id': prediction.id,
                **result,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(f"Dispute prediction failed: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DisputeSimulateView(APIView):
    """
    POST /api/dispute-predictor/simulate/
    Body:
      {
        "contract_id": "optional",
        "base_signals": {"WarRisk": 0.1, "CommodityPriceShock": 0.3},
        "scenarios": [
          {
            "name": "War Escalation",
            "description": "War risk increases significantly",
            "overrides": {"WarRisk": 0.8, "EnergyPriceShock": 0.75}
          },
          ...
        ],
        "contract_value": 5000000
      }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        data = request.data
        contract_id = data.get('contract_id', 'manual')
        base_signals = data.get('base_signals', {})
        scenarios = data.get('scenarios', [])
        contract_value = float(data.get('contract_value', 1_000_000))

        if not scenarios:
            return Response(
                {'error': 'At least one scenario must be provided.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        engine = get_bayesian_engine()

        try:
            # Base prediction
            base_result = engine.compute_dispute_probability(base_signals)

            scenario_results = []
            for scenario in scenarios:
                s_name = scenario.get('name', 'Scenario')
                s_desc = scenario.get('description', '')
                s_overrides = scenario.get('overrides', {})

                sim = engine.run_scenario(
                    base_evidence=base_signals,
                    scenario_overrides=s_overrides,
                    scenario_name=s_name,
                )

                # Cost estimates
                base_cost = contract_value * base_result['dispute_probability'] * 0.06
                scenario_cost = contract_value * sim['scenario_dispute_probability'] * 0.06

                # Persist
                saved_scenario = DisputeScenario.objects.create(
                    contract_id=contract_id,
                    prediction_id='',
                    scenario_name=s_name,
                    scenario_description=s_desc,
                    risk_overrides=s_overrides,
                    dispute_probability=sim['scenario_dispute_probability'],
                    arbitration_probability=sim['scenario_result'].get('arbitration_probability', 0),
                    predicted_cost_usd=scenario_cost,
                    contract_risk_score=sim['scenario_result'].get('contract_risk_score', 0),
                    dispute_probability_delta=sim['delta'],
                    cost_delta=round(scenario_cost - base_cost, 2),
                    risk_nodes_snapshot=sim['scenario_result'].get('all_node_posteriors', {}),
                    propagation_path=sim['scenario_result'].get('risk_propagation_path', []),
                )

                scenario_results.append({
                    'scenario_id': saved_scenario.id,
                    'scenario_name': s_name,
                    'description': s_desc,
                    'base_dispute_probability': sim['base_dispute_probability'],
                    'scenario_dispute_probability': sim['scenario_dispute_probability'],
                    'delta': sim['delta'],
                    'base_cost_usd': round(base_cost, 2),
                    'scenario_cost_usd': round(scenario_cost, 2),
                    'cost_delta': round(scenario_cost - base_cost, 2),
                    'risk_overrides': s_overrides,
                    'top_risk_drivers': sim['scenario_result'].get('top_risk_drivers', []),
                    'propagation_path': sim['scenario_result'].get('risk_propagation_path', []),
                })

            return Response({
                'success': True,
                'base_dispute_probability': base_result['dispute_probability'],
                'base_contract_risk': base_result['contract_risk_score'],
                'scenarios': scenario_results,
                'contract_value': contract_value,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(f"Dispute simulation failed: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DisputeGraphView(APIView):
    """
    GET /api/dispute-predictor/graph/
    Returns the full 60-node Bayesian risk graph structure for visualization.
    Optional: ?signals={"WarRisk":0.8,...} to get live posteriors.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        import json
        engine = get_bayesian_engine()
        graph = engine.get_graph_structure()

        # If evidence provided, compute posteriors
        signals_raw = request.query_params.get('signals', '{}')
        try:
            signals = json.loads(signals_raw)
        except Exception:
            signals = {}

        if signals:
            posteriors = engine.infer(signals)
            for node in graph['nodes']:
                node['current_probability'] = round(posteriors.get(node['id'], node['base_probability']), 3)
        else:
            for node in graph['nodes']:
                node['current_probability'] = node['base_probability']

        return Response({
            'success': True,
            'node_count': len(graph['nodes']),
            'edge_count': len(graph['edges']),
            'nodes': graph['nodes'],
            'edges': graph['edges'],
        })


class DisputePredictionListView(APIView):
    """
    GET /api/dispute-predictor/predictions/
    Returns recent predictions for the authenticated user's contracts.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        qs = DisputePrediction.objects.order_by('-created_at')[:50]
        results = []
        for p in qs:
            results.append({
                'id': p.id,
                'contract_id': p.contract_id,
                'contract_title': p.contract_title,
                'dispute_probability': p.dispute_probability,
                'contract_risk_score': p.contract_risk_score,
                'arbitration_probability': p.arbitration_probability,
                'predicted_cost_usd': p.predicted_cost_usd,
                'legal_cost_exposure_usd': p.legal_cost_exposure_usd,
                'top_risk_drivers': p.top_risk_drivers[:3] if p.top_risk_drivers else [],
                'created_at': p.created_at.isoformat(),
            })
        return Response({'success': True, 'predictions': results})


class DisputePredictionDetailView(APIView):
    """
    GET  /api/dispute-predictor/predictions/<prediction_id>/
    DELETE /api/dispute-predictor/predictions/<prediction_id>/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, prediction_id: str) -> Response:
        try:
            p = DisputePrediction.objects.get(id=prediction_id)
        except DisputePrediction.DoesNotExist:
            return Response({'error': 'Prediction not found.'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'success': True,
            'prediction': {
                'id': p.id,
                'contract_id': p.contract_id,
                'contract_title': p.contract_title,
                'contract_value_usd': p.predicted_cost_usd / p.dispute_probability if p.dispute_probability > 0 else p.predicted_cost_usd,
                'contract_text': p.contract_text or '',
                'dispute_probability': p.dispute_probability,
                'arbitration_probability': p.arbitration_probability,
                'litigation_probability': p.litigation_probability,
                'settlement_probability': p.settlement_probability,
                'contract_risk_score': p.contract_risk_score,
                'financial_stress_score': p.financial_stress_score,
                'operational_risk_score': p.operational_risk_score,
                'geopolitical_risk_score': p.geopolitical_risk_score,
                'predicted_cost_usd': p.predicted_cost_usd,
                'legal_cost_exposure_usd': p.legal_cost_exposure_usd,
                'bayesian_risk_nodes': p.bayesian_risk_nodes,
                'risk_propagation_path': p.risk_propagation_path,
                'top_risk_drivers': p.top_risk_drivers,
                'gnn_dispute_score': p.gnn_dispute_score,
                'gnn_confidence': p.gnn_confidence,
                'gnn_outcome_distribution': None,
                'legalbert_amplifications': [],
                'legalbert_available': False,
                'explanation': p.explanation,
                'mitigation_recommendations': p.mitigation_recommendations,
                'input_signals': p.input_signals,
                'created_at': p.created_at.isoformat(),
            }
        })

    def delete(self, request, prediction_id: str) -> Response:
        try:
            p = DisputePrediction.objects.get(id=prediction_id)
            p.delete()
            return Response({'success': True})
        except DisputePrediction.DoesNotExist:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)


class DisputePredictFromContractView(APIView):
    """
    POST /api/dispute-predictor/predict-from-contract/<contract_id>/
    Automatically analyses an existing contract from the database.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, contract_id: str) -> Response:
        from core.models import Contract

        try:
            contract = Contract.objects.get(id=contract_id)
        except Contract.DoesNotExist:
            return Response({'error': 'Contract not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        contract_text = getattr(contract, 'raw_text', '') or getattr(contract, 'text', '') or ''
        contract_value = float(getattr(contract, 'value', 0) or getattr(contract, 'contract_value', 0) or 1_000_000)
        contract_title = getattr(contract, 'title', '') or getattr(contract, 'name', '') or contract_id

        try:
            result = predict_dispute(
                contract_text=contract_text,
                contract_value=contract_value,
                generate_explanation=True,
            )

            prediction = DisputePrediction.objects.create(
                contract_id=contract_id,
                contract_title=contract_title,
                dispute_probability=result['dispute_probability'],
                arbitration_probability=result['arbitration_probability'],
                litigation_probability=result['litigation_probability'],
                settlement_probability=result['settlement_probability'],
                predicted_cost_usd=result['predicted_cost_usd'],
                legal_cost_exposure_usd=result['legal_cost_exposure_usd'],
                contract_risk_score=result['contract_risk_score'],
                financial_stress_score=result['financial_stress_score'],
                operational_risk_score=result['operational_risk_score'],
                geopolitical_risk_score=result['geopolitical_risk_score'],
                bayesian_risk_nodes=result['all_node_posteriors'],
                risk_propagation_path=result['risk_propagation_path'],
                top_risk_drivers=result['top_risk_drivers'],
                explanation=result['explanation'],
                mitigation_recommendations=result['mitigation_recommendations'],
                input_signals=result['input_signals'],
            )

            return Response({
                'success': True,
                'prediction_id': prediction.id,
                'contract_title': contract_title,
                **result,
            })

        except Exception as e:
            logger.exception(f"Predict-from-contract failed: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DisputePrebuiltScenariosView(APIView):
    """
    GET /api/dispute-predictor/prebuilt-scenarios/
    Returns pre-defined scenario templates.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        prebuilt = [
            {
                'id': 'war_escalation',
                'name': 'War & Geopolitical Escalation',
                'description': 'Major conflict significantly disrupts supply chains and commodities',
                'overrides': {
                    'WarRisk': 0.35, 'EnergyPriceShock': 0.30,
                    'CommodityPriceShock': 0.28, 'SanctionsRisk': 0.25,
                    'SupplierDelay': 0.30,
                },
                'severity': 'extreme',
            },
            {
                'id': 'financial_crisis',
                'name': 'Financial & Credit Crisis',
                'description': 'Credit markets tighten, counterparty defaults increase',
                'overrides': {
                    'CounterpartyCreditRisk': 0.32, 'PaymentDefaultRisk': 0.30,
                    'CashFlowStress': 0.28, 'CreditMarketTightening': 0.30,
                    'WorkingCapitalStress': 0.27,
                },
                'severity': 'severe',
            },
            {
                'id': 'supply_chain_collapse',
                'name': 'Supply Chain Collapse',
                'description': 'Major supplier failures and logistics disruptions',
                'overrides': {
                    'SupplierBankruptcy': 0.30, 'SupplierDelay': 0.35,
                    'TransportDisruption': 0.32, 'InventoryShortage': 0.28,
                    'DeliveryFailure': 0.27,
                },
                'severity': 'severe',
            },
            {
                'id': 'commodity_shock',
                'name': 'Commodity Price Shock',
                'description': 'Raw material prices spike significantly',
                'overrides': {
                    'CommodityPriceShock': 0.38, 'ContractCostOverrun': 0.32,
                    'CostEscalation': 0.28, 'RenegotiationRisk': 0.25,
                },
                'severity': 'moderate',
            },
            {
                'id': 'contract_ambiguity',
                'name': 'High Contract Ambiguity',
                'description': 'Poorly drafted contract with conflicting clauses',
                'overrides': {
                    'ContractAmbiguity': 0.38, 'ClauseConflict': 0.32,
                    'LiabilityExposure': 0.28, 'RenegotiationRisk': 0.24,
                },
                'severity': 'moderate',
            },
            {
                'id': 'base_case',
                'name': 'Base Case (No Stress)',
                'description': 'Normal operating environment',
                'overrides': {
                    'WarRisk': 0.02, 'CommodityPriceShock': 0.05,
                    'SupplierDelay': 0.05, 'ContractAmbiguity': 0.08,
                },
                'severity': 'low',
            },
        ]
        return Response({'success': True, 'scenarios': prebuilt})


class DisputeSimilarClausesView(APIView):
    """
    POST /api/dispute-predictor/similar-clauses/
    BM25+BERT RAG retrieval of similar clauses from the clause library.
    Body: { "contract_text": "...", "top_k": 5 }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        from .dispute_service import retrieve_similar_clauses
        contract_text = request.data.get('contract_text', '')
        top_k = int(request.data.get('top_k', 5))

        if not contract_text:
            return Response({'error': 'contract_text required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            results = retrieve_similar_clauses(contract_text, top_k=top_k)
            return Response({
                'success': True,
                'count': len(results),
                'similar_clauses': results,
            })
        except Exception as e:
            logger.exception(f"Similar clauses retrieval failed: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DisputeAIStatusView(APIView):
    """
    GET /api/dispute-predictor/ai-status/
    Returns availability of GNN, LegalBERT, and RAG components.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        from .dispute_service import _get_gnn, _get_legalbert, _get_rag_retriever

        # GNN
        gnn = _get_gnn()
        gnn_status = {
            'available': gnn is not None,
            'model_loaded': gnn.is_available() if gnn else False,
            'source': 'trained_model' if (gnn and gnn.is_available()) else 'heuristic',
        }

        # LegalBERT — calling _get_legalbert() triggers model load (singleton warms up here)
        lb = _get_legalbert()
        lb_loaded = lb is not None and lb.is_available()
        lb_status = {
            'available': lb is not None,
            'model_loaded': lb_loaded,
            'model': 'nlpaueb/legal-bert-base-uncased',
            'status': 'active' if lb_loaded else ('loading' if lb is not None else 'unavailable'),
        }

        # RAG
        rag = _get_rag_retriever()
        try:
            from core.models import Clause
            clause_count = Clause.objects.count()
        except Exception:
            clause_count = 0

        rag_status = {
            'available': rag is not None,
            'indexed_clauses': clause_count,
            'retriever_ready': rag is not None,
        }

        return Response({
            'success': True,
            'gnn': gnn_status,
            'legalbert': lb_status,
            'rag': rag_status,
            'bayesian': {'available': True, 'nodes': 60, 'layers': 8},
            'llm': {
                'model': getattr(__import__('django.conf', fromlist=['settings']).settings, 'OLLAMA_MODEL', 'qwen2.5:0.5b'),
                'url': getattr(__import__('django.conf', fromlist=['settings']).settings, 'OLLAMA_BASE_URL', 'http://localhost:11434'),
            },
        })
