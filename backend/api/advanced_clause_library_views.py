"""
Advanced Clause Library – API Views
"""

import logging
import re
import requests
from django.db.models import Count, Q
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from core.models import Contract, Clause, ClauseCategory

logger = logging.getLogger(__name__)

OLLAMA_URL = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')


# ── Pure-DB helpers (no ML model needed) ─────────────────────────────────────

def _live_contract_ids():
    return list(Contract.objects.values_list('id', flat=True))


def _purge_junk_categories():
    """Remove all non-standard categories — keep only seeded standard taxonomy."""
    result = ClauseCategory.objects.filter(is_standard=False).delete()
    return result[0] if result else 0


def _sync_counts():
    """Recompute clause_count from live contracts only. No ML required."""
    live_ids = _live_contract_ids()
    counts = (
        Clause.objects
        .filter(contract_id__in=live_ids)
        .exclude(clause_type__isnull=True)
        .exclude(clause_type='')
        .values('clause_type')
        .annotate(n=Count('id'))
    )
    count_map = {row['clause_type']: row['n'] for row in counts}

    to_update = []
    for cat in ClauseCategory.objects.all():
        new_count = count_map.get(cat.name, 0)
        if cat.clause_count != new_count:
            cat.clause_count = new_count
            to_update.append(cat)
    if to_update:
        ClauseCategory.objects.bulk_update(to_update, ['clause_count'])
    return count_map


def _build_tree():
    """Build nested tree from DB. No ML required."""
    _sync_counts()
    cats = list(ClauseCategory.objects.all())

    def node_dict(c):
        children = [node_dict(ch) for ch in cats if ch.parent_id == c.id]
        total = c.clause_count + sum(ch['count'] for ch in children)
        return {
            'id': c.id,
            'name': c.name,
            'count': total,
            'ownCount': c.clause_count,
            'isStandard': c.is_standard,
            'children': children,
        }

    return [node_dict(c) for c in cats if not c.parent_id]


def _get_analytics():
    """Aggregate stats. No ML required."""
    _sync_counts()
    cats = list(ClauseCategory.objects.all())
    return {
        'total_categories': len(cats),
        'total_clauses_indexed': sum(c.clause_count for c in cats),
        'standard_categories': sum(1 for c in cats if c.is_standard),
        'auto_discovered': sum(1 for c in cats if not c.is_standard),
        'top_categories': [
            {'name': c.name, 'count': c.clause_count, 'isStandard': c.is_standard}
            for c in sorted(cats, key=lambda x: x.clause_count, reverse=True)[:10]
        ],
    }


# ── Views ─────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def seed_taxonomy(request):
    """Seed standard taxonomy. Safe to call multiple times."""
    try:
        from .advanced_clause_library_service import get_taxonomy_engine
        engine = get_taxonomy_engine()
        created = engine.seed_standard_taxonomy()
    except Exception as e:
        # Model load may fail on low-memory machines — do DB-only seed
        logger.warning(f'Engine seed failed ({e}), falling back to DB-only seed')
        created = _db_only_seed()
    _purge_junk_categories()
    _sync_counts()
    return Response({'created': created, 'message': f'Seeded {created} new categories'})


