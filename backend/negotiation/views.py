"""
Negotiation Intelligence API Views
Provides endpoints for prediction, behavior analysis, simulation, and silent risk detection
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from core.models import Contract, Clause
from .models import (
    Counterparty,
    NegotiationHistory,
    CounterpartyBehaviorSnapshot,
    ContractNegotiation,
    SilentRisk,
    ExculpatoryAnalysis,
    ExculpatoryClause,
    ExculpatoryPattern
)

from ai.negotiation_predictor import (
    predict_outcome,
    predict_multiple_clauses,
    identify_high_risk_clauses,
    calculate_deal_complexity
)
from ai.behavior_metrics import (
    compute_behavior_metrics,
    clause_acceptance_matrix,
    identify_stall_clauses,
    calculate_negotiation_style,
    trend_analysis
)
from ai.negotiation_simulator import (
    simulate_negotiation,
    generate_negotiation_strategy
)
from ai.silent_risk_engine import (
    detect_silent_risks,
    generate_silent_risk_heatmap,
    explain_silent_risk
)

import logging

logger = logging.getLogger(__name__)


class NegotiationPredictionAPI(APIView):
    """
    Predict negotiation outcome for a single clause
    POST /api/negotiation/predict
    Body: {
        "clause_text": str,
        "clause_type": str,
        "counterparty": str or int (name or ID)
    }
    """
    def post(self, request):
        clause_text = request.data.get('clause_text', '')
        clause_type = request.data.get('clause_type', '')
        counterparty = request.data.get('counterparty', '')

        if not all([clause_text, clause_type, counterparty]):
            return Response(
                {"error": "Missing required fields"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get counterparty name
        if isinstance(counterparty, int) or counterparty.isdigit():
            try:
                cp = Counterparty.objects.get(id=counterparty)
                counterparty_name = cp.name
            except Counterparty.DoesNotExist:
                return Response(
                    {"error": "Counterparty not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            counterparty_name = counterparty

        prediction = predict_outcome(clause_text, clause_type, counterparty_name)

        return Response({
            "clause_type": clause_type,
            **prediction
        })


class MultiClausePredictionAPI(APIView):
    """
    Predict outcomes for multiple clauses
    POST /api/negotiation/predict-multiple
    Body: {
        "clauses": [{"clause_type": str, "text": str}, ...],
        "counterparty": str or int
    }
    """
    def post(self, request):
        clauses = request.data.get('clauses', [])
        counterparty = request.data.get('counterparty', '')

        if not clauses or not counterparty:
            return Response(
                {"error": "Missing required fields"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get counterparty name
        if isinstance(counterparty, int) or str(counterparty).isdigit():
            try:
                cp = Counterparty.objects.get(id=counterparty)
                counterparty_name = cp.name
            except Counterparty.DoesNotExist:
                return Response(
                    {"error": "Counterparty not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            counterparty_name = counterparty

        predictions = predict_multiple_clauses(clauses, counterparty_name)
        high_risk = identify_high_risk_clauses(predictions)
        complexity = calculate_deal_complexity(predictions)

        return Response({
            "predictions": predictions,
            "high_risk_clauses": high_risk,
            "deal_complexity": complexity
        })


class CounterpartyBehaviorAPI(APIView):
    """
    Get behavior metrics for a counterparty
    GET /api/negotiation/counterparty/<id>/behavior
    """
    def get(self, request, counterparty_id):
        try:
            counterparty = Counterparty.objects.get(id=counterparty_id)
        except Counterparty.DoesNotExist:
            return Response(
                {"error": "Counterparty not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get negotiation history
        history = NegotiationHistory.objects.filter(counterparty=counterparty)

        if not history.exists():
            return Response({
                "counterparty": counterparty.name,
                "message": "No negotiation history available",
                "behavior": None
            })

        # Compute metrics
        behavior = compute_behavior_metrics(history)
        clause_matrix = clause_acceptance_matrix(history)
        stall_clauses = identify_stall_clauses(history)
        negotiation_style = calculate_negotiation_style(behavior)

        # Get trends
        snapshots = CounterpartyBehaviorSnapshot.objects.filter(
            counterparty=counterparty
        ).order_by('-snapshot_date')
        trends = trend_analysis(snapshots)

        return Response({
            "counterparty": counterparty.name,
            "behavior": behavior,
            "negotiation_style": negotiation_style,
            "clause_acceptance_matrix": clause_matrix,
            "stall_clauses": stall_clauses,
            "trends": trends
        })


class NegotiationSimulationAPI(APIView):
    """
    Simulate multi-clause negotiation with caching
    """
    def get(self, request, contract_id=None, counterparty_id=None):
        """Get cached simulation"""
        if not contract_id or not counterparty_id:
            return Response(
                {"error": "Missing contract_id or counterparty_id"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            contract = Contract.objects.get(id=contract_id)
        except Contract.DoesNotExist:
            return Response(
                {"error": "Contract not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get counterparty name
        try:
            if str(counterparty_id).isdigit():
                counterparty = Counterparty.objects.get(id=counterparty_id)
                counterparty_name = counterparty.name
            else:
                counterparty_name = counterparty_id
        except Counterparty.DoesNotExist:
            return Response(
                {"error": "Counterparty not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check cache
        try:
            from .models import NegotiationSimulationCache
            cached = NegotiationSimulationCache.objects.get(
                contract=contract,
                counterparty_name=counterparty_name
            )
            logger.info(f"Returning cached simulation for contract {contract_id} vs {counterparty_name}")
            return Response({
                "simulation": cached.simulation_result,
                "strategy": cached.strategy,
                "cached": True,
                "updated_at": cached.updated_at
            })
        except:
            return Response(
                {"error": "No cached simulation found"},
                status=status.HTTP_404_NOT_FOUND
            )

    def post(self, request, contract_id=None, counterparty_id=None):
        """Run simulation (checks cache first unless force_refresh)"""
        contract_id = request.data.get('contract_id')
        counterparty = request.data.get('counterparty', '')
        clauses = request.data.get('clauses', [])
        force_refresh = request.data.get('force_refresh', False)

        if not counterparty or not clauses:
            return Response(
                {"error": "Missing required fields"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get counterparty name
        if isinstance(counterparty, int) or str(counterparty).isdigit():
            try:
                cp = Counterparty.objects.get(id=counterparty)
                counterparty_name = cp.name
            except Counterparty.DoesNotExist:
                return Response(
                    {"error": "Counterparty not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            counterparty_name = counterparty

        # Check cache if contract_id provided and not forcing refresh
        if contract_id and not force_refresh:
            try:
                contract = Contract.objects.get(id=contract_id)
                from .models import NegotiationSimulationCache
                cached = NegotiationSimulationCache.objects.get(
                    contract=contract,
                    counterparty_name=counterparty_name
                )
                logger.info(f"Returning cached simulation for contract {contract_id} vs {counterparty_name}")
                return Response({
                    "simulation": cached.simulation_result,
                    "strategy": cached.strategy,
                    "cached": True
                })
            except:
                pass  # No cache, run new simulation

        # Run simulation
        logger.info(f"Running fresh simulation for counterparty: {counterparty_name}")
        logger.info(f"Received {len(clauses)} clauses from frontend:")
        for idx, clause in enumerate(clauses):
            logger.info(f"  Clause {idx+1}: type='{clause.get('clause_type')}', text_len={len(clause.get('text', ''))}")
        simulation_result = simulate_negotiation(counterparty_name, clauses)

        # Generate strategy
        strategy = generate_negotiation_strategy(simulation_result)

        # Cache results if contract_id provided
        if contract_id:
            try:
                contract = Contract.objects.get(id=contract_id)
                from .models import NegotiationSimulationCache
                NegotiationSimulationCache.objects.update_or_create(
                    contract=contract,
                    counterparty_name=counterparty_name,
                    defaults={
                        'simulation_result': simulation_result,
                        'strategy': strategy
                    }
                )
                logger.info(f"Simulation cached for contract {contract_id} vs {counterparty_name}")
            except Exception as e:
                logger.warning(f"Failed to cache simulation: {e}")

        return Response({
            "simulation": simulation_result,
            "strategy": strategy,
            "cached": False
        })


class SilentRiskDetectionAPI(APIView):
    """
    Detect silent risks in a contract
    GET /api/negotiation/silent-risk/<contract_id>
    """
    def get(self, request, contract_id):
        try:
            contract = Contract.objects.get(id=contract_id)
        except Contract.DoesNotExist:
            return Response(
                {"error": "Contract not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            # Always recalculate to ensure fresh data per contract
            # Clear any cached risks for this contract
            SilentRisk.objects.filter(contract=contract).delete()
            logger.info(f"Calculating fresh silent risks for contract {contract_id}")

            # Get clauses - limit to top 20 most important clauses
            clauses = Clause.objects.filter(contract=contract).order_by('-id')[:20]

            if not clauses.exists():
                return Response({
                    "contract_id": contract_id,
                    "message": "No clauses found for this contract",
                    "silent_risks": []
                })

            logger.info(f"Analyzing {clauses.count()} clauses for contract {contract_id}")

            # Detect risks
            silent_risks = detect_silent_risks(contract, clauses)

            # PERSIST RISKS TO DATABASE
            for risk_data in silent_risks:
                SilentRisk.objects.create(
                    contract=contract,
                    risk_type=risk_data['risk_type'],
                    description=risk_data['description'],
                    clause_pair=risk_data.get('clause_pair', []),
                    financial_exposure=risk_data['financial_exposure'],
                    confidence=risk_data['confidence'],
                    severity=risk_data['severity']
                )

            logger.info(f"Persisted {len(silent_risks)} silent risks to database for contract {contract_id}")

            return Response({
                "contract_id": contract_id,
                "contract_name": getattr(contract, 'name', str(contract_id)),
                "silent_risks": silent_risks,
                "total_risks": len(silent_risks),
                "cached": False
            })
        except Exception as e:
            logger.error(f"Error detecting silent risks for contract {contract_id}: {str(e)}", exc_info=True)
            return Response({
                "error": f"Failed to detect risks: {str(e)}",
                "contract_id": contract_id,
                "silent_risks": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SilentRiskHeatmapAPI(APIView):
    """
    Generate heatmap data for silent risk visualization
    GET /api/negotiation/silent-risk/<contract_id>/heatmap

    Query params:
    - force_refresh=true: Force regeneration of heatmap (ignore cache)
    """
    def get(self, request, contract_id):
        try:
            contract = Contract.objects.get(id=contract_id)
        except Contract.DoesNotExist:
            return Response(
                {"error": "Contract not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if user wants to force refresh
        force_refresh = request.GET.get('force_refresh', 'false').lower() == 'true'

        # Check if we have cached heatmap (unless force refresh)
        if not force_refresh:
            try:
                from .models import SilentRiskHeatmapCache
                cached_heatmap = SilentRiskHeatmapCache.objects.get(contract=contract)
                logger.info(f"Returning cached heatmap for contract {contract_id}")
                return Response({
                    "clauses": cached_heatmap.clauses,
                    "matrix": cached_heatmap.matrix,
                    "total_risks": cached_heatmap.total_risks,
                    "cached": True,
                    "updated_at": cached_heatmap.updated_at
                })
            except:
                # No cache found, generate fresh
                pass

        # Limit to top 15 clauses for heatmap (15x15 = 225 cells max)
        clauses = Clause.objects.filter(contract=contract).order_by('-id')[:15]

        if not clauses.exists():
            return Response({
                "contract_id": contract_id,
                "clauses": [],
                "matrix": {},
                "cached": False
            })

        logger.info(f"Generating fresh heatmap for {clauses.count()} clauses")
        heatmap_data = generate_silent_risk_heatmap(contract, clauses)

        # Store in cache
        try:
            from .models import SilentRiskHeatmapCache
            total_risks = len(heatmap_data.get('matrix', {})) // 2  # Divide by 2 because of symmetry
            SilentRiskHeatmapCache.objects.update_or_create(
                contract=contract,
                defaults={
                    'clauses': heatmap_data.get('clauses', []),
                    'matrix': heatmap_data.get('matrix', {}),
                    'total_risks': total_risks
                }
            )
            logger.info(f"Heatmap cached for contract {contract_id}")
        except Exception as e:
            logger.warning(f"Failed to cache heatmap: {e}")

        heatmap_data['cached'] = False
        return Response(heatmap_data)


class SilentRiskExplainAPI(APIView):
    """
    Get detailed explanation for a silent risk
    POST /api/negotiation/silent-risk/explain
    Body: {
        "risk_type": str,
        "financial_exposure": float,
        "clause_pair": [str, str]
    }
    """
    def post(self, request):
        risk_data = request.data

        if not risk_data.get('risk_type'):
            return Response(
                {"error": "risk_type is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        explanation = explain_silent_risk(risk_data)

        return Response({
            "risk_type": risk_data.get('risk_type'),
            "explanation": explanation
        })


class CounterpartyListAPI(APIView):
    """
    List all counterparties with basic metrics
    GET /api/negotiation/counterparties
    """
    def get(self, request):
        counterparties = Counterparty.objects.all()

        data = []
        for cp in counterparties:
            history = NegotiationHistory.objects.filter(counterparty=cp)
            behavior = compute_behavior_metrics(history) if history.exists() else None

            data.append({
                "id": cp.id,
                "name": cp.name,
                "industry": cp.industry,
                "risk_profile": cp.risk_profile,
                "aggressiveness_score": cp.aggressiveness_score,
                "behavior_summary": behavior
            })

        return Response({
            "counterparties": data,
            "total": len(data)
        })

    def post(self, request):
        """Create a new counterparty"""
        name = request.data.get('name', '')
        industry = request.data.get('industry', '')

        if not name:
            return Response(
                {"error": "name is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        counterparty = Counterparty.objects.create(
            name=name,
            industry=industry
        )

        return Response({
            "id": counterparty.id,
            "name": counterparty.name,
            "industry": counterparty.industry
        }, status=status.HTTP_201_CREATED)


class ExculpatoryAnalysisAPI(APIView):
    """
    Analyze contract for exculpatory clauses
    GET /api/negotiation/exculpatory/<contract_id>
    POST /api/negotiation/exculpatory/analyze (with contract_id in body)

    Query params for GET:
    - force_refresh=true: Force re-analysis (ignore cache)
    """

    def get(self, request, contract_id):
        """Get cached exculpatory analysis"""
        try:
            contract = Contract.objects.get(id=contract_id)
        except Contract.DoesNotExist:
            return Response(
                {"error": "Contract not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check for cached analysis
        force_refresh = request.GET.get('force_refresh', 'false').lower() == 'true'

        if not force_refresh:
            try:
                from .serializers import ExculpatoryAnalysisSerializer

                analysis = ExculpatoryAnalysis.objects.get(contract=contract)
                serializer = ExculpatoryAnalysisSerializer(analysis)
                logger.info(f"Returning cached exculpatory analysis for contract {contract_id}")

                return Response({
                    **serializer.data,
                    "cached": True
                })
            except ExculpatoryAnalysis.DoesNotExist:
                pass

        # No cache or force refresh - run analysis
        return self._run_analysis(contract)

    def post(self, request, **kwargs):
        """Run exculpatory analysis (checks cache unless force_refresh)"""
        # contract_id can come from URL path or request body
        contract_id = kwargs.get('contract_id') or request.data.get('contract_id')
        force_refresh = request.data.get('force_refresh', False)

        if not contract_id:
            return Response(
                {"error": "contract_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            contract = Contract.objects.get(id=contract_id)
        except Contract.DoesNotExist:
            return Response(
                {"error": "Contract not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Import models at the top to avoid scoping issues
        from .models import ExculpatoryAnalysis, ExculpatoryClause
        from .serializers import ExculpatoryAnalysisSerializer

        # Check cache unless forcing refresh
        if not force_refresh:
            try:
                analysis = ExculpatoryAnalysis.objects.get(contract=contract)
                serializer = ExculpatoryAnalysisSerializer(analysis)
                logger.info(f"Returning cached exculpatory analysis for contract {contract_id}")

                return Response({
                    **serializer.data,
                    "cached": True
                })
            except ExculpatoryAnalysis.DoesNotExist:
                pass
        else:
            # Force refresh: Delete old cached analysis and clause records
            logger.info(f"Force refresh requested - deleting cached analysis for contract {contract_id}")

            # Delete cached analysis (will cascade delete related clauses via FK)
            ExculpatoryAnalysis.objects.filter(contract=contract).delete()
            logger.info(f"Deleted cached exculpatory analysis for fresh re-analysis")

        # Run fresh analysis
        return self._run_analysis(contract)

    def _run_analysis(self, contract):
        """Execute the actual analysis with enhanced risk allocation and interaction detection"""
        from .serializers import ExculpatoryAnalysisSerializer
        from ai.exculpatory_embeddings import generate_embeddings
        from ai.exculpatory_qdrant import get_pattern_store
        from ai.exculpatory_risk_engine import evaluate_clause, generate_summary

        try:
            # Get clauses from contract
            clauses = Clause.objects.filter(contract=contract)

            if not clauses.exists():
                return Response({
                    "error": "No clauses found for this contract",
                    "contract_id": contract.id
                }, status=status.HTTP_400_BAD_REQUEST)

            logger.info(f"Analyzing {clauses.count()} clauses for exculpatory content")

            # Prepare clause data
            clause_texts = [c.extracted_text or c.clause_name or "" for c in clauses]
            clause_names = [c.clause_name or c.clause_type or f"Clause {idx+1}" for idx, c in enumerate(clauses)]

            # Try to extract contract value from metadata
            contract_value = None
            if hasattr(contract, 'metadata') and contract.metadata:
                contract_value = contract.metadata.get('contract_value')

            # If not in metadata, try to extract from contract text (basic heuristic)
            if not contract_value and hasattr(contract, 'uploaded_file'):
                # This is a simple heuristic - could be enhanced
                logger.debug("Contract value not found in metadata, using default")
                contract_value = None  # Will skip financial calculations

            # Generate embeddings
            logger.info("Generating clause embeddings...")
            embeddings = generate_embeddings(clause_texts)

            # Get pattern store (Qdrant may be unavailable - degrade gracefully)
            pattern_store = None
            try:
                pattern_store = get_pattern_store()
            except Exception as qdrant_err:
                logger.warning(f"Qdrant unavailable, running analysis without vector pattern matching: {qdrant_err}")

            # Analyze each clause with enhanced evaluation
            analyzed_clauses = []
            for idx, (clause_text, clause_name, embedding) in enumerate(zip(clause_texts, clause_names, embeddings)):
                logger.debug(f"Analyzing clause {idx+1}/{len(clause_texts)}: {clause_name}")

                # Search for similar patterns (empty list if Qdrant is unavailable)
                pattern_matches = []
                if pattern_store is not None:
                    pattern_matches = pattern_store.search_similar_patterns(
                        clause_embedding=embedding,
                        limit=3,
                        threshold=0.50  # Lowered from 0.65 to detect more matches
                    )

                # Evaluate clause with enhanced analysis
                result = evaluate_clause(
                    clause_text=clause_text,
                    clause_name=clause_name,
                    clause_embedding=embedding,
                    pattern_matches=pattern_matches,
                    contract_value=contract_value  # Pass contract value for financial exposure
                )

                logger.info(f"Clause '{clause_name}': risk_score={result['risk_score']}, is_exculpatory={result['is_exculpatory']}, imbalance={result.get('imbalance_severity', 'N/A')}")

                analyzed_clauses.append(result)

            # Generate enhanced summary with interaction analysis
            summary = generate_summary(
                analyzed_clauses,
                total_clauses=clauses.count(),
                contract_value=contract_value
            )

            # Store in database with transaction to prevent race conditions
            logger.info("Storing enhanced analysis results in database...")
            from django.db import transaction

            with transaction.atomic():
                analysis, created = ExculpatoryAnalysis.objects.select_for_update().update_or_create(
                    contract=contract,
                    defaults={
                        "total_clauses": summary["total_clauses"],
                        "analyzed_clauses": summary["analyzed_clauses"],
                        "high_risk_count": summary["risk_distribution"]["high"],
                        "medium_risk_count": summary["risk_distribution"]["medium"],
                        "low_risk_count": summary["risk_distribution"]["low"],
                        "imbalanced_count": summary["imbalanced_clauses"],
                        "category_breakdown": summary["category_breakdown"],
                        "recommendation": summary["recommendation"]
                    }
                )

                # Delete old clauses and create new ones (within transaction)
                ExculpatoryClause.objects.filter(analysis=analysis).delete()

                # Create new clauses within the same transaction
                for clause_data in analyzed_clauses:
                    # Serialize impact chain data for storage
                    impact_chain_data = None
                    if "impact_chain" in clause_data and clause_data["impact_chain"]:
                        from ai.explainability_engine import format_impact_chain_for_display
                        impact_chain_data = {
                            "risk_rationale": clause_data["impact_chain"].risk_rationale,
                            "business_impact": clause_data["impact_chain"].business_impact,
                            "negotiation_strategy": clause_data["impact_chain"].negotiation_strategy,
                            "fallback_position": clause_data["impact_chain"].fallback_position,
                            "deal_breaker": clause_data["impact_chain"].deal_breaker,
                            "probability": clause_data["impact_chain"].probability,
                            "financial_exposure_range": clause_data["impact_chain"].financial_exposure_range,
                            "detected_patterns": clause_data["impact_chain"].detected_patterns,
                            "formatted_display": format_impact_chain_for_display(clause_data["impact_chain"])
                        }

                    ExculpatoryClause.objects.create(
                        analysis=analysis,
                        clause_name=clause_data["clause_name"],
                        text=clause_data["text"],
                        risk_score=clause_data["risk_score"],
                        is_exculpatory=clause_data["is_exculpatory"],
                        risk_category=clause_data["risk_category"],
                        controlled_by=clause_data["controlled_by"],
                        bearer=clause_data["bearer"],
                        is_imbalanced=clause_data["is_imbalanced"],
                        imbalance_explanation=clause_data["imbalance_explanation"],
                        pattern_matches=clause_data["pattern_matches"],
                        suggestions=clause_data.get("suggestions", []),
                        # Enhanced fields from Prof. Murali's research
                        imbalance_severity=clause_data.get("imbalance_severity", "LOW"),
                        imbalance_score=clause_data.get("imbalance_score", 0.0),
                        financial_exposure=clause_data.get("financial_exposure", {}),
                        proper_allocation_advice=clause_data.get("proper_allocation_advice", ""),
                        impact_chain_data=impact_chain_data,
                        deal_breaker=clause_data.get("deal_breaker", False),
                        probability=clause_data.get("probability", "MEDIUM")
                    )

            # Serialize and return
            serializer = ExculpatoryAnalysisSerializer(analysis)
            logger.info(f"Exculpatory analysis complete for contract {contract.id}")

            return Response({
                **serializer.data,
                "cached": False
            })

        except Exception as e:
            logger.error(f"Error in exculpatory analysis: {str(e)}", exc_info=True)
            return Response({
                "error": f"Analysis failed: {str(e)}",
                "contract_id": contract.id
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
