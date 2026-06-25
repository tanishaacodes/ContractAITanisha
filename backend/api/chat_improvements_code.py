
# =======================
# AI CHAT IMPROVEMENTS
# Features: Conversation History, Caching, Page Numbers, Streaming
# =======================

import hashlib
import uuid
from django.db import connection
from django.http import StreamingHttpResponse
import PyPDF2
import io

# ============ HELPER FUNCTIONS ============

def get_db_connection():
    """Get raw database connection for direct SQL queries"""
    return connection

def create_conversation(user_id):
    """Create a new conversation"""
    conversation_id = str(uuid.uuid4())
    with get_db_connection().cursor() as cursor:
        cursor.execute("""
            INSERT INTO chat_conversations (id, userId, title, lastMessageAt, createdAt, updatedAt)
            VALUES (%s, %s, %s, NOW(), NOW(), NOW())
        """, [conversation_id, user_id, 'New Conversation'])
    return conversation_id

def save_message(conversation_id, role, content, sources=None, page_numbers=None, contract_ids=None):
    """Save a chat message"""
    message_id = str(uuid.uuid4())
    with get_db_connection().cursor() as cursor:
        cursor.execute("""
            INSERT INTO chat_messages
            (id, conversationId, role, content, sources, pageNumbers, contractIds, createdAt)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        """, [
            message_id, conversation_id, role, content,
            json.dumps(sources) if sources else None,
            json.dumps(page_numbers) if page_numbers else None,
            json.dumps(contract_ids) if contract_ids else None
        ])

        # Update conversation's lastMessageAt
        cursor.execute("""
            UPDATE chat_conversations
            SET lastMessageAt = NOW(), updatedAt = NOW()
            WHERE id = %s
        """, [conversation_id])

    return message_id

def get_conversation_history(conversation_id, limit=10):
    """Get recent messages from a conversation"""
    with get_db_connection().cursor() as cursor:
        cursor.execute("""
            SELECT role, content, sources, pageNumbers, contractIds, createdAt
            FROM chat_messages
            WHERE conversationId = %s
            ORDER BY createdAt DESC
            LIMIT %s
        """, [conversation_id, limit])

        columns = [col[0] for col in cursor.description]
        messages = []
        for row in cursor.fetchall():
            msg = dict(zip(columns, row))
            # Parse JSON fields
            if msg['sources']:
                msg['sources'] = json.loads(msg['sources']) if isinstance(msg['sources'], str) else msg['sources']
            if msg['pageNumbers']:
                msg['pageNumbers'] = json.loads(msg['pageNumbers']) if isinstance(msg['pageNumbers'], str) else msg['pageNumbers']
            if msg['contractIds']:
                msg['contractIds'] = json.loads(msg['contractIds']) if isinstance(msg['contractIds'], str) else msg['contractIds']
            messages.append(msg)

        return list(reversed(messages))  # Return in chronological order

def generate_cache_key(query, contract_ids=None):
    """Generate cache key for a query"""
    cache_string = query.lower().strip()
    if contract_ids:
        cache_string += '|' + '|'.join(sorted(contract_ids))
    return hashlib.sha256(cache_string.encode()).hexdigest()

def get_cached_response(query_hash):
    """Get cached response if exists and not expired"""
    with get_db_connection().cursor() as cursor:
        cursor.execute("""
            SELECT response, sources, pageNumbers, contractIds
            FROM chat_cache
            WHERE queryHash = %s AND (expiresAt IS NULL OR expiresAt > NOW())
        """, [query_hash])

        row = cursor.fetchone()
        if row:
            # Update hit count and last accessed
            cursor.execute("""
                UPDATE chat_cache
                SET hitCount = hitCount + 1, lastAccessedAt = NOW()
                WHERE queryHash = %s
            """, [query_hash])

            return {
                'response': row[0],
                'sources': json.loads(row[1]) if row[1] else [],
                'pageNumbers': json.loads(row[2]) if row[2] else {},
                'contractIds': json.loads(row[3]) if row[3] else []
            }
    return None

def save_to_cache(query, query_hash, response, sources=None, page_numbers=None, contract_ids=None, ttl_hours=24):
    """Save response to cache"""
    cache_id = str(uuid.uuid4())
    with get_db_connection().cursor() as cursor:
        cursor.execute("""
            INSERT INTO chat_cache
            (id, queryHash, query, response, sources, pageNumbers, contractIds, createdAt, expiresAt, lastAccessedAt)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), DATE_ADD(NOW(), INTERVAL %s HOUR), NOW())
            ON DUPLICATE KEY UPDATE
                response = VALUES(response),
                sources = VALUES(sources),
                pageNumbers = VALUES(pageNumbers),
                contractIds = VALUES(contractIds),
                hitCount = hitCount + 1,
                lastAccessedAt = NOW()
        """, [
            cache_id, query_hash, query, response,
            json.dumps(sources) if sources else None,
            json.dumps(page_numbers) if page_numbers else None,
            json.dumps(contract_ids) if contract_ids else None,
            ttl_hours
        ])

