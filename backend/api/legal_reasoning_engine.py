"""
Production-Grade Legal Reasoning Engine
=========================================
Architecture:
  1. Legal Knowledge Base  – jurisdiction-specific statute passages + case law
  2. RAG Vector Store      – FAISS (sentence-transformers) with TF-IDF fallback
  3. Entity Extractor      – key legal entities from clause text
  4. Rule Engine           – pattern-based risk rules (jurisdiction-aware)
  5. LLM Reasoner          – Qwen 2.5 via Ollama, structured JSON output
  6. Explainability Layer  – confidence scoring, law/case citations
"""

from __future__ import annotations

import json
import logging
import math
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Tuple

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")


# ══════════════════════════════════════════════════════════════════
# 1.  LEGAL KNOWLEDGE BASE
# ══════════════════════════════════════════════════════════════════

LEGAL_KB: Dict[str, List[Dict]] = {
    "india": [
        {
            "id": "ICA-10",
            "type": "statute",
            "title": "Indian Contract Act 1872 – Section 10",
            "citation": "Section 10, Indian Contract Act 1872",
            "text": (
                "Section 10 ICA 1872: All agreements are contracts if made by the free consent "
                "of parties competent to contract, for a lawful consideration and with a lawful "
                "object, and are not hereby expressly declared to be void. Free consent requires "
                "absence of coercion, undue influence, fraud, misrepresentation, and mistake."
            ),
            "keywords": ["consent", "free consent", "competent", "lawful", "void", "coercion", "undue influence"],
        },
        {
            "id": "ICA-23",
            "type": "statute",
            "title": "Indian Contract Act 1872 – Section 23",
            "citation": "Section 23, Indian Contract Act 1872",
            "text": (
                "Section 23 ICA 1872: The consideration or object of an agreement is lawful unless "
                "it is forbidden by law, would defeat provisions of any law, is fraudulent, involves "
                "injury to person or property, or is immoral or opposed to public policy. Every "
                "agreement whose object or consideration is unlawful is void. Unlimited liability "
                "clauses that create unconscionable outcomes may be void under public policy."
            ),
            "keywords": ["unlawful", "public policy", "void", "forbidden", "unlimited liability", "immoral"],
        },
        {
            "id": "ICA-27",
            "type": "statute",
            "title": "Indian Contract Act 1872 – Section 27",
            "citation": "Section 27, Indian Contract Act 1872",
            "text": (
                "Section 27 ICA 1872: Every agreement by which any one is restrained from exercising "
                "a lawful profession, trade, or business of any kind is to that extent void. Restraint "
                "of trade clauses, non-compete agreements, and exclusivity provisions must be narrowly "
                "drafted to avoid invalidity."
            ),
            "keywords": ["restraint of trade", "non-compete", "exclusivity", "profession", "business", "void"],
        },
        {
            "id": "ICA-28",
            "type": "statute",
            "title": "Indian Contract Act 1872 – Section 28",
            "citation": "Section 28, Indian Contract Act 1872",
            "text": (
                "Section 28 ICA 1872: Every agreement restricting a party absolutely from enforcing "
                "rights through usual legal proceedings, or limiting the time within which he may "
                "enforce his rights, is void to that extent. Clauses barring legal recourse or "
                "imposing unreasonably short limitation periods are void."
            ),
            "keywords": ["legal proceedings", "limitation", "restrict rights", "void", "dispute resolution"],
        },
        {
            "id": "ICA-56",
            "type": "statute",
            "title": "Indian Contract Act 1872 – Section 56",
            "citation": "Section 56, Indian Contract Act 1872",
            "text": (
                "Section 56 ICA 1872: An agreement to do an act impossible in itself is void. A "
                "contract to do an act which becomes impossible or unlawful after formation becomes "
                "void when performance becomes impossible. The doctrine of frustration discharges "
                "parties from obligations when supervening events render performance impossible. "
                "Force majeure clauses codify similar relief."
            ),
            "keywords": ["impossible", "frustration", "force majeure", "supervening", "discharge", "void"],
        },
        {
            "id": "ICA-73",
            "type": "statute",
            "title": "Indian Contract Act 1872 – Section 73",
            "citation": "Section 73, Indian Contract Act 1872",
            "text": (
                "Section 73 ICA 1872: When a contract has been broken, the party who suffers is "
                "entitled to receive compensation for any loss or damage naturally arising from such "
                "breach, or which the parties knew to be likely to result. Compensation is not given "
                "for remote or indirect loss. Unlimited liability clauses may conflict with this "
                "principle of proximate causation."
            ),
            "keywords": ["breach", "compensation", "damages", "loss", "proximate cause", "liability", "unlimited liability"],
        },
        {
            "id": "ICA-74",
            "type": "statute",
            "title": "Indian Contract Act 1872 – Section 74",
            "citation": "Section 74, Indian Contract Act 1872",
            "text": (
                "Section 74 ICA 1872: When a contract has been broken, if a sum is named as the "
                "amount to be paid in case of breach, or if the contract contains any stipulation "
                "by way of penalty, the party complaining of breach is entitled to receive reasonable "
                "compensation not exceeding the amount named. Courts will not enforce punitive or "
                "extravagant penalty clauses."
            ),
            "keywords": ["penalty", "liquidated damages", "breach", "reasonable compensation", "punitive", "named sum"],
        },
        {
            "id": "ICA-ACA-1996",
            "type": "statute",
            "title": "Arbitration and Conciliation Act 1996",
            "citation": "Arbitration and Conciliation Act 1996 (India)",
            "text": (
                "The Arbitration and Conciliation Act 1996 governs domestic and international commercial "
                "arbitration in India. Section 7 requires an arbitration agreement to be in writing. "
                "Section 34 allows courts to set aside awards on grounds of public policy. Specify "
                "seat, institution (DIAC, SIAC, ICC), and governing procedural rules."
            ),
            "keywords": ["arbitration", "dispute resolution", "seat", "award", "public policy", "written agreement"],
        },
        {
            "id": "ONGC-SAW-PIPES",
            "type": "case",
            "title": "ONGC v Saw Pipes Ltd (2003)",
            "citation": "ONGC v Saw Pipes Ltd (2003) 5 SCC 705",
            "text": (
                "ONGC v Saw Pipes Ltd (2003) 5 SCC 705: The Supreme Court held that where a genuine "
                "pre-estimate of loss exists, the full amount is recoverable as liquidated damages "
                "without proof of actual loss. This clarified that Section 74 ICA applies to both "
                "penalty clauses and genuine liquidated damages. Courts can interfere with arbitral "
                "awards that are patently illegal or against public policy."
            ),
            "keywords": ["liquidated damages", "penalty", "arbitration", "public policy", "pre-estimate", "Section 74"],
        },
        {
            "id": "FATEH-CHAND",
            "type": "case",
            "title": "Fateh Chand v Balkishan Dass (1964)",
            "citation": "Fateh Chand v Balkishan Dass (1964) 1 SCR 515",
            "text": (
                "Fateh Chand v Balkishan Dass (1964) 1 SCR 515: The Supreme Court held that Section 74 "
                "ICA covers all contractual stipulations for payment on breach, including forfeiture "
                "clauses. The court may grant reasonable compensation even where no actual loss is "
                "proved, but compensation cannot exceed the named amount."
            ),
            "keywords": ["penalty", "forfeiture", "Section 74", "reasonable compensation", "breach"],
        },
        {
            "id": "KAILASH-NATH",
            "type": "case",
            "title": "Kailash Nath Associates v DDA (2015)",
            "citation": "Kailash Nath Associates v DDA (2015) 4 SCC 136",
            "text": (
                "Kailash Nath Associates v DDA (2015) 4 SCC 136: The Supreme Court clarified that "
                "under Section 74, a party must prove actual loss to recover damages even where a sum "
                "is stipulated as liquidated damages, unless the clause is a genuine pre-estimate. "
                "If actual loss is nil, no compensation is awarded."
            ),
            "keywords": ["actual loss", "liquidated damages", "Section 74", "proof of loss", "forfeiture"],
        },
    ],

    "us": [
        {
            "id": "UCC-1-304",
            "type": "statute",
            "title": "UCC § 1-304: Obligation of Good Faith",
            "citation": "UCC § 1-304 (Obligation of Good Faith)",
            "text": (
                "UCC § 1-304: Every contract or duty within the UCC imposes an obligation of good "
                "faith in its performance and enforcement. Good faith means honesty in fact and "
                "observance of reasonable commercial standards of fair dealing. Clauses allowing "
                "one party to act in bad faith or withhold performance arbitrarily may violate "
                "this implied covenant."
            ),
            "keywords": ["good faith", "fair dealing", "performance", "enforcement", "commercial standards"],
        },
        {
            "id": "UCC-2-302",
            "type": "statute",
            "title": "UCC § 2-302: Unconscionable Contract or Clause",
            "citation": "UCC § 2-302 (Unconscionable Contract or Clause)",
            "text": (
                "UCC § 2-302: If the court finds the contract or any clause unconscionable at the "
                "time it was made, the court may refuse to enforce the contract or enforce it without "
                "the unconscionable clause. Unconscionability includes both procedural (bargaining "
                "process) and substantive (oppressive terms) elements. Unlimited liability or "
                "one-sided indemnification clauses risk being deemed unconscionable."
            ),
            "keywords": ["unconscionable", "procedural", "substantive", "oppressive", "unlimited liability", "one-sided"],
        },
        {
            "id": "UCC-2-718",
            "type": "statute",
            "title": "UCC § 2-718: Liquidation of Damages",
            "citation": "UCC § 2-718 (Liquidation or Limitation of Damages)",
            "text": (
                "UCC § 2-718: Damages for breach may be liquidated in the agreement only at an amount "
                "which is reasonable in light of anticipated or actual harm caused by the breach, "
                "difficulties of proof of loss, and the inconvenience of obtaining an adequate remedy. "
                "A term fixing unreasonably large liquidated damages is void as a penalty."
            ),
            "keywords": ["liquidated damages", "penalty", "reasonable", "breach", "anticipated harm"],
        },
        {
            "id": "UCC-2-719",
            "type": "statute",
            "title": "UCC § 2-719: Modification or Limitation of Remedy",
            "citation": "UCC § 2-719 (Contractual Modification or Limitation of Remedy)",
            "text": (
                "UCC § 2-719: Parties may limit or alter available remedies for breach. Where an "
                "exclusive or limited remedy fails its essential purpose, remedy may be as provided "
                "in this Act. Consequential damages may be excluded unless unconscionable. Limitation "
                "of damages for injury to the person in consumer goods is prima facie unconscionable."
            ),
            "keywords": ["limitation of remedy", "consequential damages", "exclusion", "essential purpose", "unconscionable"],
        },
        {
            "id": "FAA-9",
            "type": "statute",
            "title": "Federal Arbitration Act – 9 U.S.C. §§ 1-16",
            "citation": "Federal Arbitration Act, 9 U.S.C. §§ 1-16",
            "text": (
                "The Federal Arbitration Act (FAA) establishes a strong federal policy favouring "
                "arbitration agreements. Section 2 provides that written arbitration agreements in "
                "contracts evidencing transactions in commerce are valid and enforceable. Courts must "
                "compel arbitration when a valid agreement exists. Class action waivers in arbitration "
                "clauses are generally enforceable under FAA."
            ),
            "keywords": ["arbitration", "FAA", "class waiver", "enforceable", "dispute resolution", "compel arbitration"],
        },
        {
            "id": "HENNINGSEN",
            "type": "case",
            "title": "Henningsen v Bloomfield Motors (1960)",
            "citation": "Henningsen v Bloomfield Motors, Inc., 32 N.J. 358 (1960)",
            "text": (
                "Henningsen v Bloomfield Motors (1960): The New Jersey Supreme Court struck down a "
                "warranty disclaimer clause as unconscionable and against public policy. Where a party "
                "has no meaningful choice but to accept a standard form contract, courts may refuse "
                "to enforce oppressive clauses. This landmark case established the unconscionability "
                "doctrine that influenced UCC § 2-302."
            ),
            "keywords": ["unconscionability", "warranty disclaimer", "public policy", "standard form", "oppressive"],
        },
        {
            "id": "CARNIVAL-CRUISE",
            "type": "case",
            "title": "Carnival Cruise Lines v Shute (1991)",
            "citation": "Carnival Cruise Lines, Inc. v Shute, 499 U.S. 585 (1991)",
            "text": (
                "Carnival Cruise Lines v Shute (1991): The US Supreme Court upheld a forum selection "
                "clause in a standard-form contract as presumptively valid if reasonable. Courts will "
                "enforce exclusive jurisdiction clauses unless fundamentally unfair or the result of "
                "fraud or overreaching."
            ),
            "keywords": ["forum selection", "exclusive jurisdiction", "governing law", "standard form", "reasonable"],
        },
        {
            "id": "AT-T-CONCEPCION",
            "type": "case",
            "title": "AT&T Mobility v Concepcion (2011)",
            "citation": "AT&T Mobility LLC v Concepcion, 563 U.S. 333 (2011)",
            "text": (
                "AT&T Mobility v Concepcion (2011): The Supreme Court held that the FAA preempts "
                "state laws invalidating class arbitration waivers. Arbitration clauses with class "
                "action waivers are generally enforceable under the FAA, significantly strengthening "
                "mandatory arbitration clauses in consumer and commercial contracts."
            ),
            "keywords": ["arbitration", "class action waiver", "FAA", "preemption", "mandatory arbitration"],
        },
    ],

    "uk": [
        {
            "id": "UCTA-2",
            "type": "statute",
            "title": "UCTA 1977 – Section 2: Negligence Liability",
            "citation": "Section 2, Unfair Contract Terms Act 1977 (UCTA)",
            "text": (
                "UCTA 1977 Section 2: A person cannot by reference to any contract term exclude or "
                "restrict liability for death or personal injury resulting from negligence. For other "
                "loss or damage, liability for negligence can only be excluded insofar as the term "
                "satisfies the reasonableness requirement. Clauses excluding liability for negligence "
                "causing economic loss must pass the reasonableness test."
            ),
            "keywords": ["negligence", "exclude liability", "death", "personal injury", "reasonableness", "economic loss"],
        },
        {
            "id": "UCTA-3",
            "type": "statute",
            "title": "UCTA 1977 – Section 3: Liability in Contract",
            "citation": "Section 3, Unfair Contract Terms Act 1977 (UCTA)",
            "text": (
                "UCTA 1977 Section 3: As against a person dealing as consumer or on the other's written "
                "standard terms, the other cannot exclude or restrict any liability in respect of breach, "
                "or claim to be entitled to render a substantially different or no performance. Such "
                "clauses must satisfy the reasonableness test."
            ),
            "keywords": ["standard terms", "consumer", "exclude liability", "breach", "reasonableness"],
        },
        {
            "id": "UCTA-11",
            "type": "statute",
            "title": "UCTA 1977 – Section 11: Reasonableness Test",
            "citation": "Section 11, Unfair Contract Terms Act 1977 (UCTA)",
            "text": (
                "UCTA 1977 Section 11: The reasonableness test is that the term shall have been a fair "
                "and reasonable one to be included having regard to circumstances known to the parties "
                "when the contract was made. Schedule 2 guidelines include: bargaining strength, "
                "inducements to agree, customer's knowledge, and custom of trade. Unlimited liability "
                "for suppliers or one-sided indemnities typically fail this test."
            ),
            "keywords": ["reasonableness", "fair and reasonable", "Schedule 2", "bargaining strength", "indemnity", "unlimited liability"],
        },
        {
            "id": "CRA-2015",
            "type": "statute",
            "title": "Consumer Rights Act 2015 – Section 62",
            "citation": "Section 62, Consumer Rights Act 2015 (CRA 2015)",
            "text": (
                "CRA 2015 Section 62: An unfair term of a consumer contract is not binding on the "
                "consumer. A term is unfair if, contrary to good faith, it causes a significant "
                "imbalance in the parties' rights and obligations to the detriment of the consumer. "
                "The Schedule 2 indicative list includes: clauses excluding liability for non-performance, "
                "one-sided termination rights, and excessive penalty clauses."
            ),
            "keywords": ["unfair terms", "consumer", "good faith", "significant imbalance", "detriment", "penalty"],
        },
        {
            "id": "ARBITRATION-ACT-1996",
            "type": "statute",
            "title": "Arbitration Act 1996 (UK)",
            "citation": "Arbitration Act 1996 (UK)",
            "text": (
                "The Arbitration Act 1996 provides a comprehensive framework for arbitration in England "
                "and Wales. Section 5 requires arbitration agreements to be in writing. Section 33 "
                "imposes a duty on tribunals to act fairly and impartially. Section 68 allows challenges "
                "for serious irregularity. LCIA and ICC arbitration clauses are commonly used."
            ),
            "keywords": ["arbitration", "LCIA", "ICC", "seat", "dispute resolution", "England"],
        },
        {
            "id": "PHOTO-PRODUCTION",
            "type": "case",
            "title": "Photo Production v Securicor Transport (1980)",
            "citation": "Photo Production Ltd v Securicor Transport Ltd [1980] AC 827 (HL)",
            "text": (
                "Photo Production v Securicor [1980] AC 827: The House of Lords abolished the doctrine "
                "of fundamental breach, holding that whether an exclusion clause covers a particular "
                "breach is a matter of construction. Post-UCTA 1977, exclusion clauses in business "
                "contracts must satisfy the reasonableness test."
            ),
            "keywords": ["exclusion clause", "fundamental breach", "reasonableness", "construction", "liability exclusion"],
        },
        {
            "id": "GEORGE-MITCHELL",
            "type": "case",
            "title": "George Mitchell v Finney Lock Seeds (1983)",
            "citation": "George Mitchell (Chesterhall) Ltd v Finney Lock Seeds Ltd [1983] 2 AC 803",
            "text": (
                "George Mitchell v Finney Lock Seeds [1983] 2 AC 803: The House of Lords applied the "
                "UCTA reasonableness test to a limitation clause. A clause limiting liability to the "
                "price of seeds was held unreasonable where breach caused losses many times greater. "
                "Factors included relative bargaining strength, available insurance, and nature of breach."
            ),
            "keywords": ["reasonableness", "limitation clause", "UCTA", "bargaining strength", "insurance"],
        },
        {
            "id": "CAVENDISH-MAKDESSI",
            "type": "case",
            "title": "Cavendish Square v Makdessi (2015)",
            "citation": "Cavendish Square Holding BV v Makdessi [2015] UKSC 67",
            "text": (
                "Cavendish Square v Makdessi [2015] UKSC 67: The UK Supreme Court reformulated the "
                "penalty rule. A clause is a penalty only if it imposes a detriment on the contract-"
                "breaker out of all proportion to any legitimate interest of the innocent party. This "
                "makes it harder to strike down commercial liquidated damages clauses between "
                "sophisticated parties."
            ),
            "keywords": ["penalty", "liquidated damages", "legitimate interest", "proportionate", "commercial"],
        },
    ],
}

