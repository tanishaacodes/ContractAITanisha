"""
API Views for Contract Counterfactual Engine.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
import logging

from .engine import (
    simulate_counterfactual,
    get_user_scenarios,
    compare_multiple_scenarios
)
from .models import CounterfactualScenario, HistoricalOutcome

logger = logging.getLogger(__name__)


class CounterfactualSimulateAPIView(APIView):
    """
    API endpoint for running counterfactual simulations.

    POST /api/counterfactual/simulate/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Run a counterfactual simulation.

        Request body:
        {
            "contract_id": "CONTRACT_001",
            "contract_text": "Full contract text...",
            "original_clause": "Original clause text...",
            "modified_clause": "Modified clause text...",
            "filters": {  // optional
                "contract_type": "Service Agreement",
                "industry": "Technology"
            }
        }
        """
        try:
            data = request.data

            # Validate required fields
            required_fields = ['contract_id', 'contract_text', 'original_clause', 'modified_clause']
            for field in required_fields:
                if field not in data:
                    return Response(
                        {"error": f"Missing required field: {field}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Extract data
            contract_id = data['contract_id']
            contract_text = data['contract_text']
            original_clause = data['original_clause']
            modified_clause = data['modified_clause']
            filters = data.get('filters', None)

            # Run simulation
            logger.info(f"Running counterfactual simulation for user {request.user.email}")
            result = simulate_counterfactual(
                contract_id=contract_id,
                contract_text=contract_text,
                original_clause=original_clause,
                modified_clause=modified_clause,
                user=request.user,
                filters=filters
            )

            if 'error' in result:
                return Response(
                    {"error": result['error']},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in counterfactual simulation: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CounterfactualCompareAPIView(APIView):
    """
    API endpoint for comparing multiple counterfactual scenarios.

    POST /api/counterfactual/compare/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Compare multiple clause modifications side-by-side.

        Request body:
        {
            "contract_id": "CONTRACT_001",
            "contract_text": "Full contract text...",
            "original_clause": "Original clause text...",
            "modified_clauses": [
                "Alternative version 1...",
                "Alternative version 2...",
                "Alternative version 3..."
            ]
        }
        """
        try:
            data = request.data

            # Validate required fields
            required_fields = ['contract_id', 'contract_text', 'original_clause', 'modified_clauses']
            for field in required_fields:
                if field not in data:
                    return Response(
                        {"error": f"Missing required field: {field}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            if not isinstance(data['modified_clauses'], list) or len(data['modified_clauses']) == 0:
                return Response(
                    {"error": "modified_clauses must be a non-empty list"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Run comparison
            logger.info(f"Comparing {len(data['modified_clauses'])} scenarios for user {request.user.email}")
            result = compare_multiple_scenarios(
                contract_id=data['contract_id'],
                contract_text=data['contract_text'],
                original_clause=data['original_clause'],
                modified_clauses=data['modified_clauses'],
                user=request.user
            )

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in scenario comparison: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CounterfactualHistoryAPIView(APIView):
    """
    API endpoint for retrieving user's counterfactual scenario history.

    GET /api/counterfactual/history/
    GET /api/counterfactual/history/?contract_id=CONTRACT_001
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get user's counterfactual simulation history.

        Query params:
        - contract_id (optional): Filter by specific contract
        - limit (optional): Maximum number of results (default: 10)
        """
        try:
            contract_id = request.query_params.get('contract_id', None)
            limit = int(request.query_params.get('limit', 10))

            scenarios = get_user_scenarios(
                user=request.user,
                contract_id=contract_id,
                limit=limit
            )

            return Response(
                {
                    "count": len(scenarios),
                    "scenarios": scenarios
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error retrieving scenario history: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CounterfactualScenarioDetailAPIView(APIView):
    """
    API endpoint for retrieving a specific scenario's details.

    GET /api/counterfactual/scenario/<id>/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, scenario_id):
        """
        Get detailed information about a specific scenario.
        """
        try:
            scenario = CounterfactualScenario.objects.get(
                id=scenario_id,
                user=request.user
            )

            result = {
                "id": scenario.id,
                "contract_id": scenario.contract_id,
                "original_clause": scenario.original_clause,
                "modified_clause": scenario.modified_clause,
                "simulated_outcome": scenario.simulated_outcome,
                "confidence_score": scenario.confidence_score,
                "risk_delta": scenario.risk_delta,
                "business_impact": scenario.business_impact,
                "legal_impact": scenario.legal_impact,
                "operational_impact": scenario.operational_impact,
                "scenario_type": scenario.scenario_type,
                "created_at": scenario.created_at.isoformat(),
                "updated_at": scenario.updated_at.isoformat(),
            }

            return Response(result, status=status.HTTP_200_OK)

        except CounterfactualScenario.DoesNotExist:
            return Response(
                {"error": "Scenario not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error retrieving scenario details: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class HistoricalOutcomeAPIView(APIView):
    """
    API endpoint for managing historical contract outcomes.

    GET /api/counterfactual/outcomes/
    POST /api/counterfactual/outcomes/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get historical outcomes (admin/analytics view).
        """
        try:
            limit = int(request.query_params.get('limit', 20))
            contract_type = request.query_params.get('contract_type', None)

            queryset = HistoricalOutcome.objects.all()

            if contract_type:
                queryset = queryset.filter(contract_type=contract_type)

            outcomes = queryset[:limit]

            result = [
                {
                    "contract_id": o.contract_id,
                    "contract_type": o.contract_type,
                    "industry": o.industry,
                    "dispute_occurred": o.dispute_occurred,
                    "litigation_occurred": o.litigation_occurred,
                    "renewal_success": o.renewal_success,
                    "revenue_impact": float(o.revenue_impact) if o.revenue_impact else None,
                    "operational_delays_days": o.operational_delays_days,
                    "outcome_recorded_date": o.outcome_recorded_date.isoformat() if o.outcome_recorded_date else None,
                }
                for o in outcomes
            ]

            return Response(
                {
                    "count": len(result),
                    "outcomes": result
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error retrieving historical outcomes: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        """
        Add a new historical outcome (for learning/training).

        This endpoint allows recording actual contract outcomes to improve
        future counterfactual predictions.
        """
        try:
            data = request.data

            # Validate required fields
            required_fields = ['contract_id', 'contract_type', 'key_clauses']
            for field in required_fields:
                if field not in data:
                    return Response(
                        {"error": f"Missing required field: {field}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Create historical outcome
            outcome = HistoricalOutcome.objects.create(
                contract_id=data['contract_id'],
                contract_type=data['contract_type'],
                industry=data.get('industry'),
                contract_value=data.get('contract_value'),
                dispute_occurred=data.get('dispute_occurred', False),
                dispute_details=data.get('dispute_details'),
                revenue_impact=data.get('revenue_impact'),
                litigation_occurred=data.get('litigation_occurred', False),
                renewal_success=data.get('renewal_success'),
                operational_delays_days=data.get('operational_delays_days'),
                key_clauses=data['key_clauses'],
                contract_start_date=data.get('contract_start_date'),
                contract_end_date=data.get('contract_end_date'),
                outcome_recorded_date=data.get('outcome_recorded_date'),
            )

            logger.info(f"Created historical outcome for contract {outcome.contract_id}")

            return Response(
                {
                    "message": "Historical outcome recorded successfully",
                    "contract_id": outcome.contract_id
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.error(f"Error creating historical outcome: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
