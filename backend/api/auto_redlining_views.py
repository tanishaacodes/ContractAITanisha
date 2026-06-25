"""
Auto Contract Redlining Views
==============================
Automatically marks up clauses that deviate from standard templates.
Provides a diff viewer showing original vs suggested redlines.
Uses Qwen 2.5 via Ollama to generate suggested rewrites.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from core.models import Contract, Clause
import logging
import difflib
import re
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def _clean_clause_type_for_lookup(raw: str) -> str:
    """Strip LLM prefix garbage from clause_type for DB lookup."""
    if not raw:
        return ''
    for prefix in ('Contract Clause Category Name:', 'Category Name:', 'Clause Category:'):
        if raw.startswith(prefix):
            raw = raw[len(prefix):].strip()
    return raw.strip().rstrip('. ')


def _get_standard_clause_text(clause_type: str, exclude_contract_id=None) -> str:
    """
    Find the 'gold standard' clause text for a given type from OTHER contracts only.
    Uses exact cleaned clause_type match first, then falls back to keyword match.
    Never uses text from the same contract being redlined.
    """
    clean_type = _clean_clause_type_for_lookup(clause_type)
    if not clean_type:
        return ''

    base_qs = Clause.objects.exclude(extracted_text='').exclude(extracted_text__isnull=True)
    if exclude_contract_id:
        base_qs = base_qs.exclude(contract_id=exclude_contract_id)

    # 1. Exact match on cleaned type
    exact = base_qs.filter(clause_type=clause_type).order_by('-confidence').first()
    if exact:
        return exact.extracted_text

    # 2. Case-insensitive exact match on clean name
    ci_exact = base_qs.filter(clause_type__iexact=clean_type).order_by('-confidence').first()
    if ci_exact:
        return ci_exact.extracted_text

    # No standard found — return empty so rule-based fallback applies
    return ''


def _rule_based_redline(original: str, standard: str, clause_type: str) -> str:
    """
    Rule-based redline: apply clause-type-specific legal improvements.
    Makes substantive structural changes, not just word swaps.
    """
    text = original

    # 1. Strengthen weak obligation language
    text = re.sub(r'\bmay\b', 'shall', text, flags=re.IGNORECASE)
    text = re.sub(r'\breasonable efforts\b', 'best efforts', text, flags=re.IGNORECASE)
    text = re.sub(r'\bat its sole discretion\b', 'only with prior written consent of both parties', text, flags=re.IGNORECASE)
    text = re.sub(r'\bat its discretion\b', 'with prior written consent', text, flags=re.IGNORECASE)
    text = re.sub(r'\bshould\b', 'shall', text, flags=re.IGNORECASE)
    text = re.sub(r'\battempt to\b', 'shall', text, flags=re.IGNORECASE)

    ctype_lower = clause_type.lower() if clause_type else ''

    # 2. Clause-type specific protective additions
    if 'confidential' in ctype_lower:
        additions = [
            ' The Receiving Party shall implement reasonable security measures to protect Confidential Information.',
            ' Confidential Information shall not be disclosed to any third party without prior written consent.',
            ' All confidential obligations shall survive termination of this Agreement for a period of five (5) years.',
        ]
    elif 'indemnif' in ctype_lower or 'liability' in ctype_lower:
        additions = [
            ' Each party\'s total liability shall not exceed the total fees paid in the preceding twelve (12) months.',
            ' Neither party shall be liable for indirect, incidental, or consequential damages.',
            ' Indemnification obligations shall survive termination of this Agreement.',
        ]
    elif 'payment' in ctype_lower:
        additions = [
            ' All payments shall be made within thirty (30) days of invoice date.',
            ' Late payments shall incur interest at 1.5% per month on the outstanding balance.',
            ' Disputed invoices must be raised in writing within fifteen (15) days of receipt.',
        ]
    elif 'termination' in ctype_lower:
        additions = [
            ' Either party may terminate this Agreement with thirty (30) days written notice.',
            ' Upon termination, all outstanding payments shall become immediately due and payable.',
            ' Termination shall not affect any rights or obligations accrued prior to the termination date.',
        ]
    elif 'arbitration' in ctype_lower or 'dispute' in ctype_lower:
        additions = [
            ' All disputes shall be resolved by binding arbitration under ICC Rules.',
            ' The seat of arbitration shall be Singapore with proceedings in English.',
            ' The arbitral award shall be final and binding on both parties.',
        ]
    elif 'force majeure' in ctype_lower:
        additions = [
            ' Force majeure events shall be notified in writing within forty-eight (48) hours of occurrence.',
            ' If a force majeure event continues for more than sixty (60) days, either party may terminate.',
            ' The affected party shall use best efforts to mitigate the impact of the force majeure event.',
        ]
    elif 'intellectual property' in ctype_lower or 'ip' in ctype_lower:
        additions = [
            ' All intellectual property created under this Agreement shall remain the property of the creating party.',
            ' Neither party shall use the other\'s IP without prior written consent.',
            ' Any jointly developed IP shall be owned equally by both parties.',
        ]
    else:
        additions = [
            ' All obligations under this clause shall be performed in good faith.',
            ' Any amendments to this clause must be made in writing and signed by both parties.',
        ]

    # Append additions that aren't already in the text
    for addition in additions:
        if addition.strip().lower()[:30] not in text.lower():
            text = text.rstrip('. ') + addition

    return text


def _generate_redline_suggestion(original: str, standard: str, clause_type: str) -> str:
    """
    Use Qwen 2.5 to generate a redlined version of the clause.
    Falls back to rule-based suggestion on failure.
    """
    if not original:
        return standard[:800] if standard else ''

    if standard:
        prompt = (
            f"You are a contract lawyer. Rewrite this {clause_type} clause to reduce legal risk "
            f"and align with the standard reference below. Make meaningful changes.\n\n"
            f"Original clause:\n{original[:600]}\n\n"
            f"Standard reference:\n{standard[:400]}\n\n"
            f"Output ONLY the improved clause text with at least 2-3 specific legal improvements."
        )
    else:
        prompt = (
            f"You are a contract lawyer. Rewrite this {clause_type} clause to reduce legal risk. "
            f"Strengthen weak language, add protective provisions, and improve enforceability.\n\n"
            f"Original clause:\n{original[:700]}\n\n"
            f"Output ONLY the improved clause text. Make specific legal improvements such as:\n"
            f"- Replace 'may' with 'shall' where obligations exist\n"
            f"- Add liability caps and indemnification limits\n"
            f"- Strengthen notice and cure period requirements\n"
            f"- Add governing law and dispute resolution clarity"
        )

    try:
        resp = requests.post(
            f"{settings.OLLAMA_BASE_URL}/api/generate",
            json={"model": "qwen2.5:0.5b", "prompt": prompt, "stream": False},
            timeout=45,
        )
        suggestion = resp.json().get('response', '').strip()
        # Only use LLM output if it's substantially different (not just same text)
        orig_words = set(original.lower().split())
        sugg_words = set(suggestion.lower().split()) if suggestion else set()
        overlap = len(orig_words & sugg_words) / max(len(orig_words), 1)
        if suggestion and len(suggestion) > 50 and overlap < 0.85:
            return suggestion
    except Exception as e:
        logger.warning(f"LLM redline generation failed: {e}")

    # Always apply rule-based on top of whatever we have
    return _rule_based_redline(original, standard, clause_type)


def _compute_diff(original: str, suggested: str) -> list:
    """
    Compute word-level diff between original and suggested text.
    Returns list of {type: 'equal'|'delete'|'insert', text: str} tokens.
    """
    orig_words = original.split()
    sugg_words = suggested.split()
    matcher = difflib.SequenceMatcher(None, orig_words, sugg_words)

    diff = []
    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == 'equal':
            diff.append({'type': 'equal', 'text': ' '.join(orig_words[i1:i2])})
        elif op == 'delete':
            diff.append({'type': 'delete', 'text': ' '.join(orig_words[i1:i2])})
        elif op == 'insert':
            diff.append({'type': 'insert', 'text': ' '.join(sugg_words[j1:j2])})
        elif op == 'replace':
            diff.append({'type': 'delete', 'text': ' '.join(orig_words[i1:i2])})
            diff.append({'type': 'insert', 'text': ' '.join(sugg_words[j1:j2])})

    return diff


def _similarity_score(a: str, b: str) -> float:
    """
    Calculate semantic similarity between two clause texts.
    Uses a combination of character-level and word-level matching.
    Returns score 0-1 where 1 = identical, 0 = completely different.
    """
    if not a or not b:
        return 0.0

    # Normalize texts: lowercase, remove extra whitespace
    a_norm = ' '.join(a.lower().split())
    b_norm = ' '.join(b.lower().split())

    # Character-level similarity (strict)
    char_sim = difflib.SequenceMatcher(None, a_norm[:1000], b_norm[:1000]).ratio()

    # Word-level similarity (more lenient)
    a_words = set(a_norm.split())
    b_words = set(b_norm.split())
    if not a_words or not b_words:
        return char_sim

    # Jaccard similarity: intersection / union
    intersection = len(a_words & b_words)
    union = len(a_words | b_words)
    word_sim = intersection / union if union > 0 else 0.0

    # Weighted average: 60% word similarity, 40% character similarity
    # This is more forgiving to rephrasing while catching major changes
    return (0.6 * word_sim) + (0.4 * char_sim)


class ContractRedlineView(APIView):
    """
    POST /api/contracts/<contract_id>/redline/
    Auto-redline all clauses in a contract against standard templates.
    Returns diff for each clause that deviates significantly.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, contract_id):
        try:
            contract = get_object_or_404(Contract, id=contract_id, user=request.user)
            threshold = float(request.data.get('threshold', 0.75))
            generate_suggestions = request.data.get('generate_suggestions', True)

            clauses = Clause.objects.filter(
                contract=contract
            ).exclude(extracted_text='').exclude(extracted_text__isnull=True)

            if not clauses.exists():
                return Response({'error': 'No clauses found for this contract'}, status=status.HTTP_400_BAD_REQUEST)

            redlines = []
            total_drifted = 0

            for clause in clauses:
                if not clause.clause_type:
                    continue

                original = clause.extracted_text or ''
                # Skip heading-only clauses (too short to redline meaningfully)
                if len(original.strip()) < 80:
                    continue

                standard = _get_standard_clause_text(clause.clause_type, exclude_contract_id=contract_id)

                if standard:
                    similarity = _similarity_score(original, standard)
                    needs_redline = similarity < threshold
                else:
                    # No standard available — use risk level to decide
                    similarity = 0.0
                    needs_redline = clause.risk_level in ('HIGH', 'MEDIUM')

                suggestion = ''
                diff = []
                if needs_redline:
                    total_drifted += 1
                    if generate_suggestions:
                        suggestion = _generate_redline_suggestion(original, standard, clause.clause_type)
                        diff = _compute_diff(original, suggestion)
                    else:
                        diff = _compute_diff(original, standard)
                        suggestion = standard

                redlines.append({
                    'clause_id': str(clause.id),
                    'clause_name': clause.clause_name or '',
                    'clause_type': clause.clause_type,
                    'original_text': original[:800],
                    'standard_text': standard[:800],
                    'suggested_text': suggestion[:800],
                    'similarity': round(similarity, 4),
                    'needs_redline': needs_redline,
                    'diff': diff[:200],  # Limit diff tokens
                    'risk_level': clause.risk_level or 'UNKNOWN',
                    'financial_impact': float(clause.financial_impact or 0),
                })

            # Sort: drifted clauses first, then by similarity (lowest = most drifted)
            redlines.sort(key=lambda x: (not x['needs_redline'], x['similarity']))

            return Response({
                'contract_id': str(contract_id),
                'contract_name': contract.original_filename,
                'total_clauses': len(redlines),
                'drifted_clauses': total_drifted,
                'threshold': threshold,
                'redlines': redlines,
            })

        except Exception as e:
            logger.error(f"Contract redline failed: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ClauseRedlineView(APIView):
    """
    POST /api/clauses/<clause_id>/redline/
    Redline a single clause against its standard template.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, clause_id):
        try:
            clause = get_object_or_404(Clause, id=clause_id, contract__user=request.user)
            generate_suggestions = request.data.get('generate_suggestions', True)
            custom_standard = request.data.get('standard_text', '')

            original = clause.extracted_text or ''
            standard = custom_standard or _get_standard_clause_text(
                clause.clause_type,
                exclude_contract_id=clause.contract_id
            )

            similarity = _similarity_score(original, standard)

            if generate_suggestions and standard:
                suggestion = _generate_redline_suggestion(original, standard, clause.clause_type or '')
            else:
                suggestion = standard

            diff = _compute_diff(original, suggestion) if suggestion else []

            return Response({
                'clause_id': str(clause.id),
                'clause_name': clause.clause_name,
                'clause_type': clause.clause_type,
                'original_text': original,
                'standard_text': standard,
                'suggested_text': suggestion,
                'similarity': round(similarity, 4),
                'diff': diff,
                'risk_level': clause.risk_level,
                'needs_redline': similarity < 0.75 and bool(standard),
            })

        except Exception as e:
            logger.error(f"Clause redline failed: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RedlineExportView(APIView):
    """
    POST /api/contracts/<contract_id>/redline/export/
    Export redline report as plain text (Word export would need python-docx).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, contract_id):
        try:
            from django.http import HttpResponse
            contract = get_object_or_404(Contract, id=contract_id, user=request.user)
            redlines = request.data.get('redlines', [])

            lines = [
                f"CONTRACT REDLINE REPORT",
                f"Contract: {contract.original_filename}",
                f"Generated: {__import__('datetime').datetime.now().isoformat()}",
                f"=" * 60,
                "",
            ]

            for r in redlines:
                if not r.get('needs_redline'):
                    continue
                lines += [
                    f"CLAUSE: {r.get('clause_name', '')} [{r.get('clause_type', '')}]",
                    f"Risk Level: {r.get('risk_level', '')} | Similarity: {r.get('similarity', 0):.2%}",
                    f"",
                    f"--- ORIGINAL ---",
                    r.get('original_text', '')[:600],
                    f"",
                    f"--- SUGGESTED REDLINE ---",
                    r.get('suggested_text', '')[:600],
                    f"",
                    f"-" * 40,
                    "",
                ]

            content = '\n'.join(lines)
            response = HttpResponse(content, content_type='text/plain')
            response['Content-Disposition'] = f'attachment; filename="redline_{contract_id}.txt"'
            return response

        except Exception as e:
            logger.error(f"Redline export failed: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