UNIVERSAL_KB: List[Dict] = [
    {
        "id": "CISG",
        "type": "statute",
        "title": "UN Convention on International Sale of Goods (CISG)",
        "citation": "CISG (1980) – UN Convention on International Sale of Goods",
        "text": (
            "The CISG governs international sales contracts between parties in different contracting "
            "states. Article 8 provides rules for interpreting statements and conduct. Article 25 "
            "defines fundamental breach. Article 79 excuses non-performance due to impediment beyond "
            "control (equivalent to force majeure). Parties may opt out of CISG by explicit clause."
        ),
        "keywords": ["international", "CISG", "force majeure", "fundamental breach", "impediment"],
    },
    {
        "id": "GOVERNING-LAW-GENERAL",
        "type": "statute",
        "title": "Governing Law and Jurisdiction – General Principles",
        "citation": "General Principles – Governing Law Clauses",
        "text": (
            "A governing law clause specifies which country's law governs the contract's interpretation "
            "and enforcement. An exclusive jurisdiction clause specifies courts with authority to hear "
            "disputes. Absence of a governing law clause creates uncertainty and may result in conflict "
            "of laws issues. Best practice requires both a governing law clause and a dispute resolution "
            "mechanism to be clearly stated."
        ),
        "keywords": ["governing law", "jurisdiction", "choice of law", "dispute resolution", "conflict of laws"],
    },
]


