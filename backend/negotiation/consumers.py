"""
WebSocket Consumer for Live Clause Co-Pilot
Real-time negotiation assistance with streaming AI
"""
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class NegotiationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs'].get('session_id')
        self.room_group_name = f'negotiation_{self.session_id}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        await self.send(text_data=json.dumps({
            'type': 'connection',
            'message': 'Connected to Live Co-Pilot',
            'session_id': self.session_id
        }))
        
        logger.info(f"WebSocket connected: session={self.session_id}")
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"WebSocket disconnected: session={self.session_id}, code={close_code}")
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_text = data.get('text', '').strip()
            clause_id = data.get('clause_id')
            
            if not message_text:
                return
            
            logger.info(f"Received message: session={self.session_id}")
            
            await self.send(text_data=json.dumps({
                'type': 'ack',
                'message': 'Processing...'
            }))
            
            await self.handle_chat_message(message_text, clause_id)
        
        except Exception as e:
            logger.error(f"Error in receive: {e}", exc_info=True)
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def handle_chat_message(self, message_text, clause_id=None):
        # Step 1: Classify intent
        intent = await self.classify_intent_async(message_text)

        # Step 2: Fetch similar clauses via RAG
        similar_clauses = await self.fetch_similar_clauses_async(message_text)

        # Step 3: Predict counter-ask
        prediction = await self.predict_counter_ask_async(intent, clause_id)

        # Step 4: Generate AI response
        ai_response = await self.generate_ai_response(message_text, clause_id, intent, similar_clauses)

        # Step 5: Save messages
        user_msg = await self.save_user_message(message_text, clause_id)
        ai_msg = await self.save_ai_message(
            ai_response['content'],
            ai_response['confidence'],
            clause_id
        )

        # Step 6: Send comprehensive response
        await self.send(text_data=json.dumps({
            'type': 'chat_response',
            'user_message': {
                'id': str(user_msg.id),
                'content': message_text,
                'timestamp': user_msg.created_at.isoformat()
            },
            'ai_message': {
                'id': str(ai_msg.id),
                'content': ai_response['content'],
                'confidence': ai_response['confidence'],
                'timestamp': ai_msg.created_at.isoformat()
            },
            'intent': intent,
            'prediction': prediction,
            'similar_clauses': [
                {
                    'id': str(c['id']),
                    'name': c['name'],
                    'score': c['score'],
                    'text_preview': c['text'][:100] + '...' if len(c['text']) > 100 else c['text']
                }
                for c in similar_clauses[:3]
            ]
        }))
    
    @database_sync_to_async
    def classify_intent_async(self, text):
        """Classify negotiation intent"""
        from negotiation.intent import classify_intent
        return classify_intent(text)

    @database_sync_to_async
    def fetch_similar_clauses_async(self, query):
        """Fetch similar clauses using RAG"""
        from negotiation.rag import get_rag
        rag = get_rag()
        return rag.fetch_similar_clauses(query, top_k=5)

    @database_sync_to_async
    def predict_counter_ask_async(self, intent, clause_id):
        """Predict next counter-ask"""
        COUNTER_MAP = {
            'LIABILITY_PUSH': 'They will likely ask for uncapped liability or broader indemnification',
            'PRICE_PUSH': 'They may request volume discounts or longer payment terms',
            'PAYMENT_DELAY': 'They will seek net-60 or net-90 payment terms',
            'INDEMNITY_EXPANSION': 'They may demand third-party indemnity coverage',
            'TERMINATION_FLEX': 'They will seek termination for convenience or shorter notice periods',
            'GOVERNING_LAW': 'They may push for their home jurisdiction'
        }

        if intent == 'GENERAL':
            return None

        return {
            'prediction': COUNTER_MAP.get(intent, 'Neutral negotiation continuation'),
            'intent': intent
        }

    async def generate_ai_response(self, message, clause_id, intent=None, similar_clauses=None):
        message_lower = message.lower()

        # High risk query
        if 'high risk' in message_lower or 'show me all' in message_lower:
            content = await self.generate_high_risk_response()

        # Liability negotiation
        elif intent == 'LIABILITY_PUSH':
            if 'cap' in message_lower or '$' in message:
                content = "A $1M liability cap is reasonable for this type of contract. I recommend:\n\n" \
                         "✓ Cap at 12 months of fees or $1M, whichever is greater\n" \
                         "✓ Exclude intentional misconduct and IP infringement\n" \
                         "✓ Require mutual liability caps\n\n" \
                         f"I found {len(similar_clauses or [])} similar liability clauses for reference."
            else:
                content = "⚠️ Unlimited liability is high risk. Counter-strategy:\n\n" \
                         "1. Propose mutual liability cap at 12 months of contract value\n" \
                         "2. Exclude gross negligence, willful misconduct, IP claims\n" \
                         "3. Require adequate insurance coverage\n\n" \
                         "Would you like me to draft counter-language?"

        # Termination negotiation
        elif intent == 'TERMINATION_FLEX':
            if '30' in message or '60' in message or '90' in message:
                content = "30-day termination for convenience is favorable for the other party. Counter-proposal:\n\n" \
                         "✓ Require 90-day notice period\n" \
                         "✓ Add termination fee (e.g., 3 months of fees)\n" \
                         "✓ Ensure payment for work in progress\n" \
                         "✓ Include IP ownership upon termination\n\n" \
                         f"I found {len(similar_clauses or [])} termination clauses to review."
            else:
                content = "Termination clauses require careful negotiation. Key protections:\n\n" \
                         "• Require cause-based termination only\n" \
                         "• If convenience allowed, demand 90+ day notice\n" \
                         "• Include termination assistance obligations\n\n" \
                         "What specific terms are they requesting?"

        # Payment terms
        elif intent == 'PAYMENT_DELAY' or intent == 'PRICE_PUSH':
            content = "Payment term negotiation strategy:\n\n" \
                     "✓ Standard: Net-30 with 2% early payment discount\n" \
                     "✓ If Net-60 required: Add late payment interest (1.5%/month)\n" \
                     "✓ Require partial upfront payment (25-30%)\n" \
                     "✓ Link payments to milestones, not calendar dates\n\n" \
                     "What payment terms are they proposing?"

        # Indemnity
        elif intent == 'INDEMNITY_EXPANSION':
            content = "Indemnification expansion requires careful limits:\n\n" \
                     "✓ Accept indemnity for your IP infringement\n" \
                     "✓ Resist third-party indemnity (too broad)\n" \
                     "✓ Require mutual indemnification\n" \
                     "✓ Exclude consequential damages\n\n" \
                     f"Similar clauses found: {len(similar_clauses or [])}"

        # Governing law
        elif intent == 'GOVERNING_LAW':
            content = "Governing law negotiation tips:\n\n" \
                     "• Neutral jurisdiction (e.g., Delaware, New York)\n" \
                     "• Avoid their home jurisdiction if unfavorable\n" \
                     "• Consider arbitration as alternative\n\n" \
                     "Which jurisdiction are they requesting?"

        # General/Unknown
        else:
            content = "I'm ready to assist with your negotiation. I can help with:\n\n" \
                     "• Risk analysis and clause review\n" \
                     "• Counter-proposal drafting\n" \
                     "• Precedent clause suggestions\n" \
                     "• Negotiation strategy\n\n" \
                     "What specific clause or term would you like to discuss?"

        return {
            'content': content,
            'confidence': 0.92
        }
    
    async def generate_high_risk_response(self):
        clauses = await self.get_session_clauses()
        high_risk = [c for c in clauses if (c.risk_score or 0) >= 0.7]
        
        if high_risk:
            names = ', '.join([c.clause_name for c in high_risk[:3]])
            return f"I've identified {len(high_risk)} high-risk clauses: {names}. Which would you like to review first?"
        else:
            return "Good news! No high-risk clauses detected in this contract."
    
    @database_sync_to_async
    def get_session_clauses(self):
        from core.models import NegotiationSession
        session = NegotiationSession.objects.get(id=self.session_id)
        return list(session.contract.clauses.all())
    
    @database_sync_to_async
    def save_user_message(self, content, clause_id=None):
        from core.models import NegotiationMessage, NegotiationSession, Clause, User
        session = NegotiationSession.objects.get(id=self.session_id)
        user = User.objects.first()
        
        clause = None
        if clause_id:
            try:
                clause = Clause.objects.get(id=clause_id)
            except Clause.DoesNotExist:
                pass
        
        return NegotiationMessage.objects.create(
            session=session,
            sender=user,
            message_type='USER',
            content=content,
            related_clause=clause
        )
    
    @database_sync_to_async
    def save_ai_message(self, content, confidence, clause_id=None):
        from core.models import NegotiationMessage, NegotiationSession, Clause
        session = NegotiationSession.objects.get(id=self.session_id)
        
        clause = None
        if clause_id:
            try:
                clause = Clause.objects.get(id=clause_id)
            except Clause.DoesNotExist:
                pass
        
        return NegotiationMessage.objects.create(
            session=session,
            sender=None,
            message_type='AI',
            content=content,
            ai_confidence=confidence,
            related_clause=clause
        )