def extract_page_numbers_from_pdf(file_path, search_text):
    """Extract page numbers where text appears in PDF"""
    page_numbers = []
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            search_text_lower = search_text.lower()[:200]  # First 200 chars

            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text().lower()

                if search_text_lower in page_text:
                    page_numbers.append(page_num + 1)  # 1-indexed

                if len(page_numbers) >= 3:  # Limit to first 3 pages
                    break
    except Exception as e:
        print(f"[PAGE EXTRACTION ERROR] {str(e)}")

    return page_numbers

def log_analytics(user_id, query, contract_id=None, response_time=None, was_cached=False):
    """Log analytics for chat queries"""
    analytics_id = str(uuid.uuid4())
    with get_db_connection().cursor() as cursor:
        cursor.execute("""
            INSERT INTO chat_analytics
            (id, userId, query, contractId, responseTime, wasCached, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """, [analytics_id, user_id, query, contract_id, response_time, 1 if was_cached else 0])

# ============ API ENDPOINTS ============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_conversations(request):
    """Get all conversations for the current user"""
    try:
        user_id = request.user.id

        with get_db_connection().cursor() as cursor:
            cursor.execute("""
                SELECT c.id, c.title, c.lastMessageAt, c.createdAt,
                       (SELECT COUNT(*) FROM chat_messages WHERE conversationId = c.id) as messageCount
                FROM chat_conversations c
                WHERE c.userId = %s
                ORDER BY c.lastMessageAt DESC
                LIMIT 50
            """, [user_id])

            columns = [col[0] for col in cursor.description]
            conversations = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return Response({
            'conversations': conversations
        })
    except Exception as e:
        print(f"[GET CONVERSATIONS ERROR] {str(e)}")
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_conversation_messages(request, conversation_id):
    """Get messages for a specific conversation"""
    try:
        user_id = request.user.id

        # Verify conversation belongs to user
        with get_db_connection().cursor() as cursor:
            cursor.execute("""
                SELECT id FROM chat_conversations
                WHERE id = %s AND userId = %s
            """, [conversation_id, user_id])

            if not cursor.fetchone():
                return Response({'error': 'Conversation not found'}, status=404)

        messages = get_conversation_history(conversation_id, limit=100)

        return Response({
            'conversation_id': conversation_id,
            'messages': messages
        })
    except Exception as e:
        print(f"[GET MESSAGES ERROR] {str(e)}")
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_suggested_questions(request):
    """Get suggested questions based on contract type"""
    try:
        contract_type = request.GET.get('contractType', 'General')

        with get_db_connection().cursor() as cursor:
            cursor.execute("""
                SELECT id, question, category, priority
                FROM suggested_questions
                WHERE contractType = %s AND isActive = 1
                ORDER BY priority DESC
                LIMIT 10
            """, [contract_type])

            columns = [col[0] for col in cursor.description]
            questions = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return Response({
            'questions': questions
        })
    except Exception as e:
        print(f"[GET SUGGESTED QUESTIONS ERROR] {str(e)}")
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chat_analytics(request):
    """Get chat analytics for the current user"""
    try:
        user_id = request.user.id
        days = int(request.GET.get('days', 7))

        with get_db_connection().cursor() as cursor:
            # Most asked questions
            cursor.execute("""
                SELECT query, COUNT(*) as count
                FROM chat_analytics
                WHERE userId = %s AND timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
                GROUP BY query
                ORDER BY count DESC
                LIMIT 10
            """, [user_id, days])

            top_questions = [{'query': row[0], 'count': row[1]} for row in cursor.fetchall()]

            # Most queried contracts
            cursor.execute("""
                SELECT c.original_filename, COUNT(*) as count
                FROM chat_analytics ca
                JOIN contracts c ON ca.contractId = c.id
                WHERE ca.userId = %s AND ca.timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
                GROUP BY c.id
                ORDER BY count DESC
                LIMIT 10
            """, [user_id, days])

            top_contracts = [{'filename': row[0], 'count': row[1]} for row in cursor.fetchall()]

            # Average response time
            cursor.execute("""
                SELECT AVG(responseTime) as avg_time,
                       SUM(CASE WHEN wasCached = 1 THEN 1 ELSE 0 END) as cached_count,
                       COUNT(*) as total_count
                FROM chat_analytics
                WHERE userId = %s AND timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
            """, [user_id, days])

            row = cursor.fetchone()
            stats = {
                'avg_response_time': round(row[0]) if row[0] else 0,
                'cached_responses': row[1],
                'total_queries': row[2],
                'cache_hit_rate': round((row[1] / row[2] * 100) if row[2] > 0 else 0, 1)
            }

        return Response({
            'top_questions': top_questions,
            'top_contracts': top_contracts,
            'stats': stats
        })
    except Exception as e:
        print(f"[GET ANALYTICS ERROR] {str(e)}")
        return Response({'error': str(e)}, status=500)