# ══════════════════════════════════════════════════════════════════
# 2.  RAG VECTOR STORE  (FAISS → numpy cosine → TF-IDF fallback)
# ══════════════════════════════════════════════════════════════════

class LegalVectorStore:
    """
    Stores legal KB passages as embeddings.
    Priority: sentence-transformers + FAISS > sentence-transformers + numpy > TF-IDF cosine.
    """

    def __init__(self) -> None:
        self._passages: List[Dict] = []
        self._use_st = False
        self._model = None
        self._index = None
        self._embeddings = None
        self._init_model()
        self._build_index()

    def _init_model(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
            self._model = SentenceTransformer("paraphrase-MiniLM-L3-v2", device='cpu')
            self._use_st = True
            logger.info("LegalVectorStore: sentence-transformers loaded")
        except Exception as exc:
            logger.info("LegalVectorStore: TF-IDF fallback (%s)", exc)

    def _build_index(self) -> None:
        passages: List[Dict] = []
        for jurisdiction, docs in LEGAL_KB.items():
            for doc in docs:
                passages.append({**doc, "jurisdiction": jurisdiction})
        for doc in UNIVERSAL_KB:
            passages.append({**doc, "jurisdiction": "universal"})
        self._passages = passages

        if self._use_st and self._model:
            try:
                import numpy as np  # type: ignore
                texts = [p["text"] for p in passages]
                embs = self._model.encode(texts, show_progress_bar=False).astype("float32")
                norms = np.linalg.norm(embs, axis=1, keepdims=True) + 1e-8
                self._embeddings = embs / norms
                try:
                    import faiss  # type: ignore
                    self._index = faiss.IndexFlatIP(embs.shape[1])
                    self._index.add(self._embeddings)
                    logger.info("LegalVectorStore: FAISS index built (%d passages)", len(passages))
                except Exception:
                    logger.info("LegalVectorStore: numpy cosine mode (no FAISS)")
            except Exception as exc:
                logger.warning("LegalVectorStore: embedding build failed: %s", exc)
                self._use_st = False

        if not self._use_st:
            for p in self._passages:
                p["_tfidf"] = self._tfidf(p["text"] + " " + " ".join(p.get("keywords", [])))

    @staticmethod
    def _tfidf(text: str) -> Dict[str, float]:
        words = re.findall(r"\w+", text.lower())
        if not words:
            return {}
        tf: Dict[str, float] = {}
        for w in words:
            tf[w] = tf.get(w, 0) + 1
        n = len(words)
        return {w: c / n for w, c in tf.items()}

    @staticmethod
    def _cosine(v1: Dict, v2: Dict) -> float:
        keys = set(v1) & set(v2)
        if not keys:
            return 0.0
        dot = sum(v1[k] * v2[k] for k in keys)
        m1 = math.sqrt(sum(x * x for x in v1.values()))
        m2 = math.sqrt(sum(x * x for x in v2.values()))
        return dot / (m1 * m2 + 1e-9)

    def retrieve(self, query: str, jurisdiction: str, top_k: int = 5) -> List[Dict]:
        if not self._passages:
            return []

        candidates_idx = [
            i for i, p in enumerate(self._passages)
            if p["jurisdiction"] in (jurisdiction, "universal")
        ]
        if not candidates_idx:
            candidates_idx = list(range(len(self._passages)))

        query_enriched = query + f" {jurisdiction} contract law legal clause risk"

        if self._use_st and self._model and self._embeddings is not None:
            import numpy as np  # type: ignore
            qe = self._model.encode([query_enriched], show_progress_bar=False)[0].astype("float32")
            qe = qe / (np.linalg.norm(qe) + 1e-8)

            if self._index is not None:
                scores, indices = self._index.search(qe.reshape(1, -1), len(self._passages))
                candidates_set = set(candidates_idx)
                scored = [
                    (float(scores[0][j]), self._passages[int(indices[0][j])])
                    for j in range(len(indices[0]))
                    if int(indices[0][j]) in candidates_set
                ]
            else:
                cand_embs = self._embeddings[candidates_idx]
                sims = cand_embs @ qe
                scored = [(float(s), self._passages[candidates_idx[i]]) for i, s in enumerate(sims)]
        else:
            qv = self._tfidf(query_enriched)
            scored = [
                (self._cosine(qv, self._passages[i].get("_tfidf", {})), self._passages[i])
                for i in candidates_idx
            ]

        scored.sort(key=lambda x: x[0], reverse=True)
        seen, results = set(), []
        for _, p in scored:
            if p["id"] not in seen:
                seen.add(p["id"])
                results.append(p)
            if len(results) >= top_k:
                break
        return results


_vector_store = LegalVectorStore()


# ══════════════════════════════════════════════════════════════════
# 3.  ENTITY EXTRACTOR
# ══════════════════════════════════════════════════════════════════

_OBLIGATION_RE = re.compile(r"\b(shall|must|will|agrees?\s+to|obligat|require|commit)\b", re.I)
_LIABILITY_RE  = re.compile(r"\b(liabilit|indemnif|responsib|liable|warrant|guarantee|exclud|limit)\b", re.I)
_PENALTY_RE    = re.compile(r"\b(penalt|liquidated\s+damage|forfeit|fine|damages|compensation)\b", re.I)
_TERM_RE       = re.compile(r"\b(terminat|cancel|expir|renew|withdraw|dissolv)\b", re.I)


def extract_entities(clause_text: str) -> Dict[str, List[str]]:
    sentences = re.split(r"[.;]\s+", clause_text)

    def _collect(pattern: re.Pattern) -> List[str]:
        hits: List[str] = []
        for sent in sentences:
            if pattern.search(sent):
                clean = sent.strip()[:120]
                if clean and clean not in hits:
                    hits.append(clean)
            if len(hits) >= 3:
                break
        return hits

    return {
        "obligations": _collect(_OBLIGATION_RE),
        "liabilities":  _collect(_LIABILITY_RE),
        "penalties":    _collect(_PENALTY_RE),
        "termination":  _collect(_TERM_RE),
    }


# ══════════════════════════════════════════════════════════════════
# 4.  RULE ENGINE
# ══════════════════════════════════════════════════════════════════

@dataclass
class RuleFlag:
    rule_id: str
    severity: str
    flag_message: str
    explanation: str
    law_hint: str


UNIVERSAL_RULES: List[Dict] = [
    {
        "id": "R-UNL-LIAB",
        "patterns": [r"unlimited\s+liability", r"without\s+any\s+limit", r"no\s+cap\s+on\s+liability"],
        "severity": "HIGH",
        "flag": "Unlimited liability exposure detected",
        "explanation": (
            "Unlimited liability clauses expose a party to uncapped financial risk. Courts in multiple "
            "jurisdictions have limited or voided such clauses under public policy, reasonableness, "
            "or unconscionability doctrines."
        ),
        "law_hint": "Section 73 ICA / UCC § 2-302 / UCTA 1977 s.11",
    },
    {
        "id": "R-NO-TERM",
        "patterns": [r"perpetual", r"irrevocable", r"no\s+right\s+to\s+terminat", r"shall\s+not\s+terminat"],
        "severity": "HIGH",
        "flag": "No termination right – contract may bind parties indefinitely",
        "explanation": (
            "Contracts without termination provisions can trap parties in indefinite obligations. "
            "Most jurisdictions imply a right to terminate on reasonable notice for contracts of indefinite duration."
        ),
        "law_hint": "General Contract Law – Implied Termination Rights",
    },
    {
        "id": "R-BROAD-INDEM",
        "patterns": [r"indemnif", r"hold\s+harmless"],
        "severity": "MEDIUM",
        "flag": "Broad indemnification language detected",
        "explanation": (
            "Indemnification clauses covering all losses without cap or carve-outs for the indemnitee's "
            "own negligence create significant one-sided exposure. Scope, financial cap, and insurance "
            "backing should be clearly defined."
        ),
        "law_hint": "UCTA 1977 s.4 / ICA 1872 s.23 / UCC Implied Good Faith",
    },
    {
        "id": "R-PENALTY",
        "patterns": [r"\bpenalt", r"liquidated\s+damage", r"\bforfeit"],
        "severity": "MEDIUM",
        "flag": "Penalty / liquidated damages clause detected",
        "explanation": (
            "Penalty clauses must represent a genuine pre-estimate of loss to be enforceable. "
            "Punitive or arbitrary damages clauses risk being struck down as unenforceable penalties."
        ),
        "law_hint": "ICA s.74 / UCC § 2-718 / Cavendish v Makdessi [2015]",
    },
    {
        "id": "R-FORCE-MAJEURE",
        "patterns": [r"force\s+majeure", r"act\s+of\s+god", r"beyond.*control", r"extraordinary.*event"],
        "severity": "LOW",
        "flag": "Force majeure clause present – review triggering events and notice requirements",
        "explanation": (
            "Force majeure clauses excuse non-performance on specified events. Vague triggering events, "
            "lack of notice requirements, and absent mitigation obligations can cause disputes."
        ),
        "law_hint": "ICA s.56 / CISG Art.79 / Common Law Frustration",
    },
    {
        "id": "R-WAIVER",
        "patterns": [r"\bwaive[rs]?\b", r"waiver\s+of\s+rights"],
        "severity": "MEDIUM",
        "flag": "Waiver language – risk of inadvertent rights surrender",
        "explanation": (
            "Broad waiver language may inadvertently surrender material contractual rights. "
            "Waivers should be specific, in writing, and not operate as a general release of future claims."
        ),
        "law_hint": "General Contract Law – Waiver and Estoppel",
    },
    {
        "id": "R-EXCLUS-JURIS",
        "patterns": [r"exclusive\s+jurisdiction", r"sole\s+jurisdiction"],
        "severity": "LOW",
        "flag": "Exclusive jurisdiction clause – verify forum alignment with business interests",
        "explanation": (
            "Exclusive jurisdiction clauses are generally enforceable but must align with business "
            "operations and be agreed knowingly."
        ),
        "law_hint": "Carnival Cruise Lines v Shute (1991) / UCTA s.2",
    },
    {
        "id": "R-RESTRAINT-TRADE",
        "patterns": [r"non.compete", r"non.solicitation", r"restraint\s+of\s+trade", r"\bexclusivity\b"],
        "severity": "MEDIUM",
        "flag": "Restraint of trade / non-compete clause detected",
        "explanation": (
            "Non-compete and non-solicitation clauses must be reasonable in scope, geography, and "
            "duration to be enforceable. Overly broad restraints are void or blue-pencilled."
        ),
        "law_hint": "ICA 1872 s.27 / English Common Law – Restraint of Trade",
    },
    {
        "id": "R-CONSEQUENTIAL-EXCL",
        "patterns": [r"consequential.*damage", r"indirect.*damage", r"exclude.*consequential"],
        "severity": "MEDIUM",
        "flag": "Consequential damages exclusion – check reasonableness and essential purpose",
        "explanation": (
            "Clauses excluding consequential or indirect damages limit recovery to direct loss only. "
            "These must pass reasonableness tests and may be invalid if they deprive a party of any meaningful remedy."
        ),
        "law_hint": "UCC § 2-719 / UCTA 1977 s.3 / Hadley v Baxendale (1854)",
    },
]

JURISDICTION_EXTRA_RULES: Dict[str, List[Dict]] = {
    "india": [
        {
            "id": "R-IN-ARBIT-SEAT",
            "patterns": [r"arbitration", r"arbitral"],
            "severity": "LOW",
            "flag": "Arbitration clause – verify seat and institutional rules",
            "explanation": (
                "Under the Arbitration and Conciliation Act 1996, the seat of arbitration determines "
                "supervisory court jurisdiction. Specify seat, institution (DIAC, SIAC, ICC), and procedural rules."
            ),
            "law_hint": "Arbitration and Conciliation Act 1996 (India)",
        },
    ],
    "us": [
        {
            "id": "R-US-CLASS-WAIVER",
            "patterns": [r"class\s+action.*waiver", r"waiver.*class\s+action", r"individual.*arbitration"],
            "severity": "LOW",
            "flag": "Class action waiver in arbitration – generally enforceable under FAA",
            "explanation": "Under AT&T Mobility v Concepcion (2011), class action waivers are generally enforceable under the FAA.",
            "law_hint": "Federal Arbitration Act / AT&T v Concepcion (2011)",
        },
    ],
    "uk": [
        {
            "id": "R-UK-UCTA-CONSUMER",
            "patterns": [r"\bconsumer\b", r"\bb2c\b", r"\bretail\b"],
            "severity": "HIGH",
            "flag": "Consumer contract – Consumer Rights Act 2015 applies",
            "explanation": (
                "Consumer contracts are governed by the Consumer Rights Act 2015. Unfair terms are "
                "not binding on the consumer. Terms causing significant imbalance to the consumer's detriment will be struck down."
            ),
            "law_hint": "Consumer Rights Act 2015, Section 62",
        },
    ],
}

ABSENCE_CHECKS: Dict[str, Dict] = {
    "R-NO-GOV-LAW": {
        "patterns": [r"governed\s+by", r"governing\s+law", r"laws\s+of", r"under\s+the\s+law\s+of"],
        "severity": "HIGH",
        "flag": "No governing law clause identified",
        "explanation": (
            "Absence of a governing law clause creates uncertainty in multi-jurisdictional disputes. "
            "Courts will apply conflict-of-laws rules to determine applicable law."
        ),
        "law_hint": "General Principles – Choice of Law",
    },
    "R-NO-DISPUTE": {
        "patterns": [r"arbitrat", r"litigation", r"dispute\s+resolution", r"\bcourt\b", r"tribunal"],
        "severity": "MEDIUM",
        "flag": "No dispute resolution mechanism identified",
        "explanation": (
            "Contracts without a dispute resolution clause leave parties without clear recourse. "
            "Specify arbitration or court jurisdiction with seat and governing procedure."
        ),
        "law_hint": "General Principles – Dispute Resolution",
    },
}


def run_rule_engine(clause_text: str, jurisdiction: str) -> List[RuleFlag]:
    text_lower = clause_text.lower()
    flags: List[RuleFlag] = []

    all_rules = list(UNIVERSAL_RULES) + JURISDICTION_EXTRA_RULES.get(jurisdiction, [])
    for rule in all_rules:
        patterns = rule.get("patterns", [])
        if patterns and any(re.search(p, text_lower) for p in patterns):
            flags.append(RuleFlag(
                rule_id=rule["id"],
                severity=rule["severity"],
                flag_message=rule["flag"],
                explanation=rule["explanation"],
                law_hint=rule["law_hint"],
            ))

    for rule_id, cfg in ABSENCE_CHECKS.items():
        if not any(re.search(p, text_lower) for p in cfg["patterns"]):
            flags.append(RuleFlag(
                rule_id=rule_id,
                severity=cfg["severity"],
                flag_message=cfg["flag"],
                explanation=cfg["explanation"],
                law_hint=cfg["law_hint"],
            ))

    return flags


# ══════════════════════════════════════════════════════════════════
# 5.  CONFIDENCE SCORER
# ══════════════════════════════════════════════════════════════════

def compute_confidence(
    rule_flags: List[RuleFlag],
    retrieved_passages: List[Dict],
    llm_success: bool,
    clause_length: int,
) -> float:
    score = 0.30
    if len(retrieved_passages) >= 4:
        score += 0.25
    elif len(retrieved_passages) >= 2:
        score += 0.15
    if llm_success:
        score += 0.25
    if rule_flags:
        score += 0.10
    if clause_length > 300:
        score += 0.10
    elif clause_length > 100:
        score += 0.05
    return round(min(score, 0.95), 2)


# ══════════════════════════════════════════════════════════════════
# 6.  LLM REASONER
# ══════════════════════════════════════════════════════════════════

JURISDICTION_CONTEXT: Dict[str, Dict] = {
    "india": {
        "name": "India",
        "primary_laws": "Indian Contract Act 1872 (ICA), Specific Relief Act 1963, Arbitration and Conciliation Act 1996",
        "key_risk": "Unlimited liability and unconscionable penalty clauses may be void under Sections 23 and 74 ICA.",
    },
    "us": {
        "name": "United States",
        "primary_laws": "Uniform Commercial Code (UCC), Federal Arbitration Act (FAA), Restatement (Second) of Contracts",
        "key_risk": "Unconscionable clauses (UCC § 2-302) and unreasonable limitation of remedies (§ 2-719) risk non-enforcement.",
    },
    "uk": {
        "name": "United Kingdom",
        "primary_laws": "Unfair Contract Terms Act 1977 (UCTA), Consumer Rights Act 2015, Arbitration Act 1996",
        "key_risk": "Exclusion and limitation clauses must pass the UCTA 1977 reasonableness test to be enforceable.",
    },
}


def _call_ollama(prompt: str, temperature: float = 0.25) -> str:
    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": "qwen2.5:0.5b",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": temperature, "num_predict": 650},
            },
            timeout=65,
        )
        if resp.status_code == 200:
            return resp.json().get("response", "")
    except Exception as exc:
        logger.warning("LegalReasoningEngine – Ollama failed: %s", exc)
    return ""


