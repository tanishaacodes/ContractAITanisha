"""
Feature 3: Live Clause Co-Pilot (Negotiation Mode) API Views
Real-time negotiation support with AI-powered clause suggestions
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg
from datetime import datetime
import json

from core.models import (
    Contract, Clause, ClauseVersion, ClauseEvent,
    NegotiationSession, NegotiationMessage,
    NegotiationClauseSuggestion, NegotiationPosition,
    User
)


class NegotiationSessionListView(APIView):
    """
    GET: List all negotiation sessions for a contract or user
    POST: Create a new negotiation session
    """
    permission_classes = [AllowAny]

    def get(self, request):
        """List negotiation sessions"""
        contract_id = request.query_params.get('contract_id')
        user_id = request.query_params.get('user_id')
        status_filter = request.query_params.get('status', 'ACTIVE')

        sessions = NegotiationSession.objects.all()

        if contract_id:
            sessions = sessions.filter(contract_id=contract_id)
        if user_id:
            sessions = sessions.filter(created_by_id=user_id)
        if status_filter and status_filter != 'ALL':
            sessions = sessions.filter(status=status_filter)

        sessions_data = []
        for session in sessions:
            message_count = session.messages.count()
            suggestion_count = session.suggestions.count()
            pending_suggestions = session.suggestions.filter(status='PENDING').count()

            sessions_data.append({
                'id': session.id,
                'session_name': session.session_name,
                'contract': {
                    'id': session.contract.id,
                    'filename': session.contract.original_filename,
                },
                'status': session.status,
                'our_party_role': session.our_party_role,
                'counterparty_name': session.counterparty_name,
                'message_count': message_count,
                'suggestion_count': suggestion_count,
                'pending_suggestions': pending_suggestions,
                'objectives': session.objectives,
                'started_at': session.started_at.isoformat(),
                'last_activity_at': session.last_activity_at.isoformat(),
            })

        return Response({
            'success': True,
            'sessions': sessions_data,
            'total': len(sessions_data)
        })

    def post(self, request):
        """Create a new negotiation session"""
        contract_id = request.data.get('contract_id')
        session_name = request.data.get('session_name')
        our_party_role = request.data.get('our_party_role', 'CLIENT')
        counterparty_name = request.data.get('counterparty_name', '')
        objectives = request.data.get('objectives', [])
        risk_tolerance = request.data.get('risk_tolerance', 'MEDIUM')

        # Get contract
        contract = get_object_or_404(Contract, id=contract_id)

        # Get first available user (in production, use authenticated user)
        user = User.objects.first()
        if not user:
            return Response({
                'success': False,
                'error': 'No users found in system'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create session
        session = NegotiationSession.objects.create(
            contract=contract,
            created_by=user,
            session_name=session_name or f"Negotiation for {contract.original_filename}",
            our_party_role=our_party_role,
            counterparty_name=counterparty_name,
            objectives=objectives,
            risk_tolerance=risk_tolerance,
            status='ACTIVE'
        )

        # Create welcome message from AI Co-Pilot
        NegotiationMessage.objects.create(
            session=session,
            sender=None,  # AI message
            message_type='AI',
            content=f"Hi! I'm your AI negotiation co-pilot. I'll help you negotiate {contract.original_filename}. "
                   f"I've identified {contract.clauses.count()} clauses to review. What would you like to focus on first?",
            ai_confidence=0.95
        )

        return Response({
            'success': True,
            'session': {
                'id': session.id,
                'session_name': session.session_name,
                'status': session.status,
                'started_at': session.started_at.isoformat()
            }
        }, status=status.HTTP_201_CREATED)


class NegotiationSessionDetailView(APIView):
    """
    GET: Get session details
    PUT: Update session
    DELETE: Delete/cancel session
    """
    permission_classes = [AllowAny]

    def get(self, request, session_id):
        """Get session details with messages and suggestions"""
        session = get_object_or_404(NegotiationSession, id=session_id)

        # Get messages
        messages = session.messages.order_by('created_at')
        messages_data = [{
            'id': msg.id,
            'message_type': msg.message_type,
            'content': msg.content,
            'sender': msg.sender.email if msg.sender else 'AI Co-Pilot',
            'ai_confidence': msg.ai_confidence,
            'reasoning': msg.reasoning,
            'related_clause': msg.related_clause_id,
            'created_at': msg.created_at.isoformat()
        } for msg in messages]

        # Get active suggestions
        suggestions = session.suggestions.filter(status='PENDING')
        suggestions_data = [{
            'id': sug.id,
            'clause_id': sug.clause_id,
            'clause_name': sug.clause.clause_name,
            'suggestion_type': sug.suggestion_type,
            'original_text': sug.original_text[:200] + '...' if len(sug.original_text) > 200 else sug.original_text,
            'suggested_text': sug.suggested_text[:200] + '...' if len(sug.suggested_text) > 200 else sug.suggested_text,
            'risk_impact': sug.risk_impact,
            'rationale': sug.rationale,
            'created_at': sug.created_at.isoformat()
        } for sug in suggestions]

        return Response({
            'success': True,
            'session': {
                'id': session.id,
                'session_name': session.session_name,
                'status': session.status,
                'contract': {
                    'id': session.contract.id,
                    'filename': session.contract.original_filename,
                },
                'our_party_role': session.our_party_role,
                'counterparty_name': session.counterparty_name,
                'objectives': session.objectives,
                'risk_tolerance': session.risk_tolerance,
                'started_at': session.started_at.isoformat(),
                'last_activity_at': session.last_activity_at.isoformat()
            },
            'messages': messages_data,
            'suggestions': suggestions_data
        })

    def put(self, request, session_id):
        """Update session status or details"""
        session = get_object_or_404(NegotiationSession, id=session_id)

        if 'status' in request.data:
            session.status = request.data['status']
            if request.data['status'] == 'COMPLETED':
                session.completed_at = datetime.now()

        if 'objectives' in request.data:
            session.objectives = request.data['objectives']

        if 'risk_tolerance' in request.data:
            session.risk_tolerance = request.data['risk_tolerance']

        session.save()

        return Response({
            'success': True,
            'session': {
                'id': session.id,
                'status': session.status
            }
        })


class NegotiationMessageView(APIView):
    """
    POST: Send a message in a negotiation session
    """
    permission_classes = [AllowAny]

    def post(self, request, session_id):
        """Send a message and get AI response"""
        session = get_object_or_404(NegotiationSession, id=session_id)

        message_content = request.data.get('content', '').strip()
        clause_id = request.data.get('clause_id')  # Optional clause reference

        if not message_content:
            return Response({
                'success': False,
                'error': 'Message content is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get user (in production, use authenticated user)
        user = User.objects.first()

        # Get clause if specified
        related_clause = None
        if clause_id:
            related_clause = Clause.objects.filter(id=clause_id).first()

        # Create user message
        user_message = NegotiationMessage.objects.create(
            session=session,
            sender=user,
            message_type='USER',
            content=message_content,
            related_clause=related_clause
        )

        # Generate AI response
        ai_response = self._generate_ai_response(session, message_content, related_clause)

        # Create AI message
        ai_message = NegotiationMessage.objects.create(
            session=session,
            sender=None,
            message_type='AI',
            content=ai_response['content'],
            ai_confidence=ai_response['confidence'],
            reasoning=ai_response.get('reasoning'),
            related_clause=related_clause
        )

        return Response({
            'success': True,
            'user_message': {
                'id': user_message.id,
                'content': user_message.content,
                'created_at': user_message.created_at.isoformat()
            },
            'ai_message': {
                'id': ai_message.id,
                'content': ai_message.content,
                'ai_confidence': ai_message.ai_confidence,
                'created_at': ai_message.created_at.isoformat()
            }
        }, status=status.HTTP_201_CREATED)

    def _generate_ai_response(self, session, user_message, clause=None):
        """Generate AI co-pilot response based on user message"""
        message_lower = user_message.lower()

        # If clause is explicitly provided
        if clause:
            return self._generate_clause_specific_response(clause, message_lower)

        # Try to detect if user is asking about a specific clause
        detected_clause = self._detect_clause_mention(session, user_message)
        if detected_clause:
            return self._generate_clause_specific_response(detected_clause, message_lower)

        # Check for specific question types
        if 'high risk' in message_lower or 'highest risk' in message_lower or 'risky' in message_lower:
            return self._generate_high_risk_analysis(session)

        if 'start' in message_lower or 'begin' in message_lower:
            return self._generate_start_response(session)

        if 'help' in message_lower or 'what can you' in message_lower:
            return self._generate_help_response()

        if 'summary' in message_lower or 'overview' in message_lower:
            return self._generate_contract_summary(session)

        if 'suggest' in message_lower or 'recommend' in message_lower:
            return self._generate_general_suggestions(session)

        # Greeting responses
        if any(word in message_lower for word in ['hi', 'hello', 'hey', 'greetings']):
            return {
                'content': f"Hello! I'm ready to help you negotiate {session.contract.original_filename}. "
                          f"I've analyzed the contract and identified key areas for discussion. What would you like to focus on?",
                'confidence': 0.95
            }

        # If we still don't have a match, provide a helpful generic response
        return self._generate_contextual_fallback(session, user_message)

    def _detect_clause_mention(self, session, message):
        """Detect if user is asking about a specific clause"""
        message_lower = message.lower()

        # Common clause keywords
        clause_keywords = [
            'liability', 'indemnity', 'indemnification', 'termination', 'payment',
            'confidentiality', 'intellectual property', 'ip', 'warranty', 'warranties',
            'limitation', 'damages', 'force majeure', 'dispute', 'arbitration',
            'governing law', 'assignment', 'renewal', 'notice', 'insurance'
        ]

        # Search for clauses by keyword
        for keyword in clause_keywords:
            if keyword in message_lower:
                # Try to find a clause with this keyword in its name
                clause = session.contract.clauses.filter(
                    Q(clause_name__icontains=keyword) | Q(clause_type__icontains=keyword)
                ).first()
                if clause:
                    return clause

        return None

    def _generate_clause_specific_response(self, clause, message_lower):
        """Generate response specific to a clause"""
        risk_score = clause.risk_score or 0.5
        risk_level = 'high' if risk_score > 0.7 else 'moderate' if risk_score > 0.4 else 'low'

        # Extract a preview of the clause text
        text_preview = (clause.extracted_text[:200] + '...') if clause.extracted_text and len(clause.extracted_text) > 200 else (clause.extracted_text or 'No text available')

        if 'risk' in message_lower:
            return {
                'content': f"**{clause.clause_name}** - Risk Analysis:\n\n"
                          f"Risk Score: {risk_score:.1%} ({risk_level} risk)\n\n"
                          f"This clause {'requires careful attention' if risk_score > 0.7 else 'should be reviewed' if risk_score > 0.4 else 'appears relatively standard'}. "
                          f"{'I strongly recommend negotiating better terms.' if risk_score > 0.7 else 'Consider if this aligns with your risk tolerance.' if risk_score > 0.4 else 'This clause seems acceptable.'}\n\n"
                          f"Would you like me to suggest alternative language?",
                'confidence': 0.9,
                'reasoning': f'Risk analysis for {clause.clause_name}'
            }
        elif 'suggest' in message_lower or 'alternative' in message_lower or 'improve' in message_lower:
            return {
                'content': f"For the **{clause.clause_name}**, here are my recommendations:\n\n"
                          f"Current Risk: {risk_score:.1%}\n\n"
                          f"Suggested improvements:\n"
                          f"1. Add specific caps or limitations\n"
                          f"2. Include clearer definitions\n"
                          f"3. Add protective language for your interests\n\n"
                          f"I can generate specific alternative language based on best practices. Would you like me to proceed?",
                'confidence': 0.85,
                'reasoning': 'Generating improvement suggestions'
            }
        else:
            return {
                'content': f"**{clause.clause_name}**\n\n"
                          f"Risk Level: {risk_score:.1%} ({risk_level})\n"
                          f"Type: {clause.clause_type or 'General'}\n\n"
                          f"Preview: {text_preview}\n\n"
                          f"This is a{'n important' if risk_score > 0.5 else ' standard'} clause in your contract. "
                          f"I can help you:\n"
                          f"- Analyze its risk implications\n"
                          f"- Suggest alternative language\n"
                          f"- Compare with industry standards\n\n"
                          f"What would you like to know?",
                'confidence': 0.85
            }

    def _generate_high_risk_analysis(self, session):
        """Generate analysis of high-risk clauses"""
        high_risk = session.contract.clauses.filter(risk_score__gte=0.7).order_by('-risk_score')[:5]

        if high_risk.count() == 0:
            return {
                'content': "Good news! I haven't identified any high-risk clauses in this contract. "
                          "However, I recommend reviewing all clauses to ensure they align with your objectives.",
                'confidence': 0.9
            }

        clause_list = '\n'.join([
            f"{i+1}. **{c.clause_name}** - Risk: {(c.risk_score or 0):.1%}"
            for i, c in enumerate(high_risk)
        ])

        return {
            'content': f"I've identified {high_risk.count()} high-risk clause(s) that need immediate attention:\n\n"
                      f"{clause_list}\n\n"
                      f"I recommend prioritizing these for negotiation. Would you like to discuss any specific clause?",
            'confidence': 0.95,
            'reasoning': 'High-risk clause analysis'
        }

    def _generate_start_response(self, session):
        """Generate response for starting a negotiation"""
        total_clauses = session.contract.clauses.count()
        high_risk = session.contract.clauses.filter(risk_score__gte=0.7).count()
        medium_risk = session.contract.clauses.filter(risk_score__gte=0.4, risk_score__lt=0.7).count()

        return {
            'content': f"Let's begin the negotiation for **{session.contract.original_filename}**!\n\n"
                      f"Contract Overview:\n"
                      f"- Total Clauses: {total_clauses}\n"
                      f"- High Risk: {high_risk}\n"
                      f"- Medium Risk: {medium_risk}\n\n"
                      f"I recommend starting with the {'high-risk clauses' if high_risk > 0 else 'most important terms'}. "
                      f"Which area would you like to focus on first?",
            'confidence': 0.95
        }

    def _generate_help_response(self):
        """Generate help response"""
        return {
            'content': "I'm your AI negotiation co-pilot! Here's how I can assist:\n\n"
                      "**Clause Analysis:**\n"
                      "- Identify high-risk clauses\n"
                      "- Explain clause implications\n"
                      "- Compare with industry standards\n\n"
                      "**Strategic Guidance:**\n"
                      "- Suggest alternative language\n"
                      "- Recommend negotiation priorities\n"
                      "- Analyze risk vs. benefit trade-offs\n\n"
                      "**Questions I can answer:**\n"
                      "- 'What are the high-risk clauses?'\n"
                      "- 'Tell me about the liability clause'\n"
                      "- 'Suggest improvements for [clause name]'\n"
                      "- 'Give me a contract summary'\n\n"
                      "What would you like to explore?",
            'confidence': 0.95
        }

    def _generate_contract_summary(self, session):
        """Generate contract summary"""
        clauses = session.contract.clauses.all()
        avg_risk = clauses.aggregate(Avg('risk_score'))['risk_score__avg'] or 0.5

        clause_types = {}
        for clause in clauses:
            ctype = clause.clause_type or 'Other'
            clause_types[ctype] = clause_types.get(ctype, 0) + 1

        top_types = sorted(clause_types.items(), key=lambda x: x[1], reverse=True)[:3]
        types_str = ', '.join([f"{t[0]} ({t[1]})" for t in top_types])

        return {
            'content': f"**Contract Summary: {session.contract.original_filename}**\n\n"
                      f"Total Clauses: {clauses.count()}\n"
                      f"Average Risk Score: {avg_risk:.1%}\n"
                      f"Top Clause Types: {types_str}\n\n"
                      f"Key Areas:\n"
                      f"- High Risk: {clauses.filter(risk_score__gte=0.7).count()} clauses\n"
                      f"- Medium Risk: {clauses.filter(risk_score__gte=0.4, risk_score__lt=0.7).count()} clauses\n"
                      f"- Low Risk: {clauses.filter(risk_score__lt=0.4).count()} clauses\n\n"
                      f"Would you like to dive deeper into any specific area?",
            'confidence': 0.9
        }

    def _generate_general_suggestions(self, session):
        """Generate general suggestions"""
        high_risk = session.contract.clauses.filter(risk_score__gte=0.7).order_by('-risk_score').first()

        if high_risk:
            return {
                'content': f"Based on my analysis, I recommend prioritizing the **{high_risk.clause_name}** "
                          f"(Risk: {(high_risk.risk_score or 0):.1%}).\n\n"
                          f"This clause should be your top negotiation priority. "
                          f"Would you like specific suggestions for improving it?",
                'confidence': 0.85
            }
        else:
            return {
                'content': "The contract appears relatively balanced. I suggest:\n\n"
                          "1. Review payment and termination clauses carefully\n"
                          "2. Ensure liability caps are appropriate\n"
                          "3. Verify intellectual property protections\n\n"
                          "Which area would you like to explore?",
                'confidence': 0.8
            }

    def _generate_contextual_fallback(self, session, user_message):
        """Generate contextual fallback when we don't understand the question"""
        # Extract any keywords from the message
        words = user_message.lower().split()
        interesting_words = [w for w in words if len(w) > 4]

        if len(interesting_words) > 0:
            return {
                'content': f"I want to make sure I understand your question correctly. Are you asking about:\n\n"
                          f"1. A specific clause in the contract?\n"
                          f"2. Risk analysis?\n"
                          f"3. Negotiation strategy?\n"
                          f"4. Something else?\n\n"
                          f"You can also try:\n"
                          f"- 'What are the high-risk clauses?'\n"
                          f"- 'Tell me about the [clause name]'\n"
                          f"- 'Give me a contract summary'",
                'confidence': 0.7
            }
        else:
            return {
                'content': "I'm here to help with your negotiation! You can ask me:\n\n"
                          f"- About specific clauses (e.g., 'liability clause')\n"
                          f"- For risk analysis (e.g., 'high-risk clauses')\n"
                          f"- For suggestions (e.g., 'suggest improvements')\n"
                          f"- For an overview (e.g., 'contract summary')\n\n"
                          f"What would you like to know about **{session.contract.original_filename}**?",
                'confidence': 0.75
            }


