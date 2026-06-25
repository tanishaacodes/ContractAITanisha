"""
Clause Drill-Down APIs
Provides detailed clause-level analysis when clicking contract dots in quadrants
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from core.models import Clause, Contract
from ai.risk_engine import score_clause_risk
from api.redline_engine import classify_risk_type, calculate_risk_score, generate_suggested_clause, generate_risk_explanation


@require_http_methods(["GET"])
def contract_clause_drilldown(request, contract_id):
    """
    Get all risky clauses for a specific contract

    Returns clauses sorted by risk score (highest first) with:
    - Clause type and text
    - Risk score
    - Explainable risk reasons
    """
    clauses = Clause.objects.filter(contract_id=contract_id).values(
        'id', 'clause_type', 'extracted_text'
    )

    response = []

    for c in clauses:
        # Use existing risk score from Clause model, or calculate on the fly
        if c.get('risk_score'):
            risk_score = c['risk_score']
            risk_reason = f"Risk score: {risk_score}"
        else:
            # Calculate risk on the fly
            risk_score, risk_reason = score_clause_risk(c['extracted_text'])

        response.append({
            'clause_id': c['id'],
            'clause_type': c['clause_type'] or 'General',
            'extracted_text': c['extracted_text'],
            'risk_score': risk_score,
            'risk_reason': risk_reason
        })

    # Sort by risk score (highest first)
    response.sort(key=lambda x: x['risk_score'], reverse=True)

    return JsonResponse(response, safe=False)


@require_http_methods(["GET"])
def high_risk_clauses_only(request, contract_id):
    """
    Get only high-risk clauses (risk_score >= 0.6) for executive view

    Used when decision-makers only want to see critical issues
    """
    clauses = Clause.objects.filter(contract_id=contract_id).values(
        'id', 'clause_type', 'extracted_text'
    )

    response = []

    for c in clauses:
        # Use existing risk score from Clause model, or calculate on the fly
        if c.get('risk_score'):
            risk_score = c['risk_score']
            risk_reason = f"Risk score: {risk_score}"
        else:
            risk_score, risk_reason = score_clause_risk(c['extracted_text'])

        # Only include high-risk clauses
        if risk_score >= 0.6:
            response.append({
                'clause_id': c['id'],
                'clause_type': c['clause_type'] or 'General',
                'extracted_text': c['extracted_text'],
                'risk_score': risk_score,
                'risk_reason': risk_reason
            })

    # Sort by risk score (highest first)
    response.sort(key=lambda x: x['risk_score'], reverse=True)

    return JsonResponse(response, safe=False)


@require_http_methods(["GET"])
def clause_search(request):
    """
    Semantic search across all clauses for a user

    Query parameter: q (search query)
    """
    from ai.search import search_clauses
    from ai.embedding import embed

    user_id = request.GET.get('user_id')
    query = request.GET.get('q')

    if not user_id or not query:
        return JsonResponse({'error': 'user_id and q parameters required'}, status=400)

    # Get all clauses with embeddings for this user
    from core.models import ClauseEmbedding, Contract

    # Get contracts for this user
    contract_ids = Contract.objects.filter(user_id=user_id).values_list('id', flat=True)

    # Get clauses from these contracts
    clauses = Clause.objects.filter(contract_id__in=contract_ids).values(
        'id', 'clause_type', 'extracted_text', 'contract_id'
    )

    # Build embedding dictionary
    clause_embeddings = {}
    for clause in clauses:
        try:
            emb_obj = ClauseEmbedding.objects.get(clause_id=clause['id'])
            clause_embeddings[clause['id']] = emb_obj.embedding
        except ClauseEmbedding.DoesNotExist:
            # Generate embedding on the fly
            clause_embeddings[clause['id']] = embed(clause['extracted_text'])

    # Perform search
    results = search_clauses(query, clause_embeddings)

    # Format response with clause details
    response = []
    for clause_id, score in results[:10]:  # Top 10 results
        clause = next((c for c in clauses if c['id'] == clause_id), None)
        if clause:
            response.append({
                'clause_id': clause_id,
                'similarity_score': round(score, 3),
                'clause_type': clause['clause_type'],
                'extracted_text': clause['extracted_text'],
                'contract_id': clause['contract_id']
            })

    return JsonResponse(response, safe=False)


@csrf_exempt
@require_http_methods(["POST"])
def auto_redline_high_risk(request, contract_id):
    """
    Batch auto-redline: find every high-risk clause in a contract,
    generate a safer suggestion for each, and return original + suggestion pairs.

    Threshold: risk_score >= 0.6 (from Clause model) OR redline_engine score >= 60.
    Uses redline_engine's rule-based + LLM fallback pipeline.
    """
    try:
        contract = Contract.objects.get(id=contract_id)
    except Contract.DoesNotExist:
        return JsonResponse({'error': 'Contract not found'}, status=404)

    jurisdiction = contract.jurisdiction or 'Common Law'

    clauses = Clause.objects.filter(contract_id=contract_id).values(
        'id', 'clause_type', 'extracted_text', 'risk_score'
    )

    results = []
    for c in clauses:
        text = c['extracted_text'] or ''
        if not text.strip():
            continue

        # Use stored risk_score if available, otherwise score on-the-fly
        stored_score = c['risk_score']
        if stored_score is not None:
            engine_score = int(stored_score * 100)  # model stores 0-1
        else:
            engine_score = calculate_risk_score(text)

        # Only process high-risk clauses (score >= 60 on 0-100 scale)
        if engine_score < 60:
            continue

        risk_type = classify_risk_type(text)
        explanation = generate_risk_explanation(text, risk_type, engine_score)
        suggestion = generate_suggested_clause(text, engine_score, risk_type, jurisdiction)

        results.append({
            'clause_id': str(c['id']),
            'clause_type': c['clause_type'] or 'General',
            'original_text': text,
            'suggested_text': suggestion,
            'risk_score': engine_score,
            'risk_type': risk_type,
            'risk_explanation': explanation,
            'changed': suggestion.strip() != text.strip(),
        })

    # Sort by risk_score descending
    results.sort(key=lambda x: x['risk_score'], reverse=True)

    return JsonResponse({
        'contract_id': str(contract_id),
        'total_high_risk': len(results),
        'redlines': results,
    })