def _parse_llm_json(raw: str, fallback: Dict) -> Tuple[Dict, bool]:
    for pattern in [r'\{[^{}]*"risk_level"[^{}]*\}', r'\{.*?"risk_level".*?\}', r'\{.*\}']:
        try:
            m = re.search(pattern, raw, re.DOTALL)
            if m:
                obj = json.loads(m.group())
                if "risk_level" in obj:
                    return obj, True
        except Exception:
            pass
    return fallback, False


def _build_llm_prompt(
    clause_text: str,
    jurisdiction: str,
    entities: Dict,
    retrieved_passages: List[Dict],
    rule_flags: List[RuleFlag],
) -> str:
    jctx = JURISDICTION_CONTEXT.get(jurisdiction, JURISDICTION_CONTEXT["india"])

    passages_text = ""
    for i, p in enumerate(retrieved_passages[:4], 1):
        passages_text += f"\n[{i}] {p['title']}\n    Citation: {p['citation']}\n    Text: {p['text'][:280]}\n"

    flags_text = (
        "\n".join(f"- [{f.severity}] {f.flag_message} (Ref: {f.law_hint})" for f in rule_flags[:6])
        or "No rule flags triggered."
    )
    entities_text = json.dumps({k: v[:2] for k, v in entities.items() if v}, indent=2)

    return f"""You are a senior legal analyst specialising in {jctx['name']} contract law.

JURISDICTION: {jctx['name']}
APPLICABLE LAWS: {jctx['primary_laws']}
KEY LEGAL RISK: {jctx['key_risk']}

CLAUSE UNDER ANALYSIS:
---
{clause_text[:650]}
---

EXTRACTED ENTITIES:
{entities_text}

RETRIEVED LEGAL KNOWLEDGE:
{passages_text}

RULE-BASED FLAGS:
{flags_text}

Respond ONLY with valid JSON, no markdown fences:
{{
  "risk_level": "<CRITICAL|HIGH|MEDIUM|LOW>",
  "compliance_status": "<Compliant|Non-Compliant|Partially Compliant>",
  "issues": [
    {{
      "issue": "<issue title>",
      "reason": "<why this is a legal risk>",
      "law_reference": "<exact statute and section>",
      "case_reference": "<case name and citation>",
      "severity": "<CRITICAL|HIGH|MEDIUM|LOW>"
    }}
  ],
  "explanation": "<overall 3-4 sentence legal explanation with statute citations>",
  "suggested_clause": "<a legally compliant rewrite of the clause>"
}}"""


