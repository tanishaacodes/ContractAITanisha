"""
Contract Redlining API Views
============================
Comprehensive API endpoints for the redlining feature:
- Start/manage redline sessions
- Analyze clauses for risk
- Accept/reject/modify suggestions
- Export to DOCX/PDF
"""

import os
from datetime import datetime
from django.conf import settings
from django.http import FileResponse, HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import (
    Contract, Clause, RedlineSession, RedlineChange,
    ContractRiskAnalysis, ClauseDeviation
)

from .redline_engine import (
    process_contract_for_redlining,
    analyze_clause,
    generate_redline_diff,
    regenerate_clause_suggestion
)

from .legal_explainability import (
    get_legal_explainability,
    generate_full_legal_analysis
)

from .document_generator import (
    generate_docx_redline,
    generate_pdf_redline,
    generate_track_changes_summary
)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_redline_session(request, contract_id):
    """
    Start a new redline session for a contract.

    Request body (optional):
    {
        "jurisdiction": "Common Law" | "US" | "UK" | "EU" | "UAE"
    }

    Returns:
    {
        "session_id": "...",
        "contract_id": "...",
        "total_clauses": 10,
        "high_risk_count": 3,
        "medium_risk_count": 4,
        "low_risk_count": 3,
        "clauses": [...]
    }
    """
    try:
        # Get contract and verify ownership
        contract = Contract.objects.get(id=contract_id)
        if contract.user != request.user:
            return Response(
                {'message': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check for contract text
        if not contract.full_text:
            return Response(
                {'message': 'Contract has no text content. Please upload a valid document.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get jurisdiction from request or default
        jurisdiction = request.data.get('jurisdiction', 'Common Law')

        # Create redline session
        session = RedlineSession.objects.create(
            contract=contract,
            user=request.user,
            jurisdiction=jurisdiction,
            status='IN_PROGRESS'
        )

        # Process contract for redlining
        print(f'[REDLINE] Processing contract {contract_id} for redlining')
        analysis_result = process_contract_for_redlining(contract.full_text, jurisdiction)

        # Create RedlineChange records for each clause
        changes_created = []
        for clause_data in analysis_result['clauses']:
            # Get legal explainability
            legal_analysis = get_legal_explainability(
                clause_data['original_text'],
                jurisdiction,
                clause_data['risk_type']
            )

            # Create change record
            change = RedlineChange.objects.create(
                session=session,
                clause_name=clause_data['clause_name'],
                clause_index=clause_data['index'],
                original_text=clause_data['original_text'],
                suggested_text=clause_data['suggested_text'],
                redline_diff=clause_data['redline_diff'],
                risk_type=clause_data['risk_type'],
                risk_score=clause_data['risk_score'],
                risk_explanation=clause_data['risk_explanation'],
                legal_doctrine=legal_analysis.get('doctrine', ''),
                court_reasoning=legal_analysis.get('court_reasoning', ''),
                litigation_risk=legal_analysis.get('litigation_risk', ''),
                judicial_treatment=legal_analysis.get('judicial_treatment', ''),
                status='PENDING'
            )

            changes_created.append({
                'id': str(change.id),
                'clause_name': change.clause_name,
                'clause_index': change.clause_index,
                'original_text': change.original_text,
                'suggested_text': change.suggested_text,
                'redline_diff': change.redline_diff,
                'risk_type': change.risk_type,
                'risk_score': change.risk_score,
                'risk_level': clause_data['risk_level'],
                'risk_explanation': change.risk_explanation,
                'legal_doctrine': change.legal_doctrine,
                'court_reasoning': change.court_reasoning,
                'litigation_risk': change.litigation_risk,
                'judicial_treatment': change.judicial_treatment,
                'status': change.status
            })

        # Update session statistics
        session.total_clauses_analyzed = len(changes_created)
        session.high_risk_count = analysis_result['high_risk_count']
        session.medium_risk_count = analysis_result['medium_risk_count']
        session.low_risk_count = analysis_result['low_risk_count']
        session.save()

        return Response({
            'message': 'Redline session started successfully',
            'session_id': str(session.id),
            'contract_id': str(contract.id),
            'contract_name': contract.original_filename,
            'jurisdiction': jurisdiction,
            'total_clauses': session.total_clauses_analyzed,
            'high_risk_count': session.high_risk_count,
            'medium_risk_count': session.medium_risk_count,
            'low_risk_count': session.low_risk_count,
            'overall_risk_level': analysis_result['overall_risk_level'],
            'average_risk_score': analysis_result['average_risk_score'],
            'clauses': changes_created
        })

    except Contract.DoesNotExist:
        return Response(
            {'message': 'Contract not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f'[REDLINE ERROR] Start session: {str(e)}')
        import traceback
        traceback.print_exc()
        return Response(
            {'message': 'Failed to start redline session', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_redline_session(request, session_id):
    """
    Get redline session details with all clauses.
    """
    try:
        session = RedlineSession.objects.get(id=session_id)

        if session.user != request.user:
            return Response(
                {'message': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get all changes in this session
        changes = session.changes.all().order_by('clause_index')

        changes_data = []
        for change in changes:
            risk_level = 'HIGH' if change.risk_score >= 70 else ('MEDIUM' if change.risk_score >= 40 else 'LOW')
            changes_data.append({
                'id': str(change.id),
                'clause_name': change.clause_name,
                'clause_index': change.clause_index,
                'original_text': change.original_text,
                'suggested_text': change.suggested_text,
                'accepted_text': change.accepted_text,
                'redline_diff': change.redline_diff,
                'risk_type': change.risk_type,
                'risk_score': change.risk_score,
                'risk_level': risk_level,
                'risk_explanation': change.risk_explanation,
                'legal_doctrine': change.legal_doctrine,
                'court_reasoning': change.court_reasoning,
                'litigation_risk': change.litigation_risk,
                'judicial_treatment': change.judicial_treatment,
                'status': change.status,
                'reviewed_at': change.reviewed_at.isoformat() if change.reviewed_at else None
            })

        return Response({
            'session_id': str(session.id),
            'contract_id': str(session.contract.id),
            'contract_name': session.contract.original_filename,
            'jurisdiction': session.jurisdiction,
            'status': session.status,
            'total_clauses': session.total_clauses_analyzed,
            'high_risk_count': session.high_risk_count,
            'medium_risk_count': session.medium_risk_count,
            'low_risk_count': session.low_risk_count,
            'changes_accepted': session.changes_accepted,
            'changes_rejected': session.changes_rejected,
            'created_at': session.created_at.isoformat(),
            'clauses': changes_data
        })

    except RedlineSession.DoesNotExist:
        return Response(
            {'message': 'Redline session not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f'[REDLINE ERROR] Get session: {str(e)}')
        return Response(
            {'message': 'Failed to retrieve redline session', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_redline_change(request, change_id):
    """
    Accept, reject, or modify a redline change.

    Request body:
    {
        "action": "accept" | "reject" | "modify",
        "accepted_text": "..." (required for modify, optional for accept)
    }
    """
    try:
        change = RedlineChange.objects.select_related('session', 'session__user').get(id=change_id)

        if change.session.user != request.user:
            return Response(
                {'message': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        action = request.data.get('action', '').lower()
        accepted_text = request.data.get('accepted_text')

        if action == 'accept':
            change.status = 'ACCEPTED'
            change.accepted_text = accepted_text or change.suggested_text
            change.reviewed_by = request.user
            change.reviewed_at = timezone.now()
            change.session.changes_accepted += 1

        elif action == 'reject':
            change.status = 'REJECTED'
            change.accepted_text = change.original_text  # Keep original
            change.reviewed_by = request.user
            change.reviewed_at = timezone.now()
            change.session.changes_rejected += 1

        elif action == 'modify':
            if not accepted_text:
                return Response(
                    {'message': 'accepted_text is required for modify action'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            change.status = 'MODIFIED'
            change.accepted_text = accepted_text
            change.redline_diff = generate_redline_diff(change.original_text, accepted_text)
            change.reviewed_by = request.user
            change.reviewed_at = timezone.now()
            change.session.changes_accepted += 1  # Modified counts as accepted

        else:
            return Response(
                {'message': 'Invalid action. Use: accept, reject, or modify'},
                status=status.HTTP_400_BAD_REQUEST
            )

        change.save()
        change.session.save()

        return Response({
            'message': f'Change {action}ed successfully',
            'change_id': str(change.id),
            'status': change.status,
            'accepted_text': change.accepted_text,
            'session_accepted': change.session.changes_accepted,
            'session_rejected': change.session.changes_rejected
        })

    except RedlineChange.DoesNotExist:
        return Response(
            {'message': 'Redline change not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f'[REDLINE ERROR] Update change: {str(e)}')
        return Response(
            {'message': 'Failed to update redline change', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def regenerate_suggestion(request, change_id):
    """
    Regenerate AI suggestion for a specific clause with optional perspective.

    Request body:
    {
        "perspective": "balanced" | "buyer_favorable" | "seller_favorable"
    }
    """
    try:
        change = RedlineChange.objects.select_related('session', 'session__user').get(id=change_id)

        if change.session.user != request.user:
            return Response(
                {'message': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        perspective = request.data.get('perspective', 'balanced')

        # Regenerate suggestion
        result = regenerate_clause_suggestion(
            change.original_text,
            perspective,
            change.session.jurisdiction
        )

        # Update change
        change.suggested_text = result['suggested_clause']
        change.redline_diff = generate_redline_diff(change.original_text, result['suggested_clause'])
        change.save()

        return Response({
            'message': 'Suggestion regenerated',
            'change_id': str(change.id),
            'suggested_text': change.suggested_text,
            'redline_diff': change.redline_diff,
            'changes_made': result['changes_made'],
            'risk_reduction': result['risk_reduction']
        })

    except RedlineChange.DoesNotExist:
        return Response(
            {'message': 'Redline change not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f'[REDLINE ERROR] Regenerate: {str(e)}')
        return Response(
            {'message': 'Failed to regenerate suggestion', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_legal_analysis(request, change_id):
    """
    Get detailed legal analysis for a specific clause.
    """
    try:
        change = RedlineChange.objects.select_related('session', 'session__user').get(id=change_id)

        if change.session.user != request.user:
            return Response(
                {'message': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Generate full legal analysis
        analysis = generate_full_legal_analysis(
            change.original_text,
            change.session.jurisdiction,
            change.risk_type
        )

        return Response({
            'change_id': str(change.id),
            'clause_name': change.clause_name,
            'original_text': change.original_text,
            'legal_analysis': analysis
        })

    except RedlineChange.DoesNotExist:
        return Response(
            {'message': 'Redline change not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f'[REDLINE ERROR] Legal analysis: {str(e)}')
        return Response(
            {'message': 'Failed to generate legal analysis', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_redline_docx(request, session_id):
    """
    Export redline session to DOCX format with track changes styling.
    """
    try:
        session = RedlineSession.objects.get(id=session_id)

        if session.user != request.user:
            return Response(
                {'message': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get all changes
        changes = session.changes.all().order_by('clause_index')

        clauses_data = []
        for change in changes:
            clauses_data.append({
                'clause_name': change.clause_name,
                'original_text': change.original_text,
                'suggested_text': change.suggested_text,
                'accepted_text': change.accepted_text,
                'risk_type': change.risk_type,
                'risk_score': change.risk_score,
                'risk_explanation': change.risk_explanation,
                'court_reasoning': change.court_reasoning,
                'status': change.status
            })

        # Generate DOCX
        output_path = generate_docx_redline(
            clauses_data,
            session.contract.original_filename
        )

        # Update session
        session.docx_exported_at = timezone.now()
        session.exported_file_path = output_path
        session.status = 'EXPORTED'
        session.save()

        # Return file
        response = FileResponse(
            open(output_path, 'rb'),
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(output_path)}"'
        return response

    except RedlineSession.DoesNotExist:
        return Response(
            {'message': 'Redline session not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f'[REDLINE ERROR] Export DOCX: {str(e)}')
        import traceback
        traceback.print_exc()
        return Response(
            {'message': 'Failed to export DOCX', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_redline_pdf(request, session_id):
    """
    Export redline session to PDF format.
    """
    try:
        session = RedlineSession.objects.get(id=session_id)

        if session.user != request.user:
            return Response(
                {'message': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get all changes
        changes = session.changes.all().order_by('clause_index')

        clauses_data = []
        for change in changes:
            clauses_data.append({
                'clause_name': change.clause_name,
                'original_text': change.original_text,
                'suggested_text': change.suggested_text,
                'accepted_text': change.accepted_text,
                'risk_type': change.risk_type,
                'risk_score': change.risk_score,
                'risk_explanation': change.risk_explanation,
                'court_reasoning': change.court_reasoning,
                'status': change.status
            })

        # Generate PDF
        output_path = generate_pdf_redline(
            clauses_data,
            session.contract.original_filename
        )

        # Update session
        session.pdf_exported_at = timezone.now()
        session.status = 'EXPORTED'
        session.save()

        # Return file
        response = FileResponse(
            open(output_path, 'rb'),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(output_path)}"'
        return response

    except RedlineSession.DoesNotExist:
        return Response(
            {'message': 'Redline session not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f'[REDLINE ERROR] Export PDF: {str(e)}')
        import traceback
        traceback.print_exc()
        return Response(
            {'message': 'Failed to export PDF', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_redline_session(request, session_id):
    """
    Mark a redline session as completed.
    """
    try:
        session = RedlineSession.objects.get(id=session_id)

        if session.user != request.user:
            return Response(
                {'message': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        session.status = 'COMPLETED'
        session.completed_at = timezone.now()
        session.save()

        # Generate summary
        changes = session.changes.all()
        clauses_data = [
            {'risk_score': c.risk_score, 'status': c.status}
            for c in changes
        ]
        summary = generate_track_changes_summary(clauses_data)

        return Response({
            'message': 'Redline session completed',
            'session_id': str(session.id),
            'status': session.status,
            'completed_at': session.completed_at.isoformat(),
            'summary': summary
        })

    except RedlineSession.DoesNotExist:
        return Response(
            {'message': 'Redline session not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f'[REDLINE ERROR] Complete session: {str(e)}')
        return Response(
            {'message': 'Failed to complete session', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_redline_sessions(request):
    """
    List all redline sessions for the current user.
    """
    try:
        sessions = RedlineSession.objects.filter(user=request.user).order_by('-created_at')

        sessions_data = []
        for session in sessions:
            sessions_data.append({
                'id': str(session.id),
                'contract_id': str(session.contract.id),
                'contract_name': session.contract.original_filename,
                'jurisdiction': session.jurisdiction,
                'status': session.status,
                'total_clauses': session.total_clauses_analyzed,
                'high_risk_count': session.high_risk_count,
                'medium_risk_count': session.medium_risk_count,
                'low_risk_count': session.low_risk_count,
                'changes_accepted': session.changes_accepted,
                'changes_rejected': session.changes_rejected,
                'created_at': session.created_at.isoformat(),
                'completed_at': session.completed_at.isoformat() if session.completed_at else None
            })

        return Response({
            'total': len(sessions_data),
            'sessions': sessions_data
        })

    except Exception as e:
        print(f'[REDLINE ERROR] List sessions: {str(e)}')
        return Response(
            {'message': 'Failed to list redline sessions', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_contract_redline_sessions(request, contract_id):
    """
    Get all redline sessions for a specific contract.
    """
    try:
        contract = Contract.objects.get(id=contract_id)

        if contract.user != request.user:
            return Response(
                {'message': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        sessions = RedlineSession.objects.filter(contract=contract).order_by('-created_at')

        sessions_data = []
        for session in sessions:
            sessions_data.append({
                'id': str(session.id),
                'jurisdiction': session.jurisdiction,
                'status': session.status,
                'total_clauses': session.total_clauses_analyzed,
                'high_risk_count': session.high_risk_count,
                'changes_accepted': session.changes_accepted,
                'created_at': session.created_at.isoformat()
            })

        return Response({
            'contract_id': str(contract.id),
            'contract_name': contract.original_filename,
            'total_sessions': len(sessions_data),
            'sessions': sessions_data
        })

    except Contract.DoesNotExist:
        return Response(
            {'message': 'Contract not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f'[REDLINE ERROR] Get contract sessions: {str(e)}')
        return Response(
            {'message': 'Failed to get contract redline sessions', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
