"""
NEW SMART SEARCH FEATURES - Additional API Views
Legal-BERT, Node2Vec, LangChain, Temporal Analysis, Anomaly Detection
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from core.models import Contract, ContractRiskAnalysis, Clause

logger = logging.getLogger(__name__)


class LegalBERTClassificationView(APIView):
    """Legal-BERT clause classification endpoint."""
    permission_classes = [AllowAny]

    def post(self, request):
        from .legal_bert_classifier import get_legal_bert_classifier

        clause_text = request.data.get("clause_text", "").strip()
        top_k = request.data.get("top_k", 3)

        if not clause_text:
            return Response({"error": "clause_text required"}, status=400)

        try:
            classifier = get_legal_bert_classifier()
            classification = classifier.classify_clause(clause_text, top_k=top_k)
            risk_score, risk_level = classifier.extract_risk_score(clause_text)
            comparison = classifier.compare_with_benchmark(clause_text)

            return Response({
                "clause_text": clause_text[:200] + "..." if len(clause_text) > 200 else clause_text,
                "classification": classification,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "benchmark_comparison": comparison,
                "model": "nlpaueb/legal-bert-base-uncased",
                "success": True
            })

        except Exception as e:
            logger.error(f"Legal-BERT error: {e}")
            return Response({"error": str(e), "success": False}, status=500)


class Node2VecRecommendationsView(APIView):
    """Node2Vec graph embedding-based recommendations."""
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            from .node2vec_embeddings import get_node2vec_embedder, _GENSIM_AVAILABLE
        except Exception:
            _GENSIM_AVAILABLE = False
        from contractai.neo4j_config import check_neo4j_available

        if not _GENSIM_AVAILABLE:
            return Response({
                "recommendations": [],
                "method": "Node2Vec",
                "message": "Node2Vec recommendations unavailable (gensim not installed). Install with: pip install gensim",
                "success": True
            })

        from .node2vec_embeddings import get_node2vec_embedder
        from ai.graph_driver import get_neo4j_driver

        node_id = request.data.get("node_id")
        top_k = request.data.get("top_k", 5)

        if not node_id:
            return Response({"error": "node_id required"}, status=400)

        try:
            # Check Neo4j availability
            if not check_neo4j_available():
                return Response({
                    "error": "Neo4j is not available. Node2Vec requires Neo4j connection.",
                    "success": False
                }, status=503)

            embedder = get_node2vec_embedder()

            if not embedder.embeddings:
                logger.info("Training Node2Vec embeddings (first time setup)...")
                neo4j_driver_wrapper = get_neo4j_driver()
                if not neo4j_driver_wrapper.driver:
                    return Response({
                        "error": "Neo4j driver not initialized. Check Neo4j connection.",
                        "success": False
                    }, status=503)
                # Pass the actual driver, not the wrapper
                embedder.fit(neo4j_driver_wrapper.driver)

            # Parse node_id if it's a string like "clause-0"
            neo4j_node_id = None
            if isinstance(node_id, str) and node_id.startswith("clause-"):
                # Extract clause index from "clause-X"
                try:
                    clause_index = int(node_id.split("-")[1])
                    # Query Neo4j to get the internal node ID for this clause index
                    neo4j_driver_wrapper = get_neo4j_driver()
                    if neo4j_driver_wrapper.driver:
                        with neo4j_driver_wrapper.driver.session() as session:
                            result = session.run("""
                                MATCH (cl:Clause)
                                WHERE cl.clauseIndex = $idx
                                RETURN id(cl) as node_id
                                LIMIT 1
                            """, idx=clause_index)
                            record = result.single()
                            if record:
                                neo4j_node_id = record["node_id"]
                                logger.info(f"Mapped {node_id} to Neo4j ID: {neo4j_node_id}")
                except Exception as e:
                    logger.error(f"Failed to map node_id: {e}")

            # If we couldn't map, return helpful message
            if neo4j_node_id is None:
                if isinstance(node_id, str) and node_id.startswith("clause-"):
                    return Response({
                        "node_id": node_id,
                        "recommendations": [],
                        "message": "Could not find Neo4j node for this clause. Make sure the graph was built with the latest version.",
                        "method": "Node2Vec",
                        "success": True
                    })
                else:
                    neo4j_node_id = int(node_id)

            recommendations = embedder.get_clause_recommendations(neo4j_node_id, top_k=top_k)

            return Response({
                "node_id": node_id,
                "recommendations": recommendations,
                "method": "Node2Vec",
                "success": True
            })

        except ValueError as e:
            logger.error(f"Node2Vec invalid node_id: {e}")
            return Response({
                "error": f"Invalid node_id format: {node_id}",
                "success": False
            }, status=400)
        except Exception as e:
            logger.error(f"Node2Vec error: {e}", exc_info=True)
            return Response({"error": str(e), "success": False}, status=500)


class LangChainAgentSearchView(APIView):
    """LangChain ReAct agent for intelligent search."""
    permission_classes = [AllowAny]

    def post(self, request):
        from .langchain_search_agent import SmartSearchLangChainAgent

        query = request.data.get("query", "").strip()
        if not query:
            return Response({"error": "query required"}, status=400)

        try:
            # Get user's auth token from request
            auth_header = request.headers.get('Authorization', '')
            auth_token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else None

            # Create agent instance with auth token for this request
            agent = SmartSearchLangChainAgent(auth_token=auth_token)
            result = agent.search(query)

            return Response({
                "query": query,
                "answer": result.get('answer', ''),
                "tools_used": result.get('tools_used', []),
                "success": result.get('success', False),
                "framework": "LangChain ReAct"
            })

        except Exception as e:
            logger.error(f"LangChain error: {e}")
            return Response({"error": str(e), "success": False}, status=500)


class TemporalAnalysisView(APIView):
    """Temporal risk analysis - track risk evolution over time."""
    permission_classes = [AllowAny]

    def post(self, request):
        from .temporal_anomaly_engine import get_temporal_analyzer

        action = request.data.get("action", "trend")
        contract_id = request.data.get("contract_id")

        if not contract_id:
            return Response({"error": "contract_id required"}, status=400)

        try:
            analyzer = get_temporal_analyzer()

            risk_analyses = ContractRiskAnalysis.objects.filter(
                contract_id=contract_id
            ).order_by('created_at')

            for analysis in risk_analyses:
                analyzer.add_risk_snapshot(
                    contract_id=contract_id,
                    risk_score=analysis.overall_risk_score or 0.0,
                    timestamp=analysis.created_at
                )

            if action == "trend":
                result = analyzer.get_risk_trend(contract_id, days_back=request.data.get("days_back", 90))
            elif action == "predict":
                result = analyzer.predict_future_risk(contract_id, days_forward=request.data.get("days_forward", 30))
            elif action == "spike":
                result = analyzer.detect_risk_spike(contract_id)
                if result is None:
                    result = {"spike_detected": False}
            else:
                return Response({"error": "Unknown action"}, status=400)

            return Response({
                "contract_id": contract_id,
                "action": action,
                "result": result,
                "success": True
            })

        except Exception as e:
            logger.error(f"Temporal analysis error: {e}")
            return Response({"error": str(e), "success": False}, status=500)


class AnomalyDetectionView(APIView):
    """Anomaly detection using Isolation Forest."""
    permission_classes = [AllowAny]

    def post(self, request):
        from .temporal_anomaly_engine import get_anomaly_detector

        try:
            detector = get_anomaly_detector()

            from core.models import ContractRiskAnalysis as _CRA
            import re as _re_a
            contracts = Contract.objects.filter(user=request.user)[:500]

            def _safe_float_a(v):
                if v is None: return 0.0
                s = _re_a.sub(r'[^0-9.]', '', str(v).replace(',', ''))
                try: return float(s)
                except: return 0.0

            contract_data = []
            for contract in contracts:
                risk_analysis = _CRA.objects.filter(contract=contract).first()
                raw_score = float(risk_analysis.risk_score) if risk_analysis and risk_analysis.risk_score else 0.0
                norm_score = raw_score / 100.0 if raw_score > 1 else raw_score
                contract_data.append({
                    'id': contract.id,
                    'title': contract.original_filename or str(contract.id),
                    'risk_score': norm_score,
                    'liability_score': 0.5 if contract.liability_level == 'HIGH' else 0.2,
                    'fm_risk_score': 0.3,
                    'num_clauses': Clause.objects.filter(contract=contract).count(),
                    'contract_value': _safe_float_a(contract.contract_value),
                    'high_risk_clauses': [],
                    'obligation_count': 0
                })

            if not detector.is_fitted:
                detector.fit(contract_data)

            anomalies = detector.detect_anomalies(contract_data)

            # Enrich anomalies with title from contract_data
            id_to_title = {str(cd['id']): cd['title'] for cd in contract_data}
            for a in anomalies:
                a['contract_title'] = id_to_title.get(str(a.get('contract_id')), str(a.get('contract_id', '')))

            return Response({
                "anomalies": anomalies[:20],
                "count": len(anomalies),
                "success": True
            })

        except Exception as e:
            logger.error(f"Anomaly detection error: {e}")
            return Response({"error": str(e), "success": False}, status=500)


class RealTimeGraphSyncView(APIView):
    """Real-time graph synchronization."""
    permission_classes = [AllowAny]

    def post(self, request):
        contract_id = request.data.get("contract_id")
        if not contract_id:
            return Response({"error": "contract_id required"}, status=400)

        try:
            contract = Contract.objects.get(id=contract_id, user=request.user)

            # Lightweight sync: only push this contract's clauses to Neo4j
            try:
                from .search_intelligence_views import _push_to_neo4j, _extract_clauses_rule_based
                text = contract.full_text or ""
                if text:
                    extracted = _extract_clauses_rule_based(text)
                    _push_to_neo4j(contract, extracted)
            except Exception as neo4j_err:
                logger.warning(f"Neo4j sync skipped: {neo4j_err}")

            # Invalidate FAISS so next search rebuilds index
            try:
                from .search_intelligence_views import _EmbeddingFAISSIndex
                faiss_idx = _EmbeddingFAISSIndex()
                faiss_idx.invalidate()
            except Exception:
                pass

            return Response({
                "contract_id": contract_id,
                "synced": True,
                "success": True
            })

        except Contract.DoesNotExist:
            return Response({"error": "Contract not found"}, status=404)
        except Exception as e:
            logger.error(f"Sync error: {e}")
            return Response({"error": str(e), "success": False}, status=500)


class CFOFinancialMetricsView(APIView):
    """CFO Financial Risk Metrics endpoint."""
    permission_classes = [AllowAny]

    def post(self, request):
        from .cfo_risk_metrics import get_cfo_engine

        action = request.data.get("action", "expected_loss")  # expected_loss, var, racv, cash_flow, report
        contract_id = request.data.get("contract_id")

        try:
            engine = get_cfo_engine()

            if action == "report":
                # Generate comprehensive portfolio report
                from core.models import ContractRiskAnalysis as _CRA2
                import re as _re_c
                contracts = Contract.objects.filter(user=request.user)[:500]

                def _safe_float_cfo(v):
                    if v is None: return 0.0
                    s = _re_c.sub(r'[^0-9.]', '', str(v).replace(',', ''))
                    try: return float(s)
                    except: return 0.0

                contract_data = []
                for contract in contracts:
                    risk_analysis = _CRA2.objects.filter(contract=contract).first()
                    raw_score = float(risk_analysis.risk_score) if risk_analysis and risk_analysis.risk_score else 0.0
                    norm_score = raw_score / 100.0 if raw_score > 1 else raw_score
                    contract_data.append({
                        'id': contract.id,
                        'title': contract.original_filename or str(contract.id),
                        'contract_value': _safe_float_cfo(contract.contract_value),
                        'risk_score': norm_score,
                        'risk_level': risk_analysis.risk_level if risk_analysis else 'MEDIUM',
                        'contract_type': contract.contract_type or 'default',
                        'liability_level': contract.liability_level or 'MEDIUM'
                    })

                report = engine.generate_cfo_risk_report(contract_data)
                return Response({"report": report, "success": True})

            elif contract_id:
                # Single contract metrics
                from core.models import ContractRiskAnalysis as _CRA3
                contract = Contract.objects.get(id=contract_id, user=request.user)
                risk_analysis = _CRA3.objects.filter(contract=contract).first()

                import re as _re2
                def _pv(v):
                    s = _re2.sub(r'[^0-9.]', '', str(v or '').replace(',', ''))
                    try: return float(s)
                    except: return 0.0

                contract_value = _pv(contract.contract_value)
                raw_score = float(risk_analysis.risk_score) if risk_analysis and risk_analysis.risk_score else 0.0
                risk_score = raw_score / 100.0 if raw_score > 1 else raw_score
                contract_type = contract.contract_type or 'default'
                liability_level = contract.liability_level or 'MEDIUM'

                if action == "expected_loss":
                    result = engine.calculate_expected_loss(contract_value, risk_score, contract_type, liability_level)
                elif action == "racv":
                    result = engine.calculate_risk_adjusted_contract_value(contract_value, risk_score, contract_type)
                elif action == "cash_flow":
                    fm_risk = 0.0  # Could pull from FM risk scorer
                    result = engine.calculate_cash_flow_impact(contract_value, risk_score, 30, fm_risk)
                else:
                    return Response({"error": "Unknown action"}, status=400)

                return Response({"contract_id": contract_id, "metrics": result, "success": True})

            else:
                return Response({"error": "contract_id or action=report required"}, status=400)

        except Contract.DoesNotExist:
            return Response({"error": "Contract not found"}, status=404)
        except Exception as e:
            logger.error(f"CFO metrics error: {e}")
            return Response({"error": str(e), "success": False}, status=500)


class PartyAttributionView(APIView):
    """Party Attribution classification endpoint."""
    permission_classes = [AllowAny]

    def post(self, request):
        from .party_attribution import get_party_classifier

        clause_text = request.data.get("clause_text", "").strip()
        clause_type = request.data.get("clause_type")
        contract_id = request.data.get("contract_id")

        if not clause_text and not contract_id:
            return Response({"error": "clause_text or contract_id required"}, status=400)

        try:
            classifier = get_party_classifier()

            if contract_id:
                # Analyze full contract balance
                contract = Contract.objects.get(id=contract_id, user=request.user)
                clauses = contract.clauses.all()

                clause_data = [
                    {'text': clause.text, 'type': clause.type}
                    for clause in clauses
                ]

                # This would need the full method implementation
                result = {
                    'contract_id': contract_id,
                    'total_clauses': len(clause_data),
                    'attribution': 'BALANCED',
                    'message': 'Full contract balance analysis coming soon'
                }

            else:
                # Single clause classification
                result = classifier.classify_clause(clause_text, clause_type)

            return Response({
                "clause_text": clause_text[:200] if clause_text else None,
                "attribution_result": result,
                "success": True
            })

        except Contract.DoesNotExist:
            return Response({"error": "Contract not found"}, status=404)
        except Exception as e:
            logger.error(f"Party attribution error: {e}")
            return Response({"error": str(e), "success": False}, status=500)