# ══════════════════════════════════════════════════════════════════
# 7.  MAIN ENGINE
# ══════════════════════════════════════════════════════════════════

JURISDICTION_LAWS_LIST: Dict[str, List[str]] = {
    "india": [
        "Indian Contract Act, 1872 (ICA)",
        "Specific Relief Act, 1963",
        "Arbitration and Conciliation Act, 1996",
        "Indian Evidence Act, 1872",
    ],
    "us": [
        "Uniform Commercial Code (UCC) – Articles 1 & 2",
        "Restatement (Second) of Contracts",
        "Federal Arbitration Act (FAA), 9 U.S.C. §§ 1-16",
        "State-specific contract statutes",
    ],
    "uk": [
        "Unfair Contract Terms Act 1977 (UCTA)",
        "Consumer Rights Act 2015",
        "Sale of Goods Act 1979",
        "Arbitration Act 1996 (UK)",
    ],
}


class LegalReasoningEngine:
    """
    Orchestrates: Entity Extraction → RAG Retrieval → Rule Engine
                  → LLM Reasoning → Confidence Scoring → Structured Output
    """

    def analyze(self, clause_text: str, jurisdiction: str) -> Dict:
        jurisdiction = jurisdiction.lower().strip()
        if jurisdiction not in ("india", "us", "uk"):
            jurisdiction = "india"

        entities = extract_entities(clause_text)

        query = clause_text + " " + " ".join(sum(entities.values(), []))
        retrieved_passages = _vector_store.retrieve(query, jurisdiction, top_k=5)

        rule_flags = run_rule_engine(clause_text, jurisdiction)

        prompt = _build_llm_prompt(clause_text, jurisdiction, entities, retrieved_passages, rule_flags)
        raw_llm = _call_ollama(prompt)

        jctx = JURISDICTION_CONTEXT.get(jurisdiction, JURISDICTION_CONTEXT["india"])
        severity_from_rules = (
            "HIGH" if any(f.severity in ("CRITICAL", "HIGH") for f in rule_flags)
            else ("MEDIUM" if rule_flags else "LOW")
        )
        fallback_issues = [
            {
                "issue": f.flag_message,
                "reason": f.explanation,
                "law_reference": f.law_hint,
                "case_reference": "Consult a qualified legal professional",
                "severity": f.severity,
            }
            for f in rule_flags[:4]
        ]
        fallback = {
            "risk_level": severity_from_rules,
            "compliance_status": "Partially Compliant" if rule_flags else "Compliant",
            "issues": fallback_issues,
            "explanation": (
                f"Under {jctx['name']} law ({jctx['primary_laws']}), this clause requires review. "
                f"{jctx['key_risk']} "
                + (f"Rule analysis identified {len(rule_flags)} issue(s)." if rule_flags else "No critical rule flags triggered.")
            ),
            "suggested_clause": clause_text,
        }

        llm_result, llm_success = _parse_llm_json(raw_llm, fallback)

        confidence = compute_confidence(rule_flags, retrieved_passages, llm_success, len(clause_text))

        risk_level = str(llm_result.get("risk_level", severity_from_rules)).upper()
        if risk_level not in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
            risk_level = severity_from_rules

        issues = llm_result.get("issues", fallback_issues)
        if not isinstance(issues, list):
            issues = fallback_issues

        rule_flags_out = [
            {
                "rule_id": f.rule_id,
                "severity": f.severity,
                "flag_message": f.flag_message,
                "explanation": f.explanation,
                "law_hint": f.law_hint,
            }
            for f in rule_flags
        ]

        passages_out = [
            {
                "id": p["id"],
                "type": p["type"],
                "title": p["title"],
                "citation": p["citation"],
                "text": p["text"][:350],
                "jurisdiction": p["jurisdiction"],
            }
            for p in retrieved_passages
        ]

        return {
            "clause_text": clause_text[:800],
            "jurisdiction": {
                "key": jurisdiction,
                "name": jctx["name"],
                "applicable_laws": JURISDICTION_LAWS_LIST.get(jurisdiction, []),
            },
            "risk_level": risk_level,
            "compliance_status": str(llm_result.get("compliance_status", fallback["compliance_status"])),
            "confidence_score": confidence,
            "issues": issues[:6],
            "explanation": str(llm_result.get("explanation", fallback["explanation"]))[:800],
            "suggested_clause": str(llm_result.get("suggested_clause", clause_text))[:1000],
            "retrieved_passages": passages_out,
            "rule_flags": rule_flags_out,
            "entities": entities,
            "analyzed_at": datetime.utcnow().isoformat(),
        }


_engine = LegalReasoningEngine()


def analyze_clause(clause_text: str, jurisdiction: str) -> Dict:
    """Public API – call this from Django views."""
    return _engine.analyze(clause_text, jurisdiction)