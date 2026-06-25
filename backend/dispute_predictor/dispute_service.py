"""
Dispute Predictor Service
=========================
Full pipeline:
1. Contract text → clause segmentation + risk signal extraction (regex)
2. LegalBERT semantic embedding → amplifies risk signals semantically
3. Bayesian risk network inference (60-node)
4. GNN dispute scoring (reuses ArbitrationGNN / heuristic fallback)
5. BM25+BERT RAG — retrieves similar historical clauses
6. Qwen 2.5 explanation via Ollama (rule-based fallback)
7. Legal cost estimation (P50/P90)
"""

import logging
import re
import sys
import os
import numpy as np
import requests
from typing import Dict, Any, List, Optional, Tuple

from django.conf import settings

from .bayesian_engine import get_bayesian_engine

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# 1. CLAUSE RISK SIGNAL EXTRACTOR  (regex keyword patterns)
# ═══════════════════════════════════════════════════════════

RISK_SIGNAL_PATTERNS = {
    'ContractAmbiguity': [
        r'may\s+at\s+its\s+discretion', r'reasonable\s+efforts?', r'best\s+efforts?',
        r'as\s+appropriate', r'to\s+be\s+agreed', r'subject\s+to\s+mutual\s+agreement',
        r'commercially\s+reasonable', r'substantially\s+complian',
    ],
    'SupplierDelay': [
        r'delivery\s+schedule', r'milestone', r'completion\s+date',
        r'force\s+majeure', r'delay\s+in\s+delivery', r'late\s+delivery',
    ],
    'PaymentDefaultRisk': [
        r'payment\s+terms?', r'invoice', r'overdue', r'late\s+payment',
        r'interest\s+on\s+late', r'default\s+in\s+payment',
    ],
    'ContractCostOverrun': [
        r'lump\s+sum', r'fixed\s+price', r'cost\s+adjustment',
        r'price\s+escalation', r'variation\s+order', r'change\s+order',
    ],
    'LiabilityExposure': [
        r'indemnif', r'liability', r'consequential\s+damage',
        r'unlimited\s+liability', r'aggregate\s+liability',
        r'hold\s+harmless',
    ],
    'TerminationRisk': [
        r'terminat', r'cancell', r'breach\s+of\s+contract',
        r'material\s+breach', r'notice\s+of\s+termination',
    ],
    'SLAViolation': [
        r'service\s+level', r'SLA', r'key\s+performance\s+indicator',
        r'KPI', r'performance\s+standard', r'uptime',
    ],
    'ClauseConflict': [
        r'notwithstanding', r'except\s+as\s+provided', r'subject\s+to\s+clause',
        r'prevail\s+over', r'supersede',
    ],
    'RenegotiationRisk': [
        r'renegotiat', r'amendment', r'variation\s+to\s+this\s+agreement',
        r'modification\s+of\s+terms',
    ],
    'ScopeChangeRisk': [
        r'scope\s+of\s+work', r'change\s+of\s+scope', r'scope\s+change',
        r'additional\s+work', r'out\s+of\s+scope',
    ],
    'CommodityPriceShock': [
        r'commodity', r'raw\s+material', r'steel', r'copper', r'aluminium',
        r'oil\s+price', r'energy\s+cost',
    ],
    'CounterpartyCreditRisk': [
        r'credit\s+risk', r'financial\s+standing', r'creditworthiness',
        r'financial\s+stability', r'insolvency',
    ],
}

# Semantic risk phrases for LegalBERT similarity amplification
RISK_SEMANTIC_PHRASES = {
    'ContractAmbiguity':     'ambiguous contractual obligation unclear terms discretionary language',
    'SupplierDelay':         'supplier delivery delay milestone completion schedule failure',
    'PaymentDefaultRisk':    'payment default non-payment late payment financial obligation',
    'LiabilityExposure':     'unlimited liability indemnification consequential damages exposure',
    'TerminationRisk':       'contract termination breach material default cancellation',
    'CommodityPriceShock':   'commodity price increase raw material cost escalation',
    'ContractCostOverrun':   'cost overrun budget escalation variation order change order',
    'SLAViolation':          'service level agreement KPI performance standard violation',
    'CounterpartyCreditRisk':'counterparty credit risk insolvency financial instability',
    'RenegotiationRisk':     'contract renegotiation amendment modification commercial terms',
}


