"""
Embedding-Based Chat Service
Pure semantic retrieval without LLM generation (no hallucinations)
Returns relevant clauses ranked by similarity
"""

from typing import List, Dict, Optional
from core.models import Contract, Clause, ClauseEmbedding
from api.embedding_service import embedding_service
from api.embedding_risk_scorer import embedding_risk_scorer
import logging

logger = logging.getLogger(__name__)


class EmbeddingChatService:
    """
    Contract Q&A using pure semantic retrieval.
    No text generation - only returns relevant clauses with context.
    """

    def __init__(self):
        self.embedding_service = embedding_service

    def query_contract(
        self,
        contract: Contract,
        query: str,
        top_k: int = 3,
        min_similarity: float = 0.6
    ) -> Dict:
        """
        Answer a question about a contract by retrieving relevant clauses.

        Args:
            contract: Contract object to query
            query: User's natural language question
            top_k: Number of top results to return
            min_similarity: Minimum similarity threshold

        Returns:
            Dict with answer and supporting clauses
        """
        # Embed the query
        query_embedding = self.embedding_service.embed_text(query)

        # Get all clauses with embeddings
        clauses = contract.clauses.all()

        if not clauses:
            return {
                'query': query,
                'answer': 'No clauses found in this contract.',
                'supporting_clauses': [],
                'confidence': 0.0
            }

        # Rank clauses by similarity
        ranked_clauses = self._rank_clauses_by_similarity(
            query_embedding=query_embedding,
            clauses=clauses,
            top_k=top_k,
            min_similarity=min_similarity
        )

        if not ranked_clauses:
            return {
                'query': query,
                'answer': 'No relevant clauses found for this question.',
                'supporting_clauses': [],
                'confidence': 0.0
            }

        # Build structured answer
        answer = self._build_answer(query, ranked_clauses)

        return {
            'query': query,
            'answer': answer,
            'supporting_clauses': ranked_clauses,
            'confidence': ranked_clauses[0]['similarity'] if ranked_clauses else 0.0,
            'num_results': len(ranked_clauses)
        }

    def query_multiple_contracts(
        self,
        contracts: List[Contract],
        query: str,
        top_k: int = 5,
        min_similarity: float = 0.6
    ) -> Dict:
        """
        Answer a question across multiple contracts.

        Args:
            contracts: List of Contract objects to query
            query: User's natural language question
            top_k: Number of top results to return
            min_similarity: Minimum similarity threshold

        Returns:
            Dict with answer and supporting clauses from all contracts
        """
        query_embedding = self.embedding_service.embed_text(query)

        all_ranked_clauses = []

        for contract in contracts:
            clauses = contract.clauses.all()

            if not clauses:
                continue

            ranked_clauses = self._rank_clauses_by_similarity(
                query_embedding=query_embedding,
                clauses=clauses,
                top_k=top_k,
                min_similarity=min_similarity
            )

            # Add contract info to each clause
            for clause_result in ranked_clauses:
                clause_result['contract_id'] = contract.id
                clause_result['contract_name'] = contract.original_filename

            all_ranked_clauses.extend(ranked_clauses)

        # Re-sort by similarity across all contracts
        all_ranked_clauses.sort(key=lambda x: x['similarity'], reverse=True)

        # Take top K overall
        all_ranked_clauses = all_ranked_clauses[:top_k]

        if not all_ranked_clauses:
            return {
                'query': query,
                'answer': 'No relevant clauses found across the contracts.',
                'supporting_clauses': [],
                'confidence': 0.0,
                'contracts_searched': len(contracts)
            }

        # Build answer
        answer = self._build_answer(query, all_ranked_clauses)

        return {
            'query': query,
            'answer': answer,
            'supporting_clauses': all_ranked_clauses,
            'confidence': all_ranked_clauses[0]['similarity'] if all_ranked_clauses else 0.0,
            'num_results': len(all_ranked_clauses),
            'contracts_searched': len(contracts)
        }

    def suggest_questions(self, contract: Contract) -> List[str]:
        """
        Suggest common questions users can ask about this contract.

        Args:
            contract: Contract object

        Returns:
            List of suggested question strings
        """
        # Analyze contract type to suggest relevant questions
        contract_type = contract.contract_type or 'Contract'

        base_questions = [
            "Where is liability capped?",
            "Can the contract be terminated for convenience?",
            "Who owns intellectual property created under this agreement?",
            "What are the payment terms?",
            "What is the governing law and jurisdiction?",
            "Are there any confidentiality obligations?",
            "What are the warranty terms?",
            "What is the contract duration?",
            "Are there any automatic renewal clauses?",
            "What dispute resolution mechanisms are included?"
        ]

        # Type-specific questions
        type_specific = {
            'NDA': [
                "What information is considered confidential?",
                "How long do confidentiality obligations last?",
                "What are the exceptions to confidentiality?"
            ],
            'SLA': [
                "What are the uptime guarantees?",
                "What are the service credits for downtime?",
                "What are the support response times?"
            ],
            'MSA': [
                "What is the scope of services?",
                "What are the pricing terms?",
                "What are the termination provisions?"
            ]
        }

        # Add type-specific questions if available
        for key in type_specific:
            if key.lower() in contract_type.lower():
                base_questions.extend(type_specific[key])
                break

        return base_questions[:10]

    def _rank_clauses_by_similarity(
        self,
        query_embedding: List[float],
        clauses: List[Clause],
        top_k: int,
        min_similarity: float
    ) -> List[Dict]:
        """Rank clauses by similarity to query"""
        ranked = []

        for clause in clauses:
            # Get clause embedding
            clause_emb = self._get_clause_embedding(clause)

            if not clause_emb:
                continue

            # Compute similarity
            similarity = self.embedding_service.cosine_similarity(query_embedding, clause_emb)

            if similarity >= min_similarity:
                # Compute actual risk score for this clause
                risk_result = embedding_risk_scorer.score_clause(clause)
                risk_level = risk_result.get('risk_level', 'UNKNOWN') if risk_result else 'UNKNOWN'
                risk_score = risk_result.get('risk_score', 0) if risk_result else 0

                ranked.append({
                    'clause_id': clause.id,
                    'clause_name': clause.clause_name,
                    'clause_text': clause.extracted_text or clause.clause_name,
                    'similarity': round(similarity, 3),
                    'risk_level': risk_level,
                    'risk_score': risk_score
                })

        # Sort by similarity descending
        ranked.sort(key=lambda x: x['similarity'], reverse=True)

        return ranked[:top_k]

    def _get_clause_embedding(self, clause: Clause) -> Optional[List[float]]:
        """Get or generate embedding for a clause"""
        try:
            clause_emb = ClauseEmbedding.objects.filter(clause_id=str(clause.id)).first()

            if clause_emb and clause_emb.embedding:
                return clause_emb.embedding

            # Generate new embedding
            text_to_embed = clause.extracted_text or clause.clause_name

            if not text_to_embed or not text_to_embed.strip():
                return None

            embedding = self.embedding_service.embed_text(text_to_embed)
            text_hash = self.embedding_service.compute_text_hash(text_to_embed)

            ClauseEmbedding.objects.update_or_create(
                clause_id=str(clause.id),
                defaults={
                    'embedding': embedding,
                    'embedded_text_hash': text_hash,
                    'embedding_model': 'all-MiniLM-L6-v2'
                }
            )

            return embedding

        except Exception as e:
            logger.error(f"Error getting clause embedding: {e}")
            return None

    def _build_answer(self, query: str, ranked_clauses: List[Dict]) -> str:
        """Build structured answer from top clauses"""
        if not ranked_clauses:
            return "No relevant information found."

        top_clause = ranked_clauses[0]

        # Build a comprehensive natural language answer
        answer_parts = []

        # Introduction based on confidence
        if top_clause['similarity'] > 0.75:
            intro = f"Based on the contract analysis, I found highly relevant information in the {top_clause['clause_name']} clause."
        elif top_clause['similarity'] > 0.6:
            intro = f"The most relevant information regarding your question is found in the {top_clause['clause_name']} clause."
        else:
            intro = f"I found potentially relevant information in the {top_clause['clause_name']} clause, though the match is moderate."

        answer_parts.append(intro)

        # Add risk context if available
        if top_clause.get('risk_level') and top_clause['risk_level'] != 'UNKNOWN':
            risk_context = self._get_risk_context(top_clause['risk_level'], top_clause.get('risk_score', 0))
            if risk_context:
                answer_parts.append(risk_context)

        # Add summary of the clause content
        clause_text = top_clause['clause_text']
        if len(clause_text) > 300:
            summary = f"\n\nKey Points:\n{self._summarize_clause_text(clause_text)}"
        else:
            summary = f"\n\nThe clause states: {clause_text}"

        answer_parts.append(summary)

        # Add context about additional clauses if available
        if len(ranked_clauses) > 1:
            additional_info = f"\n\nAdditionally, {len(ranked_clauses) - 1} other clause(s) also relate to your question:"
            for clause in ranked_clauses[1:]:
                additional_info += f"\n• {clause['clause_name']} ({int(clause['similarity']*100)}% relevant"
                if clause.get('risk_level') and clause['risk_level'] != 'UNKNOWN':
                    additional_info += f", {clause['risk_level']} risk"
                additional_info += ")"
            answer_parts.append(additional_info)

        return '\n'.join(answer_parts)

    def _get_risk_context(self, risk_level: str, risk_score: int) -> str:
        """Generate contextual risk information"""
        if risk_level == 'HIGH':
            return f"⚠️ This clause has been flagged as HIGH RISK (score: {risk_score}/100) and may require careful review or negotiation."
        elif risk_level == 'MEDIUM':
            return f"⚡ This clause has MEDIUM RISK (score: {risk_score}/100) and should be reviewed for potential concerns."
        elif risk_level == 'LOW':
            return f"✓ This clause is assessed as LOW RISK (score: {risk_score}/100) and appears to be standard."
        return ""

    def _summarize_clause_text(self, text: str) -> str:
        """Create a concise summary of clause text"""
        # Split into sentences (basic approach)
        sentences = [s.strip() for s in text.replace('\n', ' ').split('.') if s.strip()]

        if len(sentences) <= 3:
            return text[:500] + ('...' if len(text) > 500 else '')

        # Return first 2-3 key sentences
        key_sentences = sentences[:3]
        summary = '. '.join(key_sentences) + '.'

        if len(summary) > 500:
            summary = summary[:500] + '...'

        return summary


# Global instance
embedding_chat_service = EmbeddingChatService()
