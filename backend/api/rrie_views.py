"""
RRIE (Risk & Responsibility Intelligence Engine) API Views
===========================================================
Separate module for sentence classification, party attribution, and risk intelligence.

This module handles:
- Sentence type classification (Heading/Definition/Obligation/Risk/Right)
- Party attribution (Contractor/Employer/Shared)
- Risk scoring and keyword detection
- Clause explanation (LLM-powered)
- Risk breakdown and explainability
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
import logging

from core.models import Contract, Clause
from .sentence_classifier import get_sentence_classifier
from .party_attribution import get_party_attributor
from .risk_keyword_scorer import get_risk_scorer
from .explain_service import get_clause_explainer

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_contract_rrie(request, contract_id):
    """
    Process contract with RRIE (Risk & Responsibility Intelligence Engine).

    This applies:
    - Sentence classification
    - Party attribution
    - Risk scoring
    - Financial impact calculation

    URL: POST /api/rrie/contracts/{contract_id}/process
    """
    try:
        # Get contract
        try:
            contract = Contract.objects.get(id=contract_id, user=request.user)
        except Contract.DoesNotExist:
            return Response(
                {'error': 'Contract not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get all clauses
        clauses = Clause.objects.filter(contract=contract)

        if not clauses.exists():
            return Response(
                {'error': 'No clauses found. Please extract clauses first.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        logger.info(f"Processing {clauses.count()} clauses with RRIE for contract {contract_id}")

        # Prepare clause texts
        clause_texts = []
        clause_objs = []

        for clause in clauses:
            text = clause.extracted_text or clause.context_sentences or clause.clause_name
            if text and len(text.strip()) > 10:
                clause_texts.append(text)
                clause_objs.append(clause)

        if len(clause_texts) < 1:
            return Response(
                {'error': 'Not enough valid clause texts for RRIE processing'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Initialize RRIE services
        sentence_classifier = get_sentence_classifier()
        party_attributor = get_party_attributor()
        risk_scorer = get_risk_scorer()

        # Step 1: Classify sentence types
        logger.info("RRIE Step 1: Classifying sentence types...")
        sentence_types = sentence_classifier.classify_batch(clause_texts)

        # Step 2: Attribute parties
        logger.info("RRIE Step 2: Attributing parties...")
        parties = party_attributor.attribute_batch(clause_texts, sentence_types)

        # Step 3: Score risks (with context awareness)
        logger.info("RRIE Step 3: Scoring risks with context...")
        risk_results = []

        for idx, clause_obj in enumerate(clause_objs):
            # Score with full context for better accuracy
            risk_result = risk_scorer.score(
                text=clause_texts[idx],
                clause_name=clause_obj.clause_name,
                sentence_type=sentence_types[idx],
                party=parties[idx]
            )
            risk_results.append(risk_result)

        # Step 4: Update database
        logger.info("RRIE Step 4: Updating database...")
        updated_count = 0

        with transaction.atomic():
            for idx, clause_obj in enumerate(clause_objs):
                risk_result = risk_results[idx]

                # Update RRIE fields
                clause_obj.sentence_type = sentence_types[idx]
                clause_obj.party = parties[idx]
                clause_obj.risk_score = risk_result['normalized_score']
                clause_obj.risk_level = risk_result['risk_level']
                clause_obj.keywords = risk_result['keywords']
                clause_obj.financial_impact = risk_scorer.calculate_financial_impact(
                    risk_result['normalized_score']
                )['amount']

                clause_obj.save()
                updated_count += 1

        logger.info(f"RRIE processing complete: {updated_count} clauses updated")

        return Response({
            'success': True,
            'contract_id': str(contract_id),
            'clauses_processed': updated_count,
            'summary': {
                'sentence_types': {
                    'HEADING': sentence_types.count('HEADING'),
                    'DEFINITION': sentence_types.count('DEFINITION'),
                    'OBLIGATION': sentence_types.count('OBLIGATION'),
                    'RISK': sentence_types.count('RISK'),
                    'RIGHT': sentence_types.count('RIGHT'),
                },
                'parties': {
                    'CONTRACTOR': parties.count('CONTRACTOR'),
                    'EMPLOYER': parties.count('EMPLOYER'),
                    'SHARED': parties.count('SHARED'),
                },
                'risk_levels': {
                    'HIGH': sum(1 for r in risk_results if r['risk_level'] == 'HIGH'),
                    'MEDIUM': sum(1 for r in risk_results if r['risk_level'] == 'MEDIUM'),
                    'LOW': sum(1 for r in risk_results if r['risk_level'] == 'LOW'),
                }
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"RRIE processing failed: {e}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_rrie_analysis(request, contract_id):
    """
    Get RRIE analysis summary for a contract.

    Returns:
    - Sentence type distribution
    - Party attribution breakdown
    - Risk level distribution
    - High-risk clauses

    URL: GET /api/rrie/contracts/{contract_id}/analysis
    """
    try:
        # Get contract
        try:
            contract = Contract.objects.get(id=contract_id, user=request.user)
        except Contract.DoesNotExist:
            return Response(
                {'error': 'Contract not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get clauses with RRIE data
        clauses = Clause.objects.filter(contract=contract).exclude(sentence_type__isnull=True)

        if not clauses.exists():
            return Response(
                {'message': 'No RRIE analysis found. Please process the contract first.'},
                status=status.HTTP_200_OK
            )

        # Calculate distributions
        sentence_types = {}
        parties = {}
        risk_levels = {}

        for clause in clauses:
            # Sentence types
            st = clause.sentence_type or 'UNKNOWN'
            sentence_types[st] = sentence_types.get(st, 0) + 1

            # Parties
            party = clause.party or 'UNKNOWN'
            parties[party] = parties.get(party, 0) + 1

            # Risk levels
            rl = clause.risk_level or 'UNKNOWN'
            risk_levels[rl] = risk_levels.get(rl, 0) + 1

        # Get high-risk clauses
        high_risk_clauses = clauses.filter(risk_level='HIGH').values(
            'id', 'clause_name', 'sentence_type', 'party', 'risk_score',
            'financial_impact', 'keywords'
        )[:10]

        return Response({
            'contract_id': str(contract_id),
            'contract_name': contract.original_filename,
            'total_clauses': clauses.count(),
            'sentence_types': sentence_types,
            'parties': parties,
            'risk_levels': risk_levels,
            'high_risk_clauses': list(high_risk_clauses)
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Failed to get RRIE analysis: {e}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def explain_clause(request):
    """
    Generate LLM-powered explanation for a clause (RRIE Feature).

    Request body:
        {
            "clause_id": "uuid",
            "clause_text": "text" (optional if clause_id provided)
        }

    URL: POST /api/rrie/explain
    """
    try:
        clause_id = request.data.get('clause_id')
        clause_text = request.data.get('clause_text')

        # Fetch from database if clause_id provided
        if clause_id:
            try:
                clause = Clause.objects.get(id=clause_id, contract__user=request.user)
                clause_text = clause.extracted_text
                sentence_type = clause.sentence_type
                party = clause.party
                risk_score = clause.risk_score
                keywords = clause.keywords

                # DEBUG: Log what text we're explaining
                logger.info(f"Explaining clause: {clause.clause_name}")
                logger.info(f"Clause text (first 200 chars): {clause_text[:200] if clause_text else 'EMPTY'}")
            except Clause.DoesNotExist:
                return Response(
                    {'error': 'Clause not found or access denied'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            if not clause_text:
                return Response(
                    {'error': 'Either clause_id or clause_text is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            sentence_type = request.data.get('sentence_type')
            party = request.data.get('party')
            risk_score = request.data.get('risk_score')
            keywords = request.data.get('keywords', {})

        # Validate clause text
        if not clause_text or len(clause_text.strip()) < 10:
            return Response(
                {'error': 'Clause text too short or empty'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Call explanation service
        explainer = get_clause_explainer()
        result = explainer.explain_clause(
            clause_text=clause_text,
            sentence_type=sentence_type,
            party=party,
            risk_score=risk_score,
            keywords=keywords
        )

        if not result.get('success'):
            # LLM unavailable — build rule-based fallback explanation
            risk_level = 'HIGH' if float(risk_score or 0) >= 0.7 else 'MEDIUM' if float(risk_score or 0) >= 0.4 else 'LOW'
            kw_list = ', '.join(list((keywords or {}).keys())[:5]) or 'none detected'
            party_str = party or 'Unknown party'
            st_str = sentence_type or 'clause'
            text_preview = clause_text[:300].strip()

            meaning_map = {
                'OBLIGATION': f'This clause establishes a binding obligation for {party_str}. It defines specific duties or actions that must be performed under the contract.',
                'RISK': f'This clause introduces contractual risk for {party_str}. It defines conditions, liabilities or consequences that may negatively impact the party.',
                'RIGHT': f'This clause grants a right or entitlement to {party_str}. It defines what the party is permitted or entitled to do under the contract.',
                'DEFINITION': f'This clause provides definitional context for the contract. It establishes the meaning of key terms used in the agreement.',
                'HEADING': f'This is a structural heading that organizes the contract into sections.',
            }
            risk_map = {
                'HIGH': f'Risk level is HIGH. Key risk keywords detected: {kw_list}. This clause may expose {party_str} to significant legal or financial liability.',
                'MEDIUM': f'Risk level is MEDIUM. Detected keywords ({kw_list}) suggest moderate exposure. Review terms carefully.',
                'LOW': f'Risk level is LOW. The clause presents limited risk based on keyword analysis ({kw_list}).',
            }
            impact_map = {
                'OBLIGATION': f'Failure to meet the obligations in this clause could result in breach of contract, triggering liability for {party_str}.',
                'RISK': f'This risk clause could result in financial penalties, indemnification claims, or contract termination if the risk event occurs.',
                'RIGHT': f'Exercising this right may have implications for the counterparty. Ensure conditions for exercising the right are clearly understood.',
            }
            mitigation_map = {
                'HIGH': 'Review with legal counsel before signing. Negotiate a liability cap or mutual obligation. Add force majeure or carve-out provisions.',
                'MEDIUM': 'Clarify ambiguous terms. Consider adding a notice period or cure right. Ensure indemnification scope is limited.',
                'LOW': 'Standard review recommended. Confirm definitions align with intended meaning.',
            }

            result = {
                'success': True,
                'meaning': meaning_map.get(st_str, f'This {st_str} clause involves {party_str} and covers: "{text_preview[:150]}..."'),
                'risk_explanation': risk_map.get(risk_level, f'Risk analysis: {risk_level} level based on detected keywords: {kw_list}.'),
                'impact': impact_map.get(st_str, f'This clause has a {risk_level} impact on {party_str}\'s contractual position.'),
                'mitigation': mitigation_map.get(risk_level, 'Seek legal review for appropriate mitigation.'),
                'metadata': {
                    'sentence_type': sentence_type,
                    'party': party,
                    'risk_score': float(risk_score or 0),
                    'risk_level': risk_level,
                },
                'llm_used': False,
            }

        return Response(result, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Clause explanation failed: {e}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_risk_breakdown(request, clause_id):
    """
    Get detailed risk breakdown for a clause (RRIE Explainability).

    Shows:
    - Keyword contributions
    - Risk score breakdown
    - Financial impact

    URL: GET /api/rrie/clauses/{clause_id}/risk-breakdown
    """
    try:
        # Fetch clause
        try:
            clause = Clause.objects.get(id=clause_id, contract__user=request.user)
        except Clause.DoesNotExist:
            return Response(
                {'error': 'Clause not found or access denied'},
                status=status.HTTP_404_NOT_FOUND
            )

        clause_text = clause.extracted_text

        if not clause_text or len(clause_text.strip()) < 10:
            return Response(
                {
                    'success': True,
                    'clause_id': str(clause.id),
                    'clause_name': clause.clause_name,
                    'total_score': 0,
                    'normalized_score': 0.0,
                    'risk_level': 'LOW',
                    'keyword_contributions': [],
                    'financial_impact': {'amount': 0.0, 'formatted': '₹0.00'},
                    'explanation': 'Clause text too short for risk analysis'
                },
                status=status.HTTP_200_OK
            )

        # Use stored keywords if available (fast path)
        if clause.keywords and isinstance(clause.keywords, dict) and len(clause.keywords) > 0:
            total_score = sum(clause.keywords.values())
            keyword_contributions = []

            for keyword, weight in sorted(clause.keywords.items(), key=lambda x: x[1], reverse=True):
                contribution_pct = (weight / total_score * 100) if total_score > 0 else 0
                keyword_contributions.append({
                    'keyword': keyword,
                    'weight': weight,
                    'contribution_pct': round(contribution_pct, 1)
                })

            normalized_score = clause.risk_score if clause.risk_score else min(total_score / 30.0, 1.0)
            risk_level = clause.risk_level if clause.risk_level else (
                'HIGH' if normalized_score >= 0.7 else 'MEDIUM' if normalized_score >= 0.4 else 'LOW'
            )

            scorer = get_risk_scorer()
            financial_impact = scorer.calculate_financial_impact(normalized_score)

            if keyword_contributions:
                top_contributors = keyword_contributions[:3]
                explanation_parts = [f"{kw['keyword']} ({kw['contribution_pct']}%)" for kw in top_contributors]
                explanation = f"Risk driven by {', '.join(explanation_parts)}"
            else:
                explanation = "No risk keywords detected"

            breakdown = {
                'success': True,
                'clause_id': str(clause.id),
                'clause_name': clause.clause_name,
                'total_score': total_score,
                'normalized_score': round(normalized_score, 3),
                'risk_level': risk_level,
                'keyword_contributions': keyword_contributions,
                'financial_impact': financial_impact,
                'explanation': explanation
            }
        else:
            # Recompute from text
            scorer = get_risk_scorer()
            breakdown = scorer.get_risk_breakdown(clause_text)
            breakdown['clause_id'] = str(clause.id)
            breakdown['clause_name'] = clause.clause_name

        return Response(breakdown, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Risk breakdown failed: {e}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_clause_table(request, contract_id):
    """
    GET /api/rrie/contracts/<contract_id>/clauses
    Full clause intelligence table: type + party + risk + financial impact per clause.
    """
    try:
        contract = Contract.objects.get(id=contract_id, user=request.user)
        clauses = Clause.objects.filter(contract=contract).exclude(
            extracted_text__isnull=True
        ).exclude(extracted_text='')

        rows = []
        for c in clauses:
            rows.append({
                'id': str(c.id),
                'clause_name': c.clause_name or '',
                'clause_type': c.clause_type or '',
                'sentence_type': c.sentence_type or 'UNCLASSIFIED',
                'party': c.party or 'UNKNOWN',
                'risk_score': round(float(c.risk_score or 0), 4),
                'risk_level': c.risk_level or 'LOW',
                'financial_impact': round(float(c.financial_impact or 0), 2),
                'keywords': c.keywords or {},
                'text_preview': (c.extracted_text or '')[:200],
            })

        rows.sort(key=lambda x: x['risk_score'], reverse=True)
        return Response({'clauses': rows, 'total': len(rows)})
    except Contract.DoesNotExist:
        return Response({'error': 'Contract not found'}, status=404)
    except Exception as e:
        logger.error(f"Clause table failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_risk_heatmap(request, contract_id):
    """
    GET /api/rrie/contracts/<contract_id>/heatmap
    Risk Heatmap: Clause Type × Party matrix, value = avg risk score.
    """
    try:
        contract = Contract.objects.get(id=contract_id, user=request.user)
        clauses = Clause.objects.filter(
            contract=contract,
            sentence_type__isnull=False,
            party__isnull=False,
        ).exclude(sentence_type='').exclude(party='')

        # Build matrix
        matrix = {}
        sentence_types = set()
        parties = set()

        for c in clauses:
            st = c.sentence_type or 'UNKNOWN'
            pt = c.party or 'UNKNOWN'
            risk = float(c.risk_score or 0)
            sentence_types.add(st)
            parties.add(pt)
            key = (st, pt)
            if key not in matrix:
                matrix[key] = {'scores': [], 'count': 0}
            matrix[key]['scores'].append(risk)
            matrix[key]['count'] += 1

        sentence_types = sorted(sentence_types)
        parties = sorted(parties)

        rows = []
        for st in sentence_types:
            row = {'sentence_type': st, 'values': []}
            for pt in parties:
                key = (st, pt)
                if key in matrix:
                    avg_risk = sum(matrix[key]['scores']) / len(matrix[key]['scores'])
                    row['values'].append({
                        'party': pt,
                        'avg_risk': round(avg_risk, 4),
                        'count': matrix[key]['count'],
                        'risk_level': 'HIGH' if avg_risk >= 0.7 else 'MEDIUM' if avg_risk >= 0.4 else 'LOW',
                    })
                else:
                    row['values'].append({'party': pt, 'avg_risk': 0, 'count': 0, 'risk_level': 'LOW'})
            rows.append(row)

        return Response({
            'sentence_types': sentence_types,
            'parties': parties,
            'rows': rows,
        })
    except Contract.DoesNotExist:
        return Response({'error': 'Contract not found'}, status=404)
    except Exception as e:
        logger.error(f"Risk heatmap failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ai_insights(request, contract_id):
    """
    GET /api/rrie/contracts/<contract_id>/insights
    AI Insights: top risks, unbalanced liabilities, hidden clauses, GraphRAG queries.
    """
    try:
        contract = Contract.objects.get(id=contract_id, user=request.user)
        clauses = Clause.objects.filter(contract=contract)

        all_clauses = list(clauses)
        total = len(all_clauses)
        if total == 0:
            return Response({'error': 'No clauses. Process contract with RRIE first.'}, status=400)

        # 1. Top 10 risk clauses
        top_risks = sorted(
            [c for c in all_clauses if c.risk_score],
            key=lambda x: float(x.risk_score or 0), reverse=True
        )[:10]

        top_risk_list = [{
            'id': str(c.id),
            'clause_name': c.clause_name,
            'sentence_type': c.sentence_type,
            'party': c.party,
            'risk_score': round(float(c.risk_score or 0), 4),
            'risk_level': c.risk_level,
            'financial_impact': round(float(c.financial_impact or 0), 2),
            'keywords': list((c.keywords or {}).keys())[:5],
        } for c in top_risks]

        # 2. Unbalanced liabilities (contractor bears much more risk than employer)
        contractor_risk = sum(float(c.risk_score or 0) for c in all_clauses if c.party == 'CONTRACTOR')
        employer_risk = sum(float(c.risk_score or 0) for c in all_clauses if c.party == 'EMPLOYER')
        shared_risk = sum(float(c.risk_score or 0) for c in all_clauses if c.party == 'SHARED')
        total_risk = contractor_risk + employer_risk + shared_risk or 1

        contractor_pct = round(contractor_risk / total_risk * 100, 1)
        employer_pct = round(employer_risk / total_risk * 100, 1)
        shared_pct = round(shared_risk / total_risk * 100, 1)
        imbalance = abs(contractor_pct - employer_pct)

        unbalanced_clauses = [c for c in all_clauses
                              if c.party == 'CONTRACTOR' and float(c.risk_score or 0) >= 0.6][:5]

        # 3. Hidden clauses (high risk but sentence_type = DEFINITION or HEADING — often overlooked)
        hidden = [c for c in all_clauses
                  if c.sentence_type in ('DEFINITION', 'HEADING')
                  and float(c.risk_score or 0) >= 0.5][:5]

        # 4. GraphRAG-style queries using MySQL
        from django.db.models import Avg, Count, Q
        # Contractor-only risks
        contractor_risks = clauses.filter(party='CONTRACTOR', risk_level='HIGH').values(
            'id', 'clause_name', 'risk_score', 'sentence_type'
        )[:5]

        # Shared liabilities
        shared_liabilities = clauses.filter(party='SHARED').values(
            'id', 'clause_name', 'risk_score', 'clause_type'
        )[:5]

        # Cascading risks: obligation clauses that also have high risk
        cascading = clauses.filter(
            sentence_type='OBLIGATION', risk_level='HIGH'
        ).values('id', 'clause_name', 'risk_score', 'party')[:5]

        return Response({
            'contract_id': str(contract_id),
            'contract_name': contract.original_filename,
            'total_clauses': total,
            'top_risks': top_risk_list,
            'liability_balance': {
                'contractor_pct': contractor_pct,
                'employer_pct': employer_pct,
                'shared_pct': shared_pct,
                'imbalance': imbalance,
                'verdict': 'HIGHLY UNBALANCED' if imbalance > 40 else 'MODERATELY UNBALANCED' if imbalance > 20 else 'BALANCED',
                'unbalanced_clauses': [{
                    'id': str(c.id),
                    'clause_name': c.clause_name,
                    'risk_score': round(float(c.risk_score or 0), 4),
                } for c in unbalanced_clauses],
            },
            'hidden_risk_clauses': [{
                'id': str(c.id),
                'clause_name': c.clause_name,
                'sentence_type': c.sentence_type,
                'risk_score': round(float(c.risk_score or 0), 4),
                'text_preview': (c.extracted_text or '')[:150],
            } for c in hidden],
            'graph_queries': {
                'contractor_risks': list(contractor_risks),
                'shared_liabilities': list(shared_liabilities),
                'cascading_obligations': list(cascading),
            },
        })
    except Contract.DoesNotExist:
        return Response({'error': 'Contract not found'}, status=404)
    except Exception as e:
        logger.error(f"AI insights failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_deal_score(request, contract_id):
    """
    GET /api/rrie/contracts/<contract_id>/deal-score
    Deal Scoring Engine: GO / NEGOTIATE / NO-GO with score and LLM reasoning.
    """
    import requests as req
    from django.conf import settings

    try:
        contract = Contract.objects.get(id=contract_id, user=request.user)
        clauses = list(Clause.objects.filter(contract=contract))
        total = len(clauses)

        if total == 0:
            return Response({'error': 'No clauses. Process contract with RRIE first.'}, status=400)

        # Compute deal score per spec:
        # Score = 100 - risk_score + (employer_risk - contractor_risk) balance
        risk_scores = [float(c.risk_score or 0) for c in clauses]
        total_risk = sum(risk_scores)
        avg_risk = total_risk / total if total else 0

        contractor_risk = sum(float(c.risk_score or 0) for c in clauses if c.party == 'CONTRACTOR')
        employer_risk = sum(float(c.risk_score or 0) for c in clauses if c.party == 'EMPLOYER')
        balance = employer_risk - contractor_risk  # positive = employer takes more risk (good for contractor)

        high_risk_count = sum(1 for c in clauses if c.risk_level == 'HIGH')
        high_risk_pct = high_risk_count / total * 100 if total else 0

        obligation_count = sum(1 for c in clauses if c.sentence_type == 'OBLIGATION')
        right_count = sum(1 for c in clauses if c.sentence_type == 'RIGHT')
        rights_ratio = right_count / max(obligation_count, 1)

        # Score formula
        raw_score = 100 - (avg_risk * 100) + (balance * 5) + (rights_ratio * 10) - (high_risk_pct * 0.5)
        deal_score = max(0, min(100, round(raw_score, 1)))

        if deal_score > 70:
            decision = 'GO'
            decision_color = 'green'
            summary = 'Contract terms are favorable. Risk is manageable.'
        elif deal_score > 40:
            decision = 'NEGOTIATE'
            decision_color = 'yellow'
            summary = 'Contract has significant risks. Negotiate key clauses before signing.'
        else:
            decision = 'NO-GO'
            decision_color = 'red'
            summary = 'Contract is heavily risky. Recommend rejection or major renegotiation.'

        # Top reasons
        reasons = []
        if high_risk_pct > 30:
            reasons.append(f'{high_risk_pct:.0f}% of clauses are HIGH risk')
        if contractor_risk > employer_risk * 1.5:
            reasons.append('Contractor bears disproportionate risk vs Employer')
        if rights_ratio < 0.3:
            reasons.append('Very few Rights clauses relative to Obligations')
        if avg_risk > 0.6:
            reasons.append(f'Average risk score is very high ({avg_risk*100:.0f}%)')
        if balance > 0:
            reasons.append('Employer carries more risk — favorable for contractor')
        if not reasons:
            reasons.append('Risk distribution is balanced across parties')

        # LLM reasoning (Qwen)
        llm_reasoning = ''
        try:
            top_risks = sorted(clauses, key=lambda x: float(x.risk_score or 0), reverse=True)[:3]
            risk_summary = '; '.join([f"{c.clause_name} ({c.risk_level})" for c in top_risks])
            prompt = (
                f"You are a contract risk expert. Analyze this contract deal:\n"
                f"Deal Score: {deal_score}/100 — Decision: {decision}\n"
                f"Total Clauses: {total}, High Risk: {high_risk_count}, Avg Risk: {avg_risk*100:.0f}%\n"
                f"Top Risk Clauses: {risk_summary}\n\n"
                f"Give a 2-3 sentence business recommendation. Be direct and specific."
            )
            resp = req.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={"model": getattr(settings, 'OLLAMA_MODEL', 'qwen2.5:7b'), "prompt": prompt, "stream": False},
                timeout=20,
            )
            llm_reasoning = resp.json().get('response', '').strip()
        except Exception:
            llm_reasoning = summary

        return Response({
            'contract_id': str(contract_id),
            'contract_name': contract.original_filename,
            'deal_score': deal_score,
            'decision': decision,
            'decision_color': decision_color,
            'summary': summary,
            'llm_reasoning': llm_reasoning,
            'reasons': reasons,
            'metrics': {
                'total_clauses': total,
                'avg_risk_pct': round(avg_risk * 100, 1),
                'high_risk_count': high_risk_count,
                'high_risk_pct': round(high_risk_pct, 1),
                'contractor_risk': round(contractor_risk, 3),
                'employer_risk': round(employer_risk, 3),
                'rights_ratio': round(rights_ratio, 2),
                'balance_score': round(balance, 3),
            }
        })
    except Contract.DoesNotExist:
        return Response({'error': 'Contract not found'}, status=404)
    except Exception as e:
        logger.error(f"Deal score failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_contract_graph(request, contract_id):
    """
    GET /api/rrie/contracts/<contract_id>/graph
    Returns clause-risk-party graph for React Flow visualization.
    Nodes: Contract, Clause, Risk, Party
    Edges: belongs_to, has_risk, affects
    """
    try:
        contract = Contract.objects.get(id=contract_id, user=request.user)
        clauses = list(Clause.objects.filter(contract=contract))

        if not clauses:
            return Response({'error': 'No clauses. Process contract with RRIE first.'}, status=400)

        nodes = []
        edges = []
        seen_parties = set()
        seen_risk_levels = set()

        # Contract node (center)
        contract_node_id = f"contract-{contract_id}"
        nodes.append({
            'id': contract_node_id,
            'type': 'contractNode',
            'data': {
                'label': contract.original_filename or 'Contract',
                'type': 'CONTRACT',
                'clause_count': len(clauses),
            },
            'position': {'x': 600, 'y': 50},
        })

        # Party nodes — horizontal spread
        n_clauses = len(clauses)
        spread = max(1200, n_clauses * 100)
        party_positions = {
            'CONTRACTOR': {'x': spread * 0.1, 'y': 350},
            'EMPLOYER':   {'x': spread * 0.5, 'y': 350},
            'SHARED':     {'x': spread * 0.9, 'y': 350},
        }
        party_colors = {'CONTRACTOR': '#3b82f6', 'EMPLOYER': '#8b5cf6', 'SHARED': '#06b6d4'}
        for party, pos in party_positions.items():
            party_count = sum(1 for c in clauses if (c.party or 'SHARED') == party)
            nodes.append({
                'id': f"party-{party}",
                'type': 'partyNode',
                'data': {'label': party, 'type': 'PARTY', 'count': party_count},
                'position': pos,
            })
            pc = party_colors[party]
            edges.append({
                'id': f"e-contract-{party}",
                'source': contract_node_id,
                'target': f"party-{party}",
                'label': 'has_party',
                'type': 'smoothstep',
                'animated': False,
                'labelStyle': {'fill': '#64748b', 'fontSize': 9},
                'labelBgStyle': {'fill': 'rgba(8,13,26,0.8)'},
                'markerEnd': {'type': 'arrowclosed', 'color': pc, 'width': 12, 'height': 12},
                'style': {'stroke': pc, 'strokeWidth': 1.5, 'strokeDasharray': '6 3', 'opacity': 0.5},
            })

        # Risk level nodes
        risk_positions = {
            'HIGH':   {'x': spread * 0.1, 'y': 650},
            'MEDIUM': {'x': spread * 0.5, 'y': 650},
            'LOW':    {'x': spread * 0.9, 'y': 650},
        }
        risk_colors = {'HIGH': '#ef4444', 'MEDIUM': '#f59e0b', 'LOW': '#10b981'}
        for level, pos in risk_positions.items():
            count = sum(1 for c in clauses if (c.risk_level or 'LOW') == level)
            nodes.append({
                'id': f"risk-{level}",
                'type': 'riskNode',
                'data': {'label': f"{level} RISK", 'type': 'RISK', 'count': count, 'color': risk_colors[level]},
                'position': pos,
            })

        # Clause nodes — arrange in a staggered grid
        cols = min(5, max(3, n_clauses // 3 + 1))
        gap_x = max(240, spread // cols)
        gap_y = 200
        base_x = (spread - (cols - 1) * gap_x) / 2
        base_y = 950

        for idx, clause in enumerate(clauses):
            row = idx // cols
            col = idx % cols
            # stagger odd rows
            stagger = gap_x / 2 if row % 2 == 1 else 0
            x = base_x + col * gap_x + stagger
            y = base_y + row * gap_y

            party = clause.party or 'SHARED'
            risk_level = clause.risk_level or 'LOW'
            risk_score = float(clause.risk_score or 0)
            sentence_type = clause.sentence_type or 'DEFINITION'
            rc = risk_colors[risk_level]
            pc = party_colors.get(party, '#06b6d4')

            clause_node_id = f"clause-{clause.id}"
            nodes.append({
                'id': clause_node_id,
                'type': 'clauseNode',
                'data': {
                    'label': clause.clause_name or f'Clause {idx+1}',
                    'type': 'CLAUSE',
                    'sentence_type': sentence_type,
                    'party': party,
                    'risk_level': risk_level,
                    'risk_score': round(risk_score * 100, 1),
                    'financial_impact': round(risk_score * 50000),
                    'clause_type': clause.clause_type or '',
                },
                'position': {'x': x, 'y': y},
            })

            # Edge: contract → clause (belongs_to) — faint dashed
            edges.append({
                'id': f"e-{contract_node_id}-{clause_node_id}",
                'source': contract_node_id,
                'target': clause_node_id,
                'label': 'belongs_to',
                'type': 'smoothstep',
                'animated': False,
                'labelStyle': {'fill': '#334155', 'fontSize': 8},
                'labelBgStyle': {'fill': 'rgba(8,13,26,0.7)'},
                'style': {'stroke': '#1e293b', 'strokeWidth': 1, 'strokeDasharray': '4 4'},
            })

            # Edge: clause → party (affects) — colored by party
            edges.append({
                'id': f"e-{clause_node_id}-party-{party}",
                'source': clause_node_id,
                'target': f"party-{party}",
                'label': 'affects',
                'type': 'smoothstep',
                'animated': risk_level == 'HIGH',
                'labelStyle': {'fill': pc, 'fontSize': 8},
                'labelBgStyle': {'fill': 'rgba(8,13,26,0.8)'},
                'markerEnd': {'type': 'arrowclosed', 'color': pc, 'width': 10, 'height': 10},
                'style': {'stroke': pc, 'strokeWidth': 1.5 if risk_level == 'HIGH' else 1, 'opacity': 0.7},
            })

            # Edge: clause → risk level (has_risk) — colored by risk
            edges.append({
                'id': f"e-{clause_node_id}-risk-{risk_level}",
                'source': clause_node_id,
                'target': f"risk-{risk_level}",
                'label': 'has_risk',
                'type': 'smoothstep',
                'animated': risk_level == 'HIGH',
                'labelStyle': {'fill': rc, 'fontSize': 8},
                'labelBgStyle': {'fill': 'rgba(8,13,26,0.8)'},
                'markerEnd': {'type': 'arrowclosed', 'color': rc, 'width': 10, 'height': 10},
                'style': {
                    'stroke': rc,
                    'strokeWidth': 2.5 if risk_level == 'HIGH' else 1.5 if risk_level == 'MEDIUM' else 1,
                    'opacity': 0.8 if risk_level == 'HIGH' else 0.55,
                },
            })

        return Response({
            'success': True,
            'contract_id': str(contract_id),
            'contract_name': contract.original_filename,
            'nodes': nodes,
            'edges': edges,
            'stats': {
                'total_clauses': len(clauses),
                'total_nodes': len(nodes),
                'total_edges': len(edges),
            }
        })

    except Contract.DoesNotExist:
        return Response({'error': 'Contract not found'}, status=404)
    except Exception as e:
        logger.error(f"Graph view failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=500)


# ── RL Actions & reward weights ─────────────────────────────────────────────
_RL_ACTIONS = ['accept', 'reject', 'modify_clause', 'add_cap', 'share_risk', 'delay_penalty_reduction']

_ACTION_REWARDS = {
    # (action, risk_level) → reward
    ('accept',                  'LOW'):    15,
    ('accept',                  'MEDIUM'): -5,
    ('accept',                  'HIGH'):  -20,
    ('reject',                  'LOW'):   -10,
    ('reject',                  'MEDIUM'):  5,
    ('reject',                  'HIGH'):   10,
    ('modify_clause',           'LOW'):    10,
    ('modify_clause',           'MEDIUM'): 18,
    ('modify_clause',           'HIGH'):   15,
    ('add_cap',                 'LOW'):     8,
    ('add_cap',                 'MEDIUM'): 20,
    ('add_cap',                 'HIGH'):   25,
    ('share_risk',              'LOW'):     5,
    ('share_risk',              'MEDIUM'): 15,
    ('share_risk',              'HIGH'):   18,
    ('delay_penalty_reduction', 'LOW'):     3,
    ('delay_penalty_reduction', 'MEDIUM'): 12,
    ('delay_penalty_reduction', 'HIGH'):   22,
}

_ACTION_LABELS = {
    'accept': 'Accept As-Is',
    'reject': 'Reject Clause',
    'modify_clause': 'Modify Clause',
    'add_cap': 'Add Liability Cap',
    'share_risk': 'Share Risk',
    'delay_penalty_reduction': 'Reduce Delay Penalty',
}

_ACTION_DESCRIPTIONS = {
    'accept': 'Risk is acceptable. Proceed with clause as written.',
    'reject': 'Clause poses unacceptable risk. Reject or remove entirely.',
    'modify_clause': 'Rewrite clause to reduce exposure while preserving intent.',
    'add_cap': 'Insert maximum liability cap (e.g. 10% of contract value).',
    'share_risk': 'Redistribute risk equally between contractor and employer.',
    'delay_penalty_reduction': 'Cap or reduce delay penalty to industry standard rate.',
}


def _rl_recommend(clause, n_sim=500):
    """
    Q-Learning simulation to recommend best action for a clause.
    Returns ranked actions with Q-values and confidence scores.
    """
    import random, math

    risk_level = clause.risk_level or 'LOW'
    risk_score = float(clause.risk_score or 0)
    party = clause.party or 'SHARED'
    sentence_type = clause.sentence_type or 'DEFINITION'

    # Q-table
    q = {a: 0.0 for a in _RL_ACTIONS}
    alpha = 0.15   # learning rate
    gamma = 0.9    # discount
    epsilon = 0.3  # exploration

    for episode in range(n_sim):
        # Epsilon-greedy action selection
        if random.random() < epsilon:
            action = random.choice(_RL_ACTIONS)
        else:
            action = max(q, key=q.get)

        # Base reward from lookup
        base_reward = _ACTION_REWARDS.get((action, risk_level), 0)

        # Adjust by risk_score (higher risk → riskier actions get more reward)
        adjustment = risk_score * 10
        if action in ('add_cap', 'modify_clause', 'delay_penalty_reduction'):
            reward = base_reward + adjustment
        elif action == 'accept':
            reward = base_reward - adjustment
        elif action == 'reject':
            reward = base_reward + (adjustment * 0.5 if risk_level == 'HIGH' else -adjustment * 0.5)
        else:
            reward = base_reward

        # Party adjustment: contractor bears more risk → aggressive actions get bonus
        if party == 'CONTRACTOR' and action in ('add_cap', 'share_risk', 'modify_clause'):
            reward += 5
        elif party == 'EMPLOYER' and action == 'reject':
            reward -= 5

        # Sentence type adjustment
        if sentence_type == 'OBLIGATION' and action == 'modify_clause':
            reward += 3
        if sentence_type == 'RISK' and action in ('add_cap', 'share_risk'):
            reward += 4

        # Q-update (next state = same state, done=True)
        max_next = max(q.values())
        q[action] = q[action] + alpha * (reward + gamma * max_next - q[action])

        # Decay epsilon
        epsilon = max(0.05, epsilon * 0.997)

    # Convert Q-values to probabilities using softmax for realistic confidence scores
    import math

    # Apply softmax with temperature to get probabilities
    temperature = 2.5  # Higher = softer distribution, more realistic confidence scores

    # Numerical stability: subtract max Q-value before exp to prevent overflow
    q_vals = list(q.values())
    max_q = max(q_vals)

    exp_q = {action: math.exp((q_val - max_q) / temperature) for action, q_val in q.items()}
    sum_exp = sum(exp_q.values())
    probabilities = {action: exp_val / sum_exp for action, exp_val in exp_q.items()}

    ranked = sorted(q.items(), key=lambda x: x[1], reverse=True)
    results = []
    for action, q_val in ranked:
        # Confidence = softmax probability as percentage
        confidence = round(probabilities[action] * 100, 1)
        results.append({
            'action': action,
            'label': _ACTION_LABELS[action],
            'description': _ACTION_DESCRIPTIONS[action],
            'q_value': round(q_val, 3),
            'confidence': confidence,
            'reward': _ACTION_REWARDS.get((action, risk_level), 0),
        })

    return results


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_rl_negotiation(request, contract_id):
    """
    GET /api/rrie/contracts/<contract_id>/rl-negotiation
    RL-based negotiation recommendations for every clause.
    Returns per-clause recommended action with confidence scores.
    """
    import requests as req
    from django.conf import settings

    try:
        contract = Contract.objects.get(id=contract_id, user=request.user)
        clauses = list(Clause.objects.filter(contract=contract))

        if not clauses:
            return Response({'error': 'No clauses. Process contract with RRIE first.'}, status=400)

        n_sim = int(request.query_params.get('simulations', 500))
        n_sim = min(max(n_sim, 100), 2000)  # clamp 100–2000

        clause_recommendations = []
        action_summary = {a: 0 for a in _RL_ACTIONS}

        # Contract-level multiplier (different for each contract)
        import hashlib
        contract_hash = int(hashlib.md5(str(contract.id).encode()).hexdigest()[:8], 16)
        contract_multiplier = 0.7 + ((contract_hash % 60) / 100)  # Range: 0.7 to 1.3

        # Contract size multiplier (more clauses = higher financial stakes)
        contract_size_mult = min(1.5, 0.8 + (len(clauses) / 50))  # More clauses = higher multiplier

        for clause in clauses:
            ranked = _rl_recommend(clause, n_sim=n_sim)
            best = ranked[0]
            action_summary[best['action']] += 1

            # Enhanced financial impact calculation with multiple factors
            risk_score = float(clause.risk_score or 0)
            sentence_type = clause.sentence_type or 'DEFINITION'
            party = clause.party or 'SHARED'
            risk_level = clause.risk_level or 'LOW'

            # Base impact (higher base for more variation)
            base_impact = risk_score * 100000

            # Sentence type multiplier
            type_multipliers = {
                'RISK': 1.8,
                'OBLIGATION': 1.5,
                'RIGHT': 0.6,
                'DEFINITION': 0.4,
                'CONDITION': 1.2,
                'TIMELINE': 0.9,
                'PAYMENT': 2.0
            }
            type_mult = type_multipliers.get(sentence_type, 1.0)

            # Party attribution multiplier (contractor risk = higher financial impact)
            party_multipliers = {
                'CONTRACTOR': 1.4,
                'EMPLOYER': 0.6,
                'SHARED': 1.0
            }
            party_mult = party_multipliers.get(party, 1.0)

            # Risk level multiplier
            risk_multipliers = {
                'HIGH': 1.6,
                'MEDIUM': 1.0,
                'LOW': 0.5
            }
            risk_mult = risk_multipliers.get(risk_level, 1.0)

            # Calculate final financial impact with contract-specific factors
            financial_impact = base_impact * type_mult * party_mult * risk_mult

            # Apply contract-level multipliers (makes each contract unique)
            financial_impact = financial_impact * contract_multiplier * contract_size_mult

            # Add clause-specific variation based on clause ID
            if financial_impact > 0:
                clause_hash = int(hashlib.md5((clause.clause_name or '' + str(clause.id)).encode()).hexdigest()[:8], 16)
                variation = 1.0 + ((clause_hash % 20) - 10) / 100  # ±10% variation
                financial_impact = financial_impact * variation

            financial_impact = max(round(financial_impact), 5000)  # Minimum ₹5,000

            clause_recommendations.append({
                'id': str(clause.id),
                'clause_name': clause.clause_name or 'Unnamed',
                'clause_type': clause.clause_type or '',
                'sentence_type': sentence_type,
                'party': party,
                'risk_level': risk_level,
                'risk_score': round(risk_score * 100, 1),
                'financial_impact': financial_impact,
                'best_action': best['action'],
                'best_label': best['label'],
                'best_description': best['description'],
                'confidence': best['confidence'],
                'all_actions': ranked,
            })

        # Sort by risk_score desc
        clause_recommendations.sort(key=lambda x: x['risk_score'], reverse=True)

        # Portfolio strategy summary
        total = len(clauses)
        accept_pct = round(action_summary['accept'] / total * 100)
        negotiate_pct = round((action_summary['modify_clause'] + action_summary['add_cap'] +
                                action_summary['share_risk'] + action_summary['delay_penalty_reduction']) / total * 100)
        reject_pct = round(action_summary['reject'] / total * 100)

        if reject_pct > 30:
            portfolio_verdict = 'HIGH RISK — Many clauses should be rejected'
        elif negotiate_pct > 50:
            portfolio_verdict = 'NEGOTIATE — Significant clauses need modification'
        elif accept_pct > 70:
            portfolio_verdict = 'FAVORABLE — Most clauses are acceptable'
        else:
            portfolio_verdict = 'MIXED — Selective negotiation recommended'

        return Response({
            'success': True,
            'contract_id': str(contract_id),
            'contract_name': contract.original_filename,
            'simulations_run': n_sim,
            'total_clauses': total,
            'portfolio_verdict': portfolio_verdict,
            'action_summary': action_summary,
            'accept_pct': accept_pct,
            'negotiate_pct': negotiate_pct,
            'reject_pct': reject_pct,
            'clauses': clause_recommendations,
        })

    except Contract.DoesNotExist:
        return Response({'error': 'Contract not found'}, status=404)
    except Exception as e:
        logger.error(f"RL negotiation failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=500)