def extract_risk_signals_from_text(contract_text: str) -> Dict[str, float]:
    """
    Scan contract text with keyword regex → Bayesian evidence dict.
    Returns {node_id: probability (0–0.8)}.
    """
    text_lower = contract_text.lower()
    signals: Dict[str, float] = {}
    for node_id, patterns in RISK_SIGNAL_PATTERNS.items():
        matches = sum(1 for p in patterns if re.search(p, text_lower))
        if matches >= 3:
            signals[node_id] = 0.35
        elif matches == 2:
            signals[node_id] = 0.25
        elif matches == 1:
            signals[node_id] = 0.15
    return signals


# ═══════════════════════════════════════════════════════════
# 2. LEGALBERT SEMANTIC AMPLIFIER
# ═══════════════════════════════════════════════════════════

_legalbert_service = None

def _get_legalbert():
    global _legalbert_service
    if _legalbert_service is None:
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from arbitration.legalbert_service import LegalBERTEmbeddingService
            svc = LegalBERTEmbeddingService()
            # Cache the instance always — it's a singleton, model loads on __init__
            _legalbert_service = svc
        except Exception as e:
            logger.warning(f"LegalBERT unavailable: {e}")
            return None
    return _legalbert_service


def amplify_signals_with_legalbert(
    contract_text: str,
    base_signals: Dict[str, float],
) -> Tuple[Dict[str, float], Dict[str, Any]]:
    """
    Use LegalBERT cosine similarity to semantically amplify/confirm risk signals.
    For each risk category phrase, if semantic similarity > threshold,
    boost the signal strength by up to +0.15.

    Returns:
        amplified_signals: updated evidence dict
        legalbert_meta: {available, similarity_scores, amplified_nodes}
    """
    service = _get_legalbert()
    if not service or not service.is_available():
        return base_signals, {'available': False, 'amplified_nodes': []}

    # Truncate contract text to 512 tokens worth (~1800 chars)
    text_excerpt = contract_text[:1800]

    try:
        contract_emb = service.generate_embedding(text_excerpt)
        if contract_emb is None:
            return base_signals, {'available': False, 'amplified_nodes': []}

        amplified = dict(base_signals)
        similarity_scores = {}
        amplified_nodes = []

        for node_id, phrase in RISK_SEMANTIC_PHRASES.items():
            phrase_emb = service.generate_embedding(phrase)
            if phrase_emb is None:
                continue

            # Cosine similarity
            norm_c = np.linalg.norm(contract_emb)
            norm_p = np.linalg.norm(phrase_emb)
            if norm_c == 0 or norm_p == 0:
                continue
            sim = float(np.dot(contract_emb, phrase_emb) / (norm_c * norm_p))
            similarity_scores[node_id] = round(sim, 3)

            # Amplify: if similarity > 0.4, boost existing signal or set minimum
            if sim > 0.5:
                boost = min(0.15, (sim - 0.4) * 1.5)
                current = amplified.get(node_id, 0.0)
                amplified[node_id] = min(0.90, current + boost)
                amplified_nodes.append({
                    'node': node_id,
                    'similarity': round(sim, 3),
                    'boost': round(boost, 3),
                    'final_signal': round(amplified[node_id], 3),
                })
            elif sim > 0.35 and node_id not in amplified:
                # Low-confidence: add weak signal if not already present
                amplified[node_id] = 0.35

        return amplified, {
            'available': True,
            'similarity_scores': similarity_scores,
            'amplified_nodes': amplified_nodes,
        }

    except Exception as e:
        logger.warning(f"LegalBERT amplification failed: {e}")
        return base_signals, {'available': False, 'amplified_nodes': []}


# ═══════════════════════════════════════════════════════════
# 3. GNN DISPUTE SCORER
# ═══════════════════════════════════════════════════════════

_gnn_service = None

def _get_gnn():
    global _gnn_service
    if _gnn_service is None:
        try:
            from arbitration.gnn_model import GNNInferenceService
            _gnn_service = GNNInferenceService()
        except Exception as e:
            logger.warning(f"GNN service unavailable: {e}")
            _gnn_service = False
    return _gnn_service if _gnn_service else None


def _build_clause_graph_from_signals(
    signals: Dict[str, float],
    bayesian_posteriors: Dict[str, float],
) -> Tuple[List[List[float]], List[List[int]]]:
    """
    Build a clause-level graph for GNN input from Bayesian posteriors.

    Each "clause node" maps to one of the 8 risk layers.
    Node features: 8-dim risk vector derived from posteriors.
    Edges: sequential (layer i → layer i+1) + high-risk cross-edges.

    Returns:
        node_features: N × 8 list of float vectors
        edges: E × 2 list of [src, tgt] pairs
    """
    from .bayesian_engine import RISK_NODES

    # One representative node per risk cluster
    CLUSTER_REPRESENTATIVES = {
        'geo':          ['WarRisk', 'SanctionsRisk', 'PoliticalInstability'],
        'macro':        ['InflationRisk', 'CommodityPriceShock', 'EnergyPriceShock'],
        'market':       ['CompetitionIncrease', 'RegulatoryChange'],
        'supply_chain': ['SupplierDelay', 'TransportDisruption', 'InventoryShortage'],
        'financial':    ['CounterpartyCreditRisk', 'PaymentDefaultRisk', 'CashFlowStress'],
        'operational':  ['DeliveryFailure', 'SLAViolation', 'CostEscalation'],
        'contract':     ['ContractAmbiguity', 'ContractPerformanceRisk', 'ContractRisk'],
        'legal':        ['DisputeTrigger', 'DisputeEscalation', 'DisputeProbability'],
    }

    CLUSTER_ORDER = ['geo', 'macro', 'market', 'supply_chain', 'financial', 'operational', 'contract', 'legal']

    node_features = []
    node_cluster_idx = []

    for cluster_idx, cluster in enumerate(CLUSTER_ORDER):
        reps = CLUSTER_REPRESENTATIVES[cluster]
        cluster_probs = [bayesian_posteriors.get(r, 0.1) for r in reps]

        # 8-dim feature vector:
        # [mean_prob, max_prob, min_prob, std_prob, signal_count, layer_norm, geo_risk, legal_risk]
        mean_p = float(np.mean(cluster_probs))
        max_p = float(np.max(cluster_probs))
        min_p = float(np.min(cluster_probs))
        std_p = float(np.std(cluster_probs))
        sig_count = sum(1 for r in reps if signals.get(r, 0) > 0) / max(len(reps), 1)
        layer_norm = (cluster_idx + 1) / 8.0
        geo_risk = bayesian_posteriors.get('WarRisk', 0.05)
        legal_risk = bayesian_posteriors.get('DisputeProbability', 0.2)

        node_features.append([mean_p, max_p, min_p, std_p, sig_count, layer_norm, geo_risk, legal_risk])
        node_cluster_idx.append(cluster_idx)

    # Build edges: sequential + cross-layer for high-risk pairs
    edges = []
    n = len(node_features)

    # Sequential edges (layer chain)
    for i in range(n - 1):
        edges.append([i, i + 1])

    # Cross edges: geo→supply_chain, macro→financial, supply_chain→contract, financial→legal
    cross = [(0, 3), (1, 4), (3, 6), (4, 7), (6, 7)]
    for src, tgt in cross:
        if src < n and tgt < n:
            edges.append([src, tgt])

    return node_features, edges


def score_with_gnn(
    signals: Dict[str, float],
    bayesian_posteriors: Dict[str, float],
) -> Dict[str, Any]:
    """
    Score dispute using GNN over the clause-risk graph.
    Returns GNN prediction dict with dispute_probability + outcome distribution.
    """
    service = _get_gnn()

    node_features, edges = _build_clause_graph_from_signals(signals, bayesian_posteriors)

    if service:
        try:
            result = service.predict(node_features, edges)
            result['source'] = 'gnn_model' if service.is_available() else 'gnn_heuristic'
            return result
        except Exception as e:
            logger.warning(f"GNN predict error: {e}")

    # Pure heuristic fallback if GNN service totally unavailable
    avg_risk = float(np.mean([np.mean(nf) for nf in node_features]))
    dispute_prob = min(0.40 + avg_risk * 0.55, 0.92)
    return {
        'dispute_probability': round(dispute_prob, 4),
        'buyer_win_probability': round(0.30, 4),
        'supplier_win_probability': round(0.25, 4),
        'partial_award_probability': round(0.25, 4),
        'settlement_probability': round(0.20, 4),
        'confidence': round(0.35, 4),
        'source': 'heuristic',
    }


# ═══════════════════════════════════════════════════════════
# 4. BM25 + BERT RAG — SIMILAR CLAUSE RETRIEVAL
# ═══════════════════════════════════════════════════════════

_rag_retriever = None
_rag_indexed_contract_count = 0

def _get_rag_retriever(force_reindex: bool = False):
    """
    Build / return BM25+BERT retriever indexed on all clauses in DB.
    Lazy-initialised; re-indexes if new contracts have been added.
    """
    global _rag_retriever, _rag_indexed_contract_count

    try:
        from ai.rag.bm25_bert_retriever import BM25BERTRetriever
    except ImportError:
        logger.warning("BM25BERTRetriever not importable")
        return None

    try:
        from core.models import Clause
        total = Clause.objects.count()
    except Exception:
        return None

    if _rag_retriever is None or force_reindex or total != _rag_indexed_contract_count:
        try:
            from core.models import Clause
            clauses = Clause.objects.select_related().values(
                'id', 'extracted_text', 'clause_name', 'clause_type', 'contract_id'
            )[:2000]  # Cap at 2000 for performance

            documents = []
            for c in clauses:
                text = c.get('extracted_text') or c.get('clause_name') or ''
                if len(text) > 20:
                    documents.append({
                        'id': str(c['id']),
                        'text': text[:512],
                        'clause_type': c.get('clause_type', ''),
                        'contract_id': str(c.get('contract_id', '')),
                    })

            if documents:
                _rag_retriever = BM25BERTRetriever(documents=documents)
                _rag_indexed_contract_count = total
                logger.info(f"RAG retriever indexed {len(documents)} clauses")
            else:
                _rag_retriever = None
        except Exception as e:
            logger.warning(f"RAG indexing failed: {e}")
            _rag_retriever = None

    return _rag_retriever


def retrieve_similar_clauses(
    contract_text: str,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    BM25+BERT hybrid retrieval of similar clauses from the clause library.
    Uses risk-focused query derived from the top risk signals in the contract.
    """
    retriever = _get_rag_retriever()
    if not retriever:
        return []

    try:
        # Build a focused query from the most risk-relevant excerpt
        query = contract_text[:600]
        results = retriever.search(query, top_k=top_k, min_score=0.01)

        formatted = []
        for r in results:
            doc = r.get('document', {})
            formatted.append({
                'clause_id': r.get('doc_id', ''),
                'clause_text': (doc.get('text', '') or '')[:300],
                'clause_type': doc.get('clause_type', ''),
                'contract_id': doc.get('contract_id', ''),
                'fusion_score': round(r.get('fusion_score', 0), 3),
                'bm25_score': round(r.get('bm25_score', 0), 3),
                'bert_score': round(r.get('bert_score', 0), 3),
                'retrieval_method': r.get('retrieval_method', 'hybrid'),
            })

        return formatted

    except Exception as e:
        logger.warning(f"RAG retrieval failed: {e}")
        return []


# ═══════════════════════════════════════════════════════════
# 5. QWEN 2.5 EXPLANATION (via Ollama)
# ═══════════════════════════════════════════════════════════

def generate_dispute_explanation(
    contract_text: str,
    dispute_probability: float,
    top_risk_drivers: list,
    contract_value: float = 0,
    gnn_score: Optional[float] = None,
    legalbert_amplified: Optional[list] = None,
) -> str:
    ollama_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
    model_name = getattr(settings, 'OLLAMA_MODEL', 'qwen2.5:0.5b')

    drivers_text = '\n'.join([
        f"- {d['label']}: {d['probability']:.0%}"
        for d in top_risk_drivers[:5]
    ])

    gnn_line = f"GNN dispute score: {gnn_score:.0%}" if gnn_score is not None else ''
    bert_line = ''
    if legalbert_amplified:
        top_amp = legalbert_amplified[:2]
        bert_line = 'Semantically amplified risks: ' + ', '.join(
            f"{a['node']} ({a['similarity']:.2f})" for a in top_amp
        )

    contract_excerpt = contract_text[:700] if contract_text else 'No contract text provided.'

    prompt = f"""You are a senior legal risk analyst. Write a structured dispute risk report using ONLY the data below. Do NOT repeat sentences. Do NOT invent numbers.

DISPUTE PROBABILITY: {dispute_probability:.0%}
CONTRACT VALUE: ${contract_value:,.0f}
TOP RISK DRIVERS: {drivers_text}
{gnn_line}{bert_line}

Write exactly this structure (no extra text):

### Key Legal Risks
1. [First specific risk from the drivers above]
2. [Second specific risk]
3. [Third specific risk]

### Primary Dispute Triggers
1. [Specific clause or condition that could trigger dispute]
2. [Second trigger]

### Mitigation Recommendations
1. [Specific actionable recommendation for risk 1]
2. [Specific actionable recommendation for risk 2]
3. [Specific actionable recommendation for risk 3]

### Summary
One sentence summary of overall risk level and recommended action."""

    try:
        response = requests.post(
            f"{ollama_url}/api/generate",
            json={
                'model': model_name,
                'prompt': prompt,
                'stream': False,
                'options': {'temperature': 0.1, 'num_predict': 400, 'repeat_penalty': 1.3, 'top_p': 0.9},
            },
            timeout=5,
        )
        if response.status_code == 200:
            return response.json().get('response', '').strip()
    except Exception as e:
        logger.warning(f"Ollama unavailable: {e}")

    return _rule_based_explanation(dispute_probability, top_risk_drivers, contract_value)


def _rule_based_explanation(
    dispute_probability: float,
    top_risk_drivers: list,
    contract_value: float,
) -> str:
    level = 'HIGH' if dispute_probability > 0.6 else 'MEDIUM' if dispute_probability > 0.35 else 'LOW'
    top3 = top_risk_drivers[:3]
    mitigations = _build_mitigations(top_risk_drivers)

    key_risks = '\n'.join(
        f"{i+1}. **{d['label']}** ({d['probability']:.0%}) — {d.get('cluster', 'contract')} layer risk"
        for i, d in enumerate(top3)
    ) or '1. Contract ambiguity detected\n2. Performance obligation risk\n3. Payment default exposure'

    triggers = '\n'.join(
        f"{i+1}. {d['label']} at {d['probability']:.0%} probability"
        for i, d in enumerate(top3[:2])
    ) or '1. Ambiguous performance obligations\n2. Payment default provisions'

    rec_lines = '\n'.join(
        f"{i+1}. {m['recommendation']}"
        for i, m in enumerate(mitigations[:3])
    ) or '1. Add clear dispute resolution clause\n2. Define liquidated damages cap\n3. Include force majeure provisions'

    return (
        f"### Key Legal Risks\n{key_risks}\n\n"
        f"### Primary Dispute Triggers\n{triggers}\n\n"
        f"### Mitigation Recommendations\n{rec_lines}\n\n"
        f"### Summary\n"
        f"This contract carries a **{level}** dispute risk at **{dispute_probability:.0%}** probability "
        f"with estimated legal exposure of **${contract_value * dispute_probability * 0.15:,.0f}**. "
        f"Immediate review of the top risk clauses is recommended."
    )


# ═══════════════════════════════════════════════════════════
# 6. COST ESTIMATION
# ═══════════════════════════════════════════════════════════

def estimate_legal_cost(
    contract_value: float,
    dispute_probability: float,
    arbitration_probability: float,
    legal_cost_exposure_score: float,
) -> Dict[str, float]:
    base_rate = 0.03 + (legal_cost_exposure_score * 0.12)
    predicted_cost = contract_value * dispute_probability * base_rate
    if arbitration_probability > 0.3:
        predicted_cost += contract_value * arbitration_probability * 0.025
    p50 = predicted_cost
    p90 = predicted_cost * 2.5
    return {
        'predicted_cost_usd': round(predicted_cost, 2),
        'legal_cost_p50': round(p50, 2),
        'legal_cost_p90': round(p90, 2),
        'legal_cost_exposure_usd': round(p90, 2),
    }


# ═══════════════════════════════════════════════════════════
# 7. MITIGATION BUILDER
# ═══════════════════════════════════════════════════════════

def _build_mitigations(top_drivers: list) -> list:
    driver_ids = {d['node'] for d in top_drivers}
    mapping = {
        'ContractAmbiguity':      'Revise ambiguous clauses with precise, measurable definitions.',
        'SupplierDelay':          'Insert liquidated damages and milestone-based delivery schedules.',
        'DeliveryFailure':        'Add delivery performance bonds and step-in rights.',
        'PaymentDefaultRisk':     'Require payment security instruments (LC, bank guarantee).',
        'LiabilityExposure':      'Cap aggregate liability; exclude consequential damages.',
        'CommodityPriceShock':    'Include commodity price adjustment clauses (CPI/PPI indexation).',
        'ContractCostOverrun':    'Define change order approval thresholds and budget contingency.',
        'SLAViolation':           'Tighten SLA metrics with service credits and remediation timelines.',
        'RenegotiationRisk':      'Lock in key commercial terms with renegotiation blackout periods.',
        'TerminationRisk':        'Specify cure periods and graduated termination notice requirements.',
        'ClauseConflict':         'Conduct clause conflict audit and establish order of precedence.',
        'CounterpartyCreditRisk': 'Conduct financial due diligence; require parent company guarantee.',
        'CashFlowStress':         'Negotiate milestone payments aligned to project cash flow schedule.',
        'WarRisk':                'Include comprehensive force majeure and war risk insurance clauses.',
        'EnergyPriceShock':       'Add energy cost pass-through or hedging provisions.',
    }
    mitigations = []
    for node_id in [d['node'] for d in top_drivers[:7]]:
        if node_id in mapping:
            mitigations.append({'node': node_id, 'recommendation': mapping[node_id]})
    if not mitigations:
        mitigations.append({
            'node': 'General',
            'recommendation': 'Include a structured dispute resolution ladder (negotiation → mediation → arbitration).',
        })
    return mitigations[:6]


# ═══════════════════════════════════════════════════════════
# 8. MAIN PREDICTION PIPELINE
# ═══════════════════════════════════════════════════════════

def predict_dispute(
    contract_text: str,
    contract_value: float = 1_000_000,
    manual_signals: Optional[Dict[str, float]] = None,
    generate_explanation: bool = True,
    enable_legalbert: bool = True,
    enable_gnn: bool = True,
    enable_rag: bool = True,
) -> Dict[str, Any]:
    """
    Full dispute prediction pipeline.

    Args:
        contract_text: Raw contract text
        contract_value: Contract value in USD
        manual_signals: Optional override signals {node_id: 0–1}
        generate_explanation: Whether to call Qwen for explanation
        enable_legalbert: Run LegalBERT semantic amplification
        enable_gnn: Run GNN clause graph scoring
        enable_rag: Run BM25+BERT similar clause retrieval

    Returns:
        Full prediction result dict
    """
    engine = get_bayesian_engine()

    # Step 1: Regex risk signal extraction
    text_signals = extract_risk_signals_from_text(contract_text)

    # Merge with manual overrides
    evidence = {**text_signals}
    if manual_signals:
        evidence.update(manual_signals)

    # Step 2: LegalBERT semantic amplification
    legalbert_meta = {'available': False, 'amplified_nodes': []}
    if enable_legalbert and contract_text:
        evidence, legalbert_meta = amplify_signals_with_legalbert(contract_text, evidence)

    # Step 3: Bayesian inference (rescaling handled inside engine)
    bayesian_result = engine.compute_dispute_probability(evidence)

    # Step 4: GNN scoring
    gnn_result = None
    if enable_gnn:
        gnn_result = score_with_gnn(evidence, bayesian_result['all_node_posteriors'])

    # Ensemble: blend Bayesian + GNN dispute probability (60/40)
    final_dispute_prob = bayesian_result['dispute_probability']
    if gnn_result:
        final_dispute_prob = round(
            0.60 * bayesian_result['dispute_probability'] +
            0.40 * gnn_result['dispute_probability'],
            3
        )

    # Step 5: RAG — similar clause retrieval
    similar_clauses = []
    if enable_rag and contract_text:
        similar_clauses = retrieve_similar_clauses(contract_text, top_k=5)

    # Step 6: Cost estimation
    cost_result = estimate_legal_cost(
        contract_value=contract_value,
        dispute_probability=final_dispute_prob,
        arbitration_probability=bayesian_result['arbitration_probability'],
        legal_cost_exposure_score=bayesian_result['legal_cost_exposure_score'],
    )

    # Step 7: Qwen explanation
    explanation = ''
    if generate_explanation:
        explanation = generate_dispute_explanation(
            contract_text=contract_text,
            dispute_probability=final_dispute_prob,
            top_risk_drivers=bayesian_result['top_risk_drivers'],
            contract_value=contract_value,
            gnn_score=gnn_result['dispute_probability'] if gnn_result else None,
            legalbert_amplified=legalbert_meta.get('amplified_nodes', []),
        )

    # Step 8: Mitigations
    mitigations = _build_mitigations(bayesian_result['top_risk_drivers'])

    return {
        # Core probabilities
        'dispute_probability': final_dispute_prob,
        'bayesian_dispute_probability': bayesian_result['dispute_probability'],
        'contract_risk_score': bayesian_result['contract_risk_score'],
        'financial_stress_score': bayesian_result['financial_stress_score'],
        'operational_risk_score': bayesian_result['operational_risk_score'],
        'geopolitical_risk_score': bayesian_result['geopolitical_risk_score'],
        'arbitration_probability': bayesian_result['arbitration_probability'],
        'litigation_probability': bayesian_result['litigation_probability'],
        'settlement_probability': bayesian_result['settlement_probability'],

        # Cost
        'predicted_cost_usd': cost_result['predicted_cost_usd'],
        'legal_cost_p50': cost_result['legal_cost_p50'],
        'legal_cost_p90': cost_result['legal_cost_p90'],
        'legal_cost_exposure_usd': cost_result['legal_cost_exposure_usd'],

        # Risk graph
        'top_risk_drivers': bayesian_result['top_risk_drivers'],
        'risk_propagation_path': bayesian_result['risk_propagation_path'],
        'all_node_posteriors': bayesian_result['all_node_posteriors'],

        # GNN
        'gnn_dispute_score': gnn_result['dispute_probability'] if gnn_result else None,
        'gnn_confidence': gnn_result.get('confidence') if gnn_result else None,
        'gnn_outcome_distribution': {
            'buyer_win': gnn_result.get('buyer_win_probability') if gnn_result else None,
            'supplier_win': gnn_result.get('supplier_win_probability') if gnn_result else None,
            'partial_award': gnn_result.get('partial_award_probability') if gnn_result else None,
            'settlement': gnn_result.get('settlement_probability') if gnn_result else None,
        } if gnn_result else None,
        'gnn_source': gnn_result.get('source', 'unavailable') if gnn_result else 'unavailable',

        # LegalBERT
        'legalbert_available': legalbert_meta.get('available', False),
        'legalbert_amplified_nodes': legalbert_meta.get('amplified_nodes', []),
        'legalbert_similarity_scores': legalbert_meta.get('similarity_scores', {}),

        # RAG
        'similar_clauses': similar_clauses,

        # Explanation & recommendations
        'explanation': explanation,
        'mitigation_recommendations': mitigations,

        # Inputs used
        'input_signals': evidence,
        'contract_value': contract_value,
    }