def _db_only_seed():
    """Insert STANDARD_TAXONOMY into DB without loading any ML model."""
    from .advanced_clause_library_service import STANDARD_TAXONOMY
    created = 0
    for parent_name, children in STANDARD_TAXONOMY.items():
        parent, is_new = ClauseCategory.objects.get_or_create(
            name=parent_name,
            defaults={'is_standard': True, 'embedding_vector': []},
        )
        if is_new:
            created += 1
        for child_name in children:
            _, child_new = ClauseCategory.objects.get_or_create(
                name=child_name,
                defaults={
                    'is_standard': True,
                    'parent_id': parent.id,
                    'embedding_vector': [],
                },
            )
            if child_new:
                created += 1
    return created


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_taxonomy_tree(request):
    try:
        tree = _build_tree()
        return Response({'tree': tree, 'count': len(tree)})
    except Exception as e:
        logger.exception('get_taxonomy_tree failed')
        return Response({'error': str(e), 'tree': [], 'count': 0},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_analytics(request):
    try:
        return Response(_get_analytics())
    except Exception as e:
        logger.exception('get_analytics failed')
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_contract(request, contract_id):
    try:
        contract = Contract.objects.get(id=contract_id, user=request.user)
    except Contract.DoesNotExist:
        return Response({'error': 'Contract not found'}, status=status.HTTP_404_NOT_FOUND)

    try:
        from .advanced_clause_library_service import process_contract_for_library
        result = process_contract_for_library(contract, use_qwen_naming=True)
        _sync_counts()
        return Response({
            'contract_id': contract_id,
            'processed': result['processed'],
            'total_clauses': result['total'],
            'lda_topics_discovered': result.get('lda_topics', []),
            'message': f"Assigned {result['processed']} clauses to taxonomy",
        })
    except Exception as e:
        logger.exception('process_contract failed')
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def search_clauses(request):
    query = request.data.get('query', '').strip()
    if not query:
        return Response({'error': 'query is required'}, status=status.HTTP_400_BAD_REQUEST)

    top_k = min(int(request.data.get('top_k', 20)), 50)
    use_qwen = bool(request.data.get('use_qwen', True))

    try:
        from .advanced_clause_library_service import hybrid_search_with_rerank
        results = hybrid_search_with_rerank(query, top_k=top_k, use_qwen=use_qwen)
        return Response({'query': query, 'results': results, 'count': len(results)})
    except Exception as e:
        logger.exception('search_clauses failed')
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clean_taxonomy(request):
    try:
        from .advanced_clause_library_service import get_taxonomy_engine
        engine = get_taxonomy_engine()
        merged = engine.clean_taxonomy()
    except Exception as e:
        logger.warning(f'clean_taxonomy engine error: {e}')
        merged = 0
    return Response({'merged': merged, 'message': f'Merged {merged} duplicate categories'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_categories(request):
    _sync_counts()
    cats = ClauseCategory.objects.all().order_by('-clause_count')
    return Response({
        'categories': [
            {
                'id': c.id,
                'name': c.name,
                'count': c.clause_count,
                'isStandard': c.is_standard,
                'parentId': c.parent_id,
            }
            for c in cats
        ],
        'total': cats.count(),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def clauses_in_category(request, category_name):
    live_ids = _live_contract_ids()
    clauses = (
        Clause.objects
        .filter(clause_type=category_name, contract_id__in=live_ids)
        .exclude(extracted_text__isnull=True)
        .exclude(extracted_text='')
        .values('id', 'extracted_text', 'risk_level', 'risk_score', 'contract_id')[:200]
    )
    return Response({
        'category': category_name,
        'clauses': list(clauses),
        'count': len(clauses),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_neo4j_graph(request):
    """
    Build knowledge graph directly from MySQL clause data (no Neo4j required).
    Falls back to Neo4j if available and populated.
    Returns nodes + edges for frontend SVG graph.
    """
    limit = min(int(request.query_params.get('limit', 200)), 500)
    try:
        # Try Neo4j first
        from .advanced_clause_library_service import neo4j_get_graph
        graph = neo4j_get_graph(limit=limit)
        if graph['nodes']:
            return Response(graph)
    except Exception:
        pass

    # Build graph directly from MySQL — always works
    try:
        live_ids = _live_contract_ids()

        # Get clauses with their category + contract info
        clauses = list(
            Clause.objects
            .filter(contract_id__in=live_ids)
            .exclude(extracted_text__isnull=True)
            .exclude(extracted_text='')
            .values('id', 'extracted_text', 'clause_type', 'risk_level',
                    'clause_name', 'contract_id')[:limit]
        )

        nodes = []
        edges = []
        node_ids = {}

        # Category nodes first
        for c in clauses:
            cat = c['clause_type'] or c['clause_name'] or 'Uncategorised'
            if cat not in node_ids:
                node_ids[cat] = f"cat_{len(node_ids)}"
                nodes.append({
                    'id': node_ids[cat],
                    'label': cat,
                    'type': 'category',
                })

        # Clause nodes + BELONGS_TO edges
        for c in clauses:
            cid = str(c['id'])
            if cid not in node_ids:
                node_ids[cid] = f"cl_{len(node_ids)}"
                full_text = (c['extracted_text'] or '').strip()
                nodes.append({
                    'id': node_ids[cid],
                    'label': full_text[:60],
                    'fullLabel': full_text,
                    'type': 'clause',
                    'risk': c['risk_level'] or 'UNKNOWN',
                    'clauseType': c.get('clause_type') or c.get('clause_name') or '',
                })
            cat = c['clause_type'] or c['clause_name'] or 'Uncategorised'
            edges.append({
                'source': node_ids[cid],
                'target': node_ids[cat],
                'label': 'BELONGS_TO',
            })

        return Response({'nodes': nodes, 'edges': edges})
    except Exception as e:
        logger.exception('get_neo4j_graph (mysql fallback) failed')
        return Response({'error': str(e), 'nodes': [], 'edges': []},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ── Clause Insights ───────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def clause_insights(request, category_name):
    """
    Per-category insights: contract distribution, risk breakdown, top clauses.
    """
    live_ids = _live_contract_ids()
    clauses = list(
        Clause.objects
        .filter(clause_type=category_name, contract_id__in=live_ids)
        .exclude(extracted_text__isnull=True)
        .exclude(extracted_text='')
        .values('id', 'extracted_text', 'risk_level', 'risk_score', 'contract_id')[:500]
    )

    if not clauses:
        return Response({
            'category': category_name,
            'total_clauses': 0,
            'unique_contracts': 0,
            'risk_breakdown': {},
            'contract_distribution': [],
            'sample_clauses': [],
        })

    # Risk breakdown
    risk_counts = {}
    for c in clauses:
        r = (c['risk_level'] or 'UNKNOWN').upper()
        risk_counts[r] = risk_counts.get(r, 0) + 1

    # Contract distribution (how many clauses per contract)
    contract_counts = {}
    for c in clauses:
        cid = str(c['contract_id'])
        contract_counts[cid] = contract_counts.get(cid, 0) + 1

    # Enrich with contract titles
    contract_ids = list(contract_counts.keys())
    contracts = {
        str(c.id): (c.original_filename or c.filename or str(c.id))
        for c in Contract.objects.filter(id__in=contract_ids).only('id', 'original_filename', 'filename')
    }
    contract_distribution = sorted(
        [{'contract_id': cid, 'title': contracts.get(cid, cid)[:60], 'clause_count': cnt}
         for cid, cnt in contract_counts.items()],
        key=lambda x: x['clause_count'], reverse=True
    )[:20]

    # Top sample clauses (one per contract for diversity)
    seen = set()
    sample = []
    for c in clauses:
        cid = str(c['contract_id'])
        if cid not in seen:
            seen.add(cid)
            sample.append({
                'id': c['id'],
                'text': (c['extracted_text'] or '')[:300],
                'risk_level': c['risk_level'] or 'UNKNOWN',
                'risk_score': c['risk_score'],
                'contract_id': cid,
                'contract_title': (contracts.get(cid) or cid)[:60],
            })
        if len(sample) >= 10:
            break

    return Response({
        'category': category_name,
        'total_clauses': len(clauses),
        'unique_contracts': len(contract_counts),
        'risk_breakdown': risk_counts,
        'contract_distribution': contract_distribution,
        'sample_clauses': sample,
    })


# ── Clause Risk Scoring ───────────────────────────────────────────────────────

def _qwen_risk_score(text: str) -> dict:
    prompt = (
        "You are a legal risk analyst. Score the following contract clause.\n"
        "Reply ONLY with valid JSON in this exact format:\n"
        '{"risk": "High|Medium|Low", "reason": "one sentence", "fix": "one sentence improvement"}\n\n'
        f"Clause:\n{text[:800]}"
    )
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": "qwen2.5:0.5b", "prompt": prompt, "stream": False},
            timeout=40,
        )
        raw = resp.json().get('response', '')
        # Extract JSON from response
        match = re.search(r'\{.*?\}', raw, re.DOTALL)
        if match:
            import json
            return json.loads(match.group())
    except Exception as e:
        logger.warning(f'Qwen risk score failed: {e}')
    # Fallback heuristic
    text_lower = text.lower()
    if any(w in text_lower for w in ['indemnif', 'unlimited', 'consequential', 'terminat']):
        return {'risk': 'High', 'reason': 'Contains high-risk legal terms.', 'fix': 'Add liability cap and define indemnification scope.'}
    if any(w in text_lower for w in ['warrant', 'represent', 'comply', 'breach']):
        return {'risk': 'Medium', 'reason': 'Contains moderate risk obligations.', 'fix': 'Clarify scope and add cure period.'}
    return {'risk': 'Low', 'reason': 'Clause appears standard.', 'fix': 'No immediate changes needed.'}


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def score_clause_risk(request):
    """
    Score a single clause for risk. Returns {"risk", "reason", "fix"}.
    """
    text = (request.data.get('text') or '').strip()
    if not text:
        return Response({'error': 'text is required'}, status=status.HTTP_400_BAD_REQUEST)
    result = _qwen_risk_score(text)
    return Response(result)


# ── Clause Negotiation AI ─────────────────────────────────────────────────────

# Rule-based substitution tables for each mode
_SAFER_SUBS = [
    (r'shall not be liable for any', 'shall not be liable for direct'),
    (r'unlimited liability', 'liability capped at the total fees paid in the preceding 12 months'),
    (r'sole discretion', 'reasonable discretion'),
    (r'immediately upon notice', 'upon 30 days\' written notice'),
    (r'without cause', 'for convenience upon 30 days\' written notice'),
    (r'at any time', 'upon reasonable written notice'),
    (r'irrevocable', 'revocable upon 60 days\' written notice'),
    (r'all intellectual property', 'intellectual property created specifically under this Agreement'),
    (r'waives all claims', 'waives all claims except those arising from gross negligence or willful misconduct'),
    (r'consequential[, ]*indirect[, ]*or special damages', 'consequential, indirect, or special damages, except in cases of fraud or willful misconduct'),
]

_MARKET_SUBS = [
    (r'unlimited liability', 'aggregate liability shall not exceed the fees paid in the 12 months prior to the claim'),
    (r'sole discretion', 'reasonable discretion, not to be unreasonably withheld'),
    (r'immediately terminat', 'terminate upon 30 days\' written notice'),
    (r'all rights reserved', 'all rights reserved, subject to the licenses granted herein'),
    (r'irrevocable', 'non-revocable during the term of this Agreement'),
    (r'without any warranty', 'subject to the limited warranties set forth herein'),
]

_AGGRESSIVE_SUBS = [
    (r'reasonable efforts', 'best efforts and at its sole cost and expense'),
    (r'may terminate', 'shall have the right to immediately terminate'),
    (r'upon 30 days', 'upon 5 business days\''),
    (r'upon \d+ days', 'upon 5 business days\''),
    (r'reasonable notice', 'written notice of no less than 5 business days'),
    (r'limited warranty', 'full warranty with no exclusions'),
    (r'limitation of liability', 'unlimited liability with full indemnification obligations'),
    (r'mutual indemnification', 'full indemnification by the other party'),
    (r'prior written consent', 'prior written consent, which may be withheld in the disclosing party\'s absolute discretion'),
    (r'without prior written consent', 'without prior written consent, which may be withheld for any reason'),
    (r'holds? in strict confidence', 'holds in strict confidence and shall implement all reasonable technical and organizational measures to protect'),
    (r'shall not disclose', 'shall not disclose, reproduce, summarize, or otherwise make available'),
]

_AGGRESSIVE_ADDITIONS = {
    'confidentiality': [
        'Added: Breach of confidentiality triggers immediate injunctive relief without bond requirement.',
        'Added: Receiving party liable for breaches by its employees, contractors, and agents.',
        'Added: Confidentiality obligations survive termination for 7 years.',
        'Added: Receiving party must notify Disclosing party within 24 hours of any suspected breach.',
        'Added: Return or certified destruction of all Confidential Information within 5 days of termination.',
    ],
    'termination': [
        'Added: Immediate termination right on first material breach — no cure period.',
        'Added: Counterparty must pay all outstanding fees immediately upon termination.',
        'Added: Non-solicitation of employees/clients for 24 months post-termination.',
    ],
    'indemnification': [
        'Added: Indemnification obligations are uncapped.',
        'Added: Indemnification covers all losses including consequential and punitive damages.',
        'Added: Indemnitee has sole control of defense and settlement.',
    ],
    'liability': [
        'Added: Counterparty liable for all consequential and indirect damages.',
        'Added: No limitation of liability for IP infringement, confidentiality breach, or fraud.',
        'Added: Aggregate cap does not apply to willful breaches.',
    ],
    'general': [
        'Added: Breach triggers immediate suspension of all services.',
        'Added: All obligations are absolute, not qualified by reasonableness.',
        'Added: Prevailing party entitled to full legal costs and attorney fees.',
    ],
}

def _apply_subs(text: str, subs: list) -> tuple:
    """Apply regex substitutions, return (new_text, list_of_changes)."""
    changes = []
    result = text
    for pattern, replacement in subs:
        new = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        if new != result:
            changes.append(f'"{pattern}" → "{replacement}"')
            result = new
    return result, changes


def _detect_clause_type(text: str) -> str:
    tl = text.lower()
    if 'confidential' in tl: return 'confidentiality'
    if 'terminat' in tl: return 'termination'
    if 'indemnif' in tl: return 'indemnification'
    if 'liability' in tl or 'liable' in tl: return 'liability'
    if 'payment' in tl or 'invoice' in tl: return 'payment'
    if 'force majeure' in tl: return 'force_majeure'
    if 'intellectual property' in tl or 'copyright' in tl: return 'ip'
    if 'warrant' in tl: return 'warranty'
    if 'dispute' in tl or 'arbitration' in tl: return 'dispute'
    return 'general'


_EXPLANATIONS = {
    'confidentiality': (
        "This is a Confidentiality clause. It requires both parties to keep each other's "
        "non-public information secret and not share it with third parties without permission. "
        "Risk for recipient: broad definition of 'Confidential Information' may restrict normal business operations. "
        "Risk for discloser: relies on the other party's compliance — breach is hard to detect early."
    ),
    'termination': (
        "This is a Termination clause. It defines when and how either party can end the contract. "
        "'Termination for Convenience' means ending the contract without needing a reason (typically requires notice). "
        "'Termination for Cause' means ending it due to a breach or failure. "
        "Risk: short notice periods leave little time to transition; ensure IP and data return obligations are clear."
    ),
    'indemnification': (
        "This is an Indemnification clause. It requires one party to compensate the other for losses, damages, "
        "or legal costs arising from specified events (e.g. IP infringement, negligence). "
        "Risk: unlimited indemnification can create catastrophic financial exposure. "
        "Always check if there's a cap, and whether gross negligence / willful misconduct are carved out."
    ),
    'liability': (
        "This is a Limitation of Liability clause. It caps how much either party can be sued for. "
        "Common cap: fees paid in the last 12 months. Consequential damages (lost profits, lost data) are typically excluded. "
        "Risk: if the cap is too low, it may not cover actual losses. Watch for carve-outs that expose you to unlimited liability."
    ),
    'payment': (
        "This is a Payment clause. It defines fees, invoicing schedules, payment deadlines, and late payment penalties. "
        "Risk for payer: automatic late fees and suspension rights if payment is missed. "
        "Risk for payee: disputed invoice provisions — ensure the dispute window is reasonable (15-30 days)."
    ),
    'force_majeure': (
        "This is a Force Majeure clause. It excuses a party from performing if an extraordinary event beyond their control "
        "(war, pandemic, natural disaster) prevents performance. "
        "Risk: vague definitions may allow a party to avoid obligations too easily. "
        "Look for: notice requirements, mitigation obligations, and a termination right if the event lasts too long."
    ),
    'ip': (
        "This is an Intellectual Property clause. It determines who owns work created under the contract. "
        "'Work made for hire' and 'assigns all IP' mean the client owns everything. "
        "Risk for provider: you may lose rights to your own tools, methodologies, or pre-existing IP. "
        "Ensure pre-existing IP is explicitly carved out with a license-back to the client."
    ),
    'warranty': (
        "This is a Warranty clause. It sets out promises about the quality and fitness of the services or products. "
        "An 'AS IS' disclaimer strips all warranties. "
        "Risk: no warranty = no recourse if deliverables are defective. "
        "Market standard: 90-day workmanship warranty with re-performance as the sole remedy."
    ),
    'dispute': (
        "This is a Dispute Resolution clause. It determines how disagreements are resolved. "
        "Arbitration is private and usually faster than court but limits appeal rights. "
        "Governing law determines which country's laws apply. Jurisdiction determines where disputes are heard. "
        "Risk: one-sided jurisdiction (e.g. only courts in the other party's city) creates practical barriers to justice."
    ),
    'general': (
        "This clause sets out specific rights and obligations between the parties. "
        "Key questions to ask: (1) Are the obligations mutual or one-sided? "
        "(2) Is there a time limit on these obligations? "
        "(3) What happens if this clause is breached? "
        "(4) Are there any carve-outs or exceptions that could leave you exposed?"
    ),
}

_SAFER_ADDITIONS = {
    'confidentiality': [
        'Added: exceptions for information already in public domain.',
        'Added: 2-year post-termination sunset on confidentiality obligations.',
        'Added: Receiving Party may disclose if required by law, with prior notice to Discloser.',
    ],
    'termination': [
        'Added: 30-day cure period before termination for cause takes effect.',
        'Added: Upon termination, Provider must return all Client data within 5 business days.',
        'Added: Accrued rights survive termination.',
    ],
    'indemnification': [
        'Added: Mutual indemnification (both parties indemnify each other).',
        'Added: Indemnification capped at aggregate liability limit.',
        'Added: Indemnitor controls defense; indemnitee has right to participate with own counsel.',
    ],
    'liability': [
        'Added: Carve-out — cap does not apply to gross negligence or fraud.',
        'Added: Cap set at 12 months of fees paid.',
        'Added: Mutual application — cap applies equally to both parties.',
    ],
    'payment': [
        'Added: 15-day window to dispute invoices in writing.',
        'Added: Interest on late payments capped at 1.5% per month.',
        'Added: Suspension of services only after 60 days of non-payment with written notice.',
    ],
    'force_majeure': [
        'Added: Affected party must notify within 5 business days.',
        'Added: Termination right if Force Majeure continues beyond 60 days.',
        'Added: Payment obligations for work completed prior to Force Majeure event remain.',
    ],
    'ip': [
        'Added: Provider retains all pre-existing IP; Client gets a perpetual license to use it.',
        'Added: Work Product limited to deliverables specifically created under this Agreement.',
        'Added: Provider background IP explicitly excluded from assignment.',
    ],
    'warranty': [
        'Added: 90-day workmanship warranty from delivery date.',
        'Added: Remedy for breach is re-performance at Provider\'s cost.',
        'Added: Warranty does not cover Client-caused defects.',
    ],
    'dispute': [
        'Added: Parties must attempt good-faith negotiation for 30 days before arbitration.',
        'Added: Either party may seek injunctive relief in any court without breaching arbitration agreement.',
        'Added: Arbitration costs shared equally between parties.',
    ],
    'general': [
        'Added: Either party may raise concerns in writing before exercising any remedy.',
        'Added: Obligations apply equally to both parties unless expressly stated otherwise.',
        'Added: Any waiver must be in writing and does not constitute ongoing waiver.',
    ],
}

def _rule_based_negotiate(text: str, mode: str) -> dict:
    clause_type = _detect_clause_type(text)

    if mode == 'explain':
        explanation = _EXPLANATIONS.get(clause_type, _EXPLANATIONS['general'])
        return {
            'output': explanation,
            'key_changes': [
                f'Clause type detected: {clause_type.replace("_", " ").title()}',
                'Plain English explanation provided',
                'Risk assessment for each party included',
            ],
            'risk_delta': 'neutral',
        }

    if mode == 'safer':
        output, changes = _apply_subs(text, _SAFER_SUBS)
        additions = _SAFER_ADDITIONS.get(clause_type, _SAFER_ADDITIONS['general'])
        if not changes:
            changes = ['Reviewed — no high-risk terms detected in original text']
        changes.extend(additions)
        # Add protective header
        output = (
            f"[SAFER VERSION — {clause_type.replace('_',' ').upper()} CLAUSE]\n\n"
            + output
            + "\n\n[ADDITIONAL PROTECTIONS RECOMMENDED]\n"
            + "\n".join(f"• {a}" for a in additions)
        )
        return {'output': output, 'key_changes': changes, 'risk_delta': 'improved'}

    if mode == 'market':
        output, changes = _apply_subs(text, _MARKET_SUBS)
        if not changes:
            changes = ['Clause already uses market-standard language']
        output = f"[MARKET-STANDARD VERSION]\n\n" + output
        changes.insert(0, 'Rebalanced obligations to be mutual')
        changes.append('Aligned with IACCM/World Commerce & Contracting market standards')
        return {'output': output, 'key_changes': changes, 'risk_delta': 'neutral'}

    if mode == 'aggressive':
        output, changes = _apply_subs(text, _AGGRESSIVE_SUBS)
        additions = _AGGRESSIVE_ADDITIONS.get(clause_type, _AGGRESSIVE_ADDITIONS['general'])
        if not changes:
            changes = ['Strengthened obligations on counterparty']
        output = (
            f"[AGGRESSIVE VERSION — MAXIMUM PROTECTION]\n\n"
            + output
            + "\n\n[ADDITIONAL AGGRESSIVE PROTECTIONS]\n"
            + "\n".join(f"• {a}" for a in additions)
        )
        changes.extend(additions)
        return {'output': output, 'key_changes': changes, 'risk_delta': 'worsened'}

    return {'output': text, 'key_changes': [], 'risk_delta': 'neutral'}


def _qwen_negotiate(text: str, mode: str) -> dict:
    # Skip Qwen entirely — rule-based is more reliable and always works
    return _rule_based_negotiate(text, mode)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def negotiate_clause(request):
    """
    Rewrite/explain a clause. modes: safer | market | aggressive | explain
    """
    text = (request.data.get('text') or '').strip()
    mode = (request.data.get('mode') or 'safer').strip()
    if not text:
        return Response({'error': 'text is required'}, status=status.HTTP_400_BAD_REQUEST)
    if mode not in ('safer', 'market', 'aggressive', 'explain'):
        return Response({'error': 'mode must be safer|market|aggressive|explain'},
                        status=status.HTTP_400_BAD_REQUEST)
    result = _qwen_negotiate(text, mode)
    return Response({'mode': mode, **result})


# ── Contract Risk View ────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_all_contracts(request):
    """
    Pure-DB keyword assignment against STANDARD taxonomy only.
    Never creates new categories. Maps clause text → nearest standard category
    using keyword scoring, then syncs counts.
    """
    live_ids = _live_contract_ids()

    # Only use STANDARD categories as targets — never auto-create from clause names
    cats = list(ClauseCategory.objects.filter(is_standard=True))
    if not cats:
        return Response({'error': 'No standard categories found — seed taxonomy first'},
                        status=status.HTTP_400_BAD_REQUEST)

    # Weighted keyword map: (keyword, weight)
    # Subcategories listed BEFORE parents so they win when more specific
    CATEGORY_KEYWORDS = {
        # ── Dispute Resolution subcategories ──
        'Arbitration':           [('arbitration', 8), ('arbitrator', 7), ('aaa rules', 6), ('jams', 5), ('binding arbitration', 7), ('arbitral award', 6)],
        'Governing Law':         [('governed by the laws', 8), ('governing law', 8), ('choice of law', 7), ('laws of the state', 6)],
        'Jurisdiction':          [('exclusive jurisdiction', 7), ('submit to jurisdiction', 6), ('courts of', 5), ('jurisdiction', 4)],
        'Mediation':             [('mediation', 7), ('mediator', 6), ('non-binding mediation', 7), ('submit to mediation', 6)],
        'Litigation':            [('litigation', 6), ('lawsuit', 5), ('court proceedings', 5), ('legal proceedings', 4)],
        'Expert Determination':  [('expert determination', 8), ('independent expert', 7), ('expert opinion', 5)],
        # ── Assignment subcategories ──
        'Assignment Restriction':[('may not assign', 8), ('shall not assign', 8), ('without consent', 5), ('consent to assign', 6)],
        'Change of Control':     [('change of control', 9), ('merger', 5), ('acquisition', 5), ('change in ownership', 6)],
        'Novation':              [('novation', 9), ('novated', 8)],
        # ── Indemnification subcategories ──
        'IP Indemnity':          [('ip indemnif', 8), ('intellectual property indemnif', 8), ('patent indemnif', 7), ('infringement indemnif', 7)],
        'Third Party Claims':    [('third party claim', 8), ('third-party claim', 8), ('third party action', 6)],
        'Tax Indemnity':         [('tax indemnif', 8), ('indemnif.*tax', 7), ('taxes and indemnif', 7)],
        # ── Liability subcategories ──
        'Limitation of Liability':[('limitation of liability', 9), ('liability cap', 8), ('aggregate liability shall not exceed', 8), ('limit.*liability', 6)],
        'Consequential Damages': [('consequential damage', 8), ('indirect damage', 7), ('special damage', 6), ('punitive damage', 6), ('lost profit', 6)],
        # ── Termination subcategories ──
        'Termination for Cause': [('termination for cause', 9), ('terminate for cause', 8), ('material breach', 5)],
        'Termination for Convenience': [('termination for convenience', 9), ('terminate for convenience', 8), ('without cause', 6)],
        # ── IP subcategories ──
        'Work Product':          [('work product', 8), ('work made for hire', 8), ('deliverable', 5)],
        'Ownership':             [('ownership of', 7), ('owns all right', 7), ('title and interest', 6)],
        'Licensing':             [('license to use', 7), ('grant.*license', 6), ('non-exclusive license', 6), ('royalty-free', 5)],
        # ── Payment subcategories ──
        'Invoicing':             [('invoice', 7), ('invoicing', 7), ('billing cycle', 6), ('submit invoice', 6)],
        'Late Fees':             [('late fee', 8), ('interest on late', 7), ('overdue', 6), ('late payment', 6)],
        'Payment Terms':         [('payment terms', 8), ('net 30', 7), ('net 60', 7), ('days of invoice', 6)],
        # ── Warranty subcategories ──
        'Service Warranty':      [('service warranty', 8), ('warrant.*service', 7), ('services conform', 6)],
        'Disclaimer':            [('as-is', 8), ('as is', 7), ('no warranty', 7), ('disclaimer of warrant', 7), ('implied warrant', 6)],
        # ── Security subcategories ──
        'Data Breach':           [('data breach', 9), ('breach notification', 8), ('security incident', 7), ('notify.*breach', 6)],
        'Encryption':            [('encrypt', 8), ('aes-256', 7), ('tls', 6), ('data in transit', 5)],
        # ── Parent categories (catch-all when no subcategory matches) ──
        'Assignment':            [('assign', 4), ('transfer of rights', 5), ('assignee', 4)],
        'Audit Rights':          [('audit right', 7), ('right to audit', 7), ('books and records', 5), ('audit', 3)],
        'Compliance':            [('compliance with law', 6), ('applicable law', 5), ('regulatory', 4), ('comply with', 4)],
        'Confidentiality':       [('confidential information', 7), ('non-disclosure', 7), ('nda', 6), ('trade secret', 6), ('confidential', 4)],
        'Dispute Resolution':    [('dispute resolution', 7), ('resolve.*dispute', 5), ('dispute', 3)],
        'Force Majeure':         [('force majeure', 9), ('act of god', 7), ('beyond reasonable control', 7), ('beyond its control', 6), ('natural disaster', 5), ('pandemic', 4)],
        'Indemnification':       [('indemnification', 7), ('indemnify', 7), ('hold harmless', 6), ('indemnif', 5)],
        'Insurance':             [('insurance', 7), ('insured', 6), ('policy limits', 6), ('coverage', 5), ('premium', 4)],
        'Intellectual Property': [('intellectual property', 7), ('copyright', 6), ('patent', 6), ('trademark', 5), ('ip rights', 5)],
        'Liability':             [('liable', 4), ('liability', 4)],
        'Payment':               [('payment shall', 5), ('fees and expenses', 5), ('remuneration', 5), ('payment', 3)],
        'Security':              [('data security', 7), ('cybersecurity', 7), ('security measures', 5), ('safeguard', 4)],
        'Service Levels':        [('service level', 8), ('sla', 7), ('uptime', 7), ('response time', 6), ('availability', 5)],
        'Termination':           [('upon termination', 5), ('terminat', 3)],
        'Warranty':              [('warrants and represents', 7), ('representation and warrant', 6), ('guarantee', 5), ('warranty', 4)],
    }

    cat_by_name = {c.name: c for c in cats}

    all_clauses = list(
        Clause.objects
        .filter(contract_id__in=live_ids)
        .exclude(extracted_text__isnull=True)
        .exclude(extracted_text='')
        .values('id', 'extracted_text', 'clause_name')
    )

    assigned = 0
    to_update = []

    for clause in all_clauses:
        text = (clause['extracted_text'] or '').lower()
        name = (clause['clause_name'] or '').lower()
        if len(text) < 10:
            continue

        best_cat = None
        best_score = 0

        for cat_name, weighted_keywords in CATEGORY_KEYWORDS.items():
            if cat_name not in cat_by_name:
                continue
            # clause_name match gives 3x bonus
            name_bonus = sum(w * 3 for kw, w in weighted_keywords if kw in name)
            text_score = sum(w for kw, w in weighted_keywords if kw in text)
            score = name_bonus + text_score
            if score > best_score:
                best_score = score
                best_cat = cat_name

        if best_cat and best_score > 0:
            c = Clause(id=clause['id'])
            c.clause_type = best_cat
            to_update.append(c)
            assigned += 1

    if to_update:
        Clause.objects.bulk_update(to_update, ['clause_type'])

    # Wipe all non-standard junk categories, then sync counts
    _purge_junk_categories()
    _sync_counts()

    return Response({
        'assigned': assigned,
        'total_clauses': len(all_clauses),
        'message': f'Assigned {assigned} clauses to taxonomy categories',
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def contract_risk_view(request):
    """
    Per-contract high/safe clause counts for all live contracts.
    """
    live_ids = _live_contract_ids()
    contracts = list(Contract.objects.filter(id__in=live_ids).values('id', 'original_filename', 'filename')[:100])

    result = []
    for c in contracts:
        clauses = list(
            Clause.objects
            .filter(contract_id=c['id'])
            .exclude(extracted_text__isnull=True)
            .values_list('risk_level', flat=True)
        )
        if not clauses:
            continue
        high = sum(1 for r in clauses if (r or '').upper() == 'HIGH')
        medium = sum(1 for r in clauses if (r or '').upper() == 'MEDIUM')
        low = sum(1 for r in clauses if (r or '').upper() == 'LOW')
        total = len(clauses)
        display_name = c.get('original_filename') or c.get('filename') or str(c['id'])
        result.append({
            'contract_id': c['id'],
            'title': display_name[:60],
            'total_clauses': total,
            'high_risk': high,
            'medium_risk': medium,
            'low_risk': low,
            'safe_clauses': low,
            'risk_score': round((high * 3 + medium * 1) / max(total, 1), 2),
        })

    result.sort(key=lambda x: x['risk_score'], reverse=True)
    return Response({'contracts': result, 'total': len(result)})
