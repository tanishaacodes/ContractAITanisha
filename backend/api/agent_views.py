"""
API Views for Agentic AI System
Exposes the LangGraph agent to the frontend for intelligent contract analysis.
"""

import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from asgiref.sync import async_to_sync
import asyncio

from core.models import Contract, AnalysisResult
from agents.contract_agent import run_analysis_workflow


# ========================================
# AGENT ANALYSIS ENDPOINT
# ========================================
@csrf_exempt
@require_http_methods(["POST"])
def analyze_with_agent(request, contract_id):
    """
    Main endpoint for agentic contract analysis.

    POST /api/agent/contracts/<contract_id>/analyze
    Body: {
        "mode": "full" | "risk" | "intent" | "summary" | "extract" | "classify",
        "query": "Optional natural language query"
    }

    Response: {
        "status": "success",
        "contract_id": "...",
        "mode": "...",
        "results": { ... },
        "tools_used": ["..."],
        "execution_time_seconds": 1.23
    }
    """
    try:
        # Parse request body
        body = json.loads(request.body.decode('utf-8'))
        mode = body.get('mode', 'full')
        user_query = body.get('query', None)

        # Validate contract exists
        try:
            contract = Contract.objects.get(id=contract_id)
        except Contract.DoesNotExist:
            return JsonResponse({
                "status": "error",
                "message": f"Contract {contract_id} not found"
            }, status=404)

        # Run the agent analysis (async to sync conversion)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            run_analysis_workflow(str(contract_id), user_query, mode)
        )
        loop.close()

        return JsonResponse(result, status=200)

    except json.JSONDecodeError:
        return JsonResponse({
            "status": "error",
            "message": "Invalid JSON in request body"
        }, status=400)
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": f"Agent error: {str(e)}"
        }, status=500)


# ========================================
# GET LATEST ANALYSIS RESULTS
# ========================================
@require_http_methods(["GET"])
def get_agent_analysis(request, contract_id):
    """
    Retrieve the latest agentic analysis results for a contract.

    GET /api/agent/contracts/<contract_id>/results

    Response: {
        "status": "success",
        "contract_id": "...",
        "analysis": { ... },
        "analyzed_at": "...",
        "tools_used": ["..."]
    }
    """
    try:
        # Fetch the latest analysis result
        analysis = AnalysisResult.objects.filter(
            contract_id=contract_id
        ).order_by('-analyzed_at').first()

        if not analysis:
            return JsonResponse({
                "status": "not_found",
                "message": "No analysis results found for this contract. Run analysis first.",
                "contract_id": str(contract_id)
            }, status=404)

        # Format response
        response_data = {
            "status": "success",
            "contract_id": str(contract_id),
            "analysis": {
                "executive_summary": analysis.executive_summary,
                "risk_analysis": {
                    "risk_score": analysis.risk_score,
                    "risk_level": analysis.risk_level,
                    "risk_flags": analysis.risk_flags
                },
                "extracted_clauses": analysis.extracted_clauses,
                "classification": {
                    "classified_as": analysis.agent_metadata.get("classification") if analysis.agent_metadata else None,
                    "confidence": analysis.agent_metadata.get("classification_confidence") if analysis.agent_metadata else None
                },
                "intent_analysis": {
                    "primary_intent": analysis.primary_intent,
                    "confidence": analysis.intent_confidence,
                    "metadata": analysis.agent_metadata
                },
                "compliance": {
                    "is_compliant": analysis.is_compliant,
                    "issues": analysis.compliance_issues
                }
            },
            "meta": {
                "agent_version": analysis.agent_version,
                "tools_used": analysis.tools_used,
                "execution_time_seconds": analysis.execution_time_seconds,
                "analyzed_at": analysis.analyzed_at.isoformat(),
                "updated_at": analysis.updated_at.isoformat()
            }
        }

        return JsonResponse(response_data, status=200)

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": f"Error retrieving analysis: {str(e)}"
        }, status=500)


# ========================================
# QUICK AGENT ACTIONS
# ========================================
@csrf_exempt
@require_http_methods(["POST"])
def quick_risk_score(request, contract_id):
    """
    Quick endpoint for risk scoring only.

    POST /api/agent/contracts/<contract_id>/quick-risk
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            run_analysis_workflow(str(contract_id), mode="risk")
        )
        loop.close()

        return JsonResponse(result, status=200)
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": f"Error: {str(e)}"
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def quick_intent_mine(request, contract_id):
    """
    Quick endpoint for intent mining only.

    POST /api/agent/contracts/<contract_id>/quick-intent
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            run_analysis_workflow(str(contract_id), mode="intent")
        )
        loop.close()

        return JsonResponse(result, status=200)
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": f"Error: {str(e)}"
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def quick_summary(request, contract_id):
    """
    Quick endpoint for executive summary only.

    POST /api/agent/contracts/<contract_id>/quick-summary
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            run_analysis_workflow(str(contract_id), mode="summary")
        )
        loop.close()

        return JsonResponse(result, status=200)
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": f"Error: {str(e)}"
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def quick_classify(request, contract_id):
    """
    Quick endpoint for classification only.

    POST /api/agent/contracts/<contract_id>/quick-classify
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            run_analysis_workflow(str(contract_id), mode="classify")
        )
        loop.close()

        return JsonResponse(result, status=200)
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": f"Error: {str(e)}"
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def quick_extract_clauses(request, contract_id):
    """
    Quick endpoint for clause extraction only.

    POST /api/agent/contracts/<contract_id>/quick-extract
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            run_analysis_workflow(str(contract_id), mode="extract")
        )
        loop.close()

        return JsonResponse(result, status=200)
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": f"Error: {str(e)}"
        }, status=500)


# ========================================
# AGENT HEALTH CHECK
# ========================================
@require_http_methods(["GET"])
def agent_health(request):
    """
    Check if the agent system is operational.

    GET /api/agent/health
    """
    try:
        # Don't initialize the agent yet, just check if imports work
        from agents import contract_agent

        return JsonResponse({
            "status": "healthy",
            "agent_version": "1.0",
            "tools_available": [
                "extract_clauses",
                "generate_summary",
                "classify_contract",
                "calculate_risk",
                "mine_intent"
            ],
            "model": "qwen2.5:0.5b (Ollama)"
        }, status=200)
    except Exception as e:
        return JsonResponse({
            "status": "unhealthy",
            "error": str(e)
        }, status=500)