class NegotiationClauseListView(APIView):
    """
    GET: List all clauses in the contract with negotiation metadata
    """
    permission_classes = [AllowAny]

    def get(self, request, session_id):
        """Get all clauses for negotiation session with metadata"""
        session = get_object_or_404(NegotiationSession, id=session_id)

        clauses = session.contract.clauses.all()

        clauses_data = []
        for clause in clauses:
            # Count suggestions
            suggestion_count = NegotiationClauseSuggestion.objects.filter(
                session=session,
                clause=clause
            ).count()

            # Get latest position
            latest_position = NegotiationPosition.objects.filter(
                session=session,
                clause=clause
            ).order_by('-iteration').first()

            clauses_data.append({
                'id': clause.id,
                'clause_name': clause.clause_name,
                'clause_type': clause.clause_type,
                'extracted_text': clause.extracted_text[:300] + '...' if clause.extracted_text and len(clause.extracted_text) > 300 else clause.extracted_text,
                'risk_score': clause.risk_score,
                'risk_level': clause.risk_level,
                'suggestion_count': suggestion_count,
                'position_status': latest_position.position_status if latest_position else None,
                'iteration': latest_position.iteration if latest_position else 0
            })

        # Sort by risk score descending
        clauses_data.sort(key=lambda x: x['risk_score'] or 0, reverse=True)

        return Response({
            'success': True,
            'clauses': clauses_data,
            'total': len(clauses_data),
            'high_risk_count': len([c for c in clauses_data if (c['risk_score'] or 0) >= 0.7]),
            'medium_risk_count': len([c for c in clauses_data if 0.4 <= (c['risk_score'] or 0) < 0.7]),
            'low_risk_count': len([c for c in clauses_data if (c['risk_score'] or 0) < 0.4])
        })
