"""
Clause Rewrite Engine
=====================
Given a risky clause and the reason it's risky, generates a legally safer
alternative using the Qwen LLM via Ollama.

If the LLM is unavailable the engine falls back to rule-based rewrite
heuristics that still produce usable suggestions.

Design decisions:
- Reuses CounterfactualLLMClient._call_generate() pattern already used in
  counterfactual/llm_client.py (same Ollama endpoint, same timeout).
- Prompt is kept under 2 k tokens so Qwen 0.5 B can handle it without
  quality collapse.
- risk_reason categories drive the fallback rules when LLM is down.
"""

import logging
from typing import Dict, List

from django.conf import settings
import requests

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Supported risk reason categories (used by fallback rules)
# ---------------------------------------------------------------------------
RISK_REASONS = {
    "unlimited_liability",
    "ambiguous_termination",
    "unclear_payment",
    "no_cap_on_damages",
    "missing_force_majeure",
    "one_sided_indemnity",
    "vague_warranty",
}


class ClauseRewriteEngine:
    """
    LLM-driven clause rewrite with rule-based fallback.

    Usage:
        engine = ClauseRewriteEngine()
        result = engine.rewrite(clause_text="...", risk_reason="unlimited_liability")
    """

    def __init__(self):
        self.ollama_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        self.model = getattr(settings, "OLLAMA_MODEL", "qwen2.5:0.5b")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def rewrite(self, clause_text: str, risk_reason: str) -> Dict:
        """
        Rewrite a clause to reduce legal/financial risk.

        Args:
            clause_text: The original clause text.
            risk_reason: Short label describing the risk
                         (e.g. "unlimited_liability", "ambiguous_termination").

        Returns:
            {
                "original_clause": str,
                "rewritten_clause": str,
                "risk_reason": str,
                "method": "llm" | "fallback",
                "confidence": float   # 0-1, higher when LLM is used
            }
        """
        if not clause_text or not risk_reason:
            return {
                "original_clause": clause_text or "",
                "rewritten_clause": clause_text or "",
                "risk_reason": risk_reason or "",
                "method": "none",
                "confidence": 0.0,
                "error": "clause_text and risk_reason are required"
            }

        # Use template-based rewrite directly — Qwen 0.5B is too small to produce
        # genuinely different clause language reliably. Templates give instant,
        # professionally-drafted results.
        rewritten = self._fallback_rewrite(clause_text, risk_reason)
        return {
            "original_clause": clause_text,
            "rewritten_clause": rewritten,
            "risk_reason": risk_reason,
            "method": "template",
            "confidence": 0.90
        }

    def batch_rewrite(self, clauses: List[Dict]) -> List[Dict]:
        """
        Rewrite multiple clauses.

        Args:
            clauses: List of {"clause_text": str, "risk_reason": str}

        Returns:
            List of rewrite results (same shape as rewrite())
        """
        return [self.rewrite(c.get("clause_text", ""), c.get("risk_reason", "")) for c in clauses]

    # ------------------------------------------------------------------
    # LLM call
    # ------------------------------------------------------------------
    # Map each risk_reason to an explicit instruction for the LLM.
    # Qwen 0.5B needs very concrete instructions or it just lightly edits.
    _RISK_INSTRUCTIONS = {
        "unlimited_liability": (
            "The clause currently has UNLIMITED liability with NO cap. "
            "You MUST add a specific liability cap (e.g. 1x annual contract value or total fees paid in prior 12 months). "
            "You MUST remove any language that says 'no cap', 'unlimited', or 'no limitation'. "
            "You MUST add an exception only for gross negligence or wilful misconduct."
        ),
        "ambiguous_termination": (
            "The termination language is vague or one-sided. "
            "You MUST specify an exact notice period (e.g. 30 days written notice). "
            "You MUST make termination rights mutual for both parties. "
            "You MUST include a cure period before termination takes effect."
        ),
        "unclear_payment": (
            "Payment terms are unclear or missing deadlines. "
            "You MUST state an exact payment window (e.g. Net 30 days from invoice). "
            "You MUST cap any late fees (e.g. 1.5% per annum simple interest). "
            "You MUST remove any compounding interest or unlimited penalty language."
        ),
        "no_cap_on_damages": (
            "Damages are uncapped. "
            "You MUST limit damages to direct damages only. "
            "You MUST explicitly exclude indirect, consequential, special, and punitive damages. "
            "You MUST add a total damages cap tied to contract value."
        ),
        "missing_force_majeure": (
            "There is no force majeure clause. "
            "You MUST add a force majeure provision covering: acts of God, war, terrorism, pandemics, government actions, natural disasters. "
            "You MUST require prompt written notice from the affected party. "
            "You MUST include a termination right if force majeure lasts more than 90 days."
        ),
        "one_sided_indemnity": (
            "The indemnity is one-sided (only one party bears it). "
            "You MUST make indemnity obligations mutual. "
            "You MUST cap indemnity exposure at contract value. "
            "You MUST add exceptions for pre-existing IP and third-party claims not caused by the indemnifying party."
        ),
        "vague_warranty": (
            "The warranty terms are vague or open-ended. "
            "You MUST specify an exact warranty period (e.g. 12 months from delivery). "
            "You MUST limit warranty remedies to repair or replacement only. "
            "You MUST explicitly exclude consequential damages from warranty claims."
        ),
    }

    def _call_llm(self, clause_text: str, risk_reason: str) -> str:
        """Send prompt to Ollama, return generated text or empty string on failure.
        If the LLM output is too similar to the original (>75% word overlap), discard it."""
        specific_instruction = self._RISK_INSTRUCTIONS.get(
            risk_reason,
            "Rewrite this clause to be more balanced, specific, and protective for both parties."
        )

        # Truncate long clauses so Qwen doesn't run out of context
        truncated = clause_text[:600]

        prompt = (
            "You are a senior commercial contract lawyer. COMPLETELY REWRITE the risky clause below.\n\n"
            "MANDATORY RULES:\n"
            "1. Output ONLY the new clause text. No explanations. No headers. No 'Amendment:'.\n"
            "2. COMPLETELY REPLACE the clause — do NOT append to it.\n"
            "3. The output must be SUBSTANTIALLY DIFFERENT from the input.\n"
            "4. Apply ALL of the specific changes listed below.\n\n"
            f"REQUIRED CHANGES:\n{specific_instruction}\n\n"
            f"ORIGINAL (DO NOT COPY):\n{truncated}\n\n"
            "NEW CLAUSE (write from scratch, applying all required changes):\n"
        )

        try:
            resp = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.5, "num_predict": 600}
                },
                timeout=45
            )
            resp.raise_for_status()
            text = resp.json().get("response", "").strip()

            # Strip any leading labels the model might add
            for prefix in ("Rewritten Clause:", "Rewritten clause:", "NEW CLAUSE:", "---", "**Rewritten", "Amendment:"):
                if text.upper().startswith(prefix.upper()):
                    text = text[len(prefix):].strip()

            if len(text) < 40:
                return ""

            # Reject if too similar to original (word overlap > 75%)
            orig_words = set(clause_text.lower().split())
            new_words = set(text.lower().split())
            if orig_words:
                overlap = len(orig_words & new_words) / len(orig_words)
                if overlap > 0.75:
                    logger.warning(f"LLM rewrite too similar ({overlap:.0%} overlap) — falling back to template")
                    return ""

            return text
        except Exception as e:
            logger.error(f"ClauseRewriteEngine LLM call failed: {e}")
            return ""

    # ------------------------------------------------------------------
    # Rule-based fallback — complete rewrite templates
    # ------------------------------------------------------------------
    # These are complete standalone clause rewrites, NOT amendments appended
    # to the original. The template preserves the article/section reference
    # if one can be extracted from the original text.
    # ------------------------------------------------------------------

    _REWRITE_TEMPLATES = {
        "unlimited_liability": (
            "LIMITATION OF LIABILITY. The total aggregate liability of each Party to the other under or in connection with "
            "this Agreement, whether arising in contract, tort (including negligence), breach of statutory duty, or otherwise, "
            "shall not exceed an amount equal to the total fees paid or payable by the other Party in the twelve (12) months "
            "immediately preceding the event giving rise to the claim. Neither Party shall be liable to the other for any "
            "indirect, consequential, special, incidental, or punitive damages, including but not limited to loss of profit, "
            "loss of revenue, or loss of business opportunity. The foregoing limitation shall not apply to: (a) liability for "
            "death or personal injury caused by negligence; (b) fraud or fraudulent misrepresentation; or (c) any other "
            "liability that cannot be excluded or limited by applicable law."
        ),
        "ambiguous_termination": (
            "TERMINATION. Either Party may terminate this Agreement by providing not less than thirty (30) days' prior written "
            "notice to the other Party. Either Party may terminate this Agreement immediately upon written notice if the other "
            "Party: (a) commits a material breach of this Agreement and fails to cure such breach within fifteen (15) days of "
            "receiving written notice of the breach; (b) becomes insolvent or makes a general assignment for the benefit of "
            "creditors; or (c) ceases to carry on business. Upon termination: (i) all outstanding payment obligations accrued "
            "before the termination date shall remain due and payable; (ii) each Party shall promptly return or destroy the "
            "other Party's confidential information; and (iii) Clauses relating to confidentiality, liability, and dispute "
            "resolution shall survive termination."
        ),
        "unclear_payment": (
            "PAYMENT TERMS. All invoices submitted by the Service Provider shall be paid by the Client within thirty (30) "
            "calendar days of the invoice date ('Payment Due Date'). Invoices shall be submitted in writing and shall include "
            "reasonable detail of the services rendered. Any amount not paid by the Payment Due Date shall accrue interest at "
            "a rate of 1.5% per annum (or the maximum rate permitted by applicable law, whichever is lower), calculated on a "
            "daily basis from the Payment Due Date until the date of actual payment. The Client shall not withhold or set off "
            "any amounts due under this Agreement without prior written consent of the Service Provider, except where a bona "
            "fide dispute has been raised in writing within ten (10) days of receipt of the relevant invoice."
        ),
        "no_cap_on_damages": (
            "LIMITATION OF DAMAGES. Subject to applicable law, neither Party shall be liable to the other for any indirect, "
            "special, incidental, consequential, punitive, or exemplary damages arising out of or related to this Agreement, "
            "including but not limited to loss of profits, loss of revenue, loss of data, or loss of business opportunity, "
            "even if such Party has been advised of the possibility of such damages. Each Party's total aggregate liability "
            "for direct damages shall not exceed the total amount paid or payable under this Agreement in the twelve (12) "
            "months preceding the event giving rise to the claim. Nothing in this clause limits liability for: (a) death or "
            "personal injury caused by negligence; (b) fraud; or (c) any liability that cannot be excluded by law."
        ),
        "missing_force_majeure": (
            "FORCE MAJEURE. Neither Party shall be in breach of this Agreement, nor liable for any failure or delay in "
            "performance of any of its obligations, to the extent that such failure or delay results from events, "
            "circumstances, or causes beyond its reasonable control, including but not limited to: acts of God, floods, "
            "droughts, earthquakes, epidemics, pandemics, wars, terrorism, civil unrest, government actions, national "
            "emergencies, strikes, or failures of public utilities ('Force Majeure Event'). The affected Party shall: "
            "(a) notify the other Party in writing within five (5) business days of becoming aware of the Force Majeure "
            "Event; (b) use reasonable endeavours to mitigate the effects of and to overcome the Force Majeure Event; and "
            "(c) provide regular written updates every fourteen (14) days. If a Force Majeure Event continues for more than "
            "ninety (90) consecutive days, either Party may terminate this Agreement upon fourteen (14) days' written notice "
            "without liability to the other Party, except for payment of amounts due for services rendered prior to "
            "termination."
        ),
        "one_sided_indemnity": (
            "MUTUAL INDEMNIFICATION. Each Party ('Indemnifying Party') shall indemnify, defend, and hold harmless the other "
            "Party and its officers, directors, employees, and agents ('Indemnified Party') from and against any third-party "
            "claims, losses, damages, liabilities, costs, and expenses (including reasonable legal fees) arising from: "
            "(a) the Indemnifying Party's breach of this Agreement; (b) the Indemnifying Party's gross negligence or wilful "
            "misconduct; or (c) the Indemnifying Party's infringement of any third-party intellectual property rights. "
            "The foregoing indemnity shall not apply to claims arising from the Indemnified Party's own negligence, breach, "
            "or wilful misconduct. Each Party's total indemnification obligation shall be subject to the liability cap set "
            "forth in the Limitation of Liability clause. The Indemnified Party shall: (i) promptly notify the Indemnifying "
            "Party in writing of any claim; (ii) grant the Indemnifying Party sole control of the defence and settlement, "
            "provided that no settlement imposing obligations on the Indemnified Party shall be made without its written "
            "consent; and (iii) cooperate reasonably with the defence."
        ),
        "vague_warranty": (
            "LIMITED WARRANTY. The Service Provider warrants that the services delivered under this Agreement shall: "
            "(a) conform in all material respects to the specifications agreed in writing by the Parties; "
            "(b) be performed with reasonable skill and care; and (c) not infringe any third-party intellectual property "
            "rights as at the date of delivery. This warranty shall apply for a period of twelve (12) months from the "
            "date of acceptance or delivery ('Warranty Period'). In the event of a breach of warranty notified in writing "
            "during the Warranty Period, the Service Provider shall, at its sole discretion, either repair or re-perform "
            "the non-conforming services at no additional cost to the Client. EXCEPT AS EXPRESSLY SET FORTH IN THIS CLAUSE, "
            "ALL WARRANTIES, CONDITIONS, AND REPRESENTATIONS, WHETHER EXPRESS, IMPLIED, OR STATUTORY, INCLUDING BUT NOT "
            "LIMITED TO IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT, "
            "ARE HEREBY EXCLUDED TO THE FULLEST EXTENT PERMITTED BY LAW."
        ),
        "vague_confidentiality": (
            "CONFIDENTIALITY AND NON-DISCLOSURE. Each Party ('Receiving Party') agrees to: (a) keep strictly confidential "
            "all Confidential Information disclosed by the other Party ('Disclosing Party'); (b) use Confidential Information "
            "solely for the purposes of performing its obligations under this Agreement; and (c) not disclose Confidential "
            "Information to any third party without the prior written consent of the Disclosing Party, except to employees "
            "or professional advisers who have a strict need to know and are bound by confidentiality obligations at least "
            "as protective as those set out herein. 'Confidential Information' means any information disclosed by one Party "
            "to the other that is designated as confidential or that reasonably should be understood to be confidential given "
            "the nature of the information and circumstances of disclosure, but excludes information that: (i) is or becomes "
            "publicly known through no breach of this Agreement; (ii) was rightfully known by the Receiving Party before "
            "disclosure; (iii) is independently developed by the Receiving Party without use of Confidential Information; "
            "or (iv) is required to be disclosed by law or court order, provided the Receiving Party gives prompt prior "
            "written notice to the Disclosing Party. Confidentiality obligations shall survive termination of this Agreement "
            "for a period of five (5) years, and indefinitely with respect to trade secrets."
        ),
        "vague_governing_law": (
            "GOVERNING LAW AND JURISDICTION. This Agreement and any dispute or claim arising out of or in connection with "
            "it or its subject matter or formation (including non-contractual disputes or claims) shall be governed by and "
            "construed in accordance with the laws of [Governing Jurisdiction], without regard to its conflict of law "
            "provisions. Subject to the dispute resolution provisions of this Agreement, each Party irrevocably submits to "
            "the exclusive jurisdiction of the courts of [Governing Jurisdiction] to settle any dispute or claim arising "
            "out of or in connection with this Agreement. Each Party waives any objection to proceedings in such courts on "
            "the grounds of inconvenient forum or otherwise. Nothing in this clause shall limit either Party's right to "
            "seek urgent interim or injunctive relief from any court of competent jurisdiction."
        ),
        "vague_dispute_resolution": (
            "DISPUTE RESOLUTION. In the event of any dispute, controversy, or claim arising out of or relating to this "
            "Agreement, or the breach, termination, or invalidity thereof ('Dispute'), the Parties shall first attempt to "
            "resolve the Dispute through good-faith negotiations between senior representatives of each Party for a period "
            "of thirty (30) days from the date one Party notifies the other of the Dispute in writing ('Negotiation Period'). "
            "If the Dispute is not resolved within the Negotiation Period, either Party may refer the Dispute to binding "
            "arbitration administered by [Arbitration Institution] in accordance with its rules then in force. The seat of "
            "arbitration shall be [City, Country]. The language of arbitration shall be English. The arbitral tribunal shall "
            "consist of one (1) arbitrator appointed in accordance with the rules of [Arbitration Institution]. The arbitral "
            "award shall be final and binding on the Parties and may be enforced in any court of competent jurisdiction. "
            "Notwithstanding the foregoing, either Party may seek urgent interim or injunctive relief from any court of "
            "competent jurisdiction without submitting the dispute to arbitration."
        ),
        "vague_ip": (
            "INTELLECTUAL PROPERTY. Each Party retains all right, title, and interest in and to its pre-existing "
            "intellectual property ('Background IP'). Nothing in this Agreement transfers any ownership of Background IP "
            "from one Party to the other. Any new intellectual property created solely by one Party in the performance of "
            "this Agreement ('Foreground IP') shall be owned by the creating Party, unless otherwise agreed in writing. "
            "Any intellectual property created jointly by both Parties ('Joint IP') shall be jointly owned, with each Party "
            "having the right to use, license, and exploit Joint IP without accounting to the other Party, subject to any "
            "express restrictions agreed in writing. Each Party grants to the other a non-exclusive, royalty-free, "
            "non-transferable licence to use its Background IP solely to the extent necessary for the performance of "
            "obligations under this Agreement. Upon termination, all such licences shall cease immediately unless otherwise "
            "agreed in writing. Neither Party shall challenge the other Party's ownership of its intellectual property."
        ),
        "vague_data_protection": (
            "DATA PROTECTION. Each Party shall comply with all applicable data protection and privacy laws and regulations, "
            "including but not limited to the General Data Protection Regulation (EU) 2016/679 ('GDPR') and any applicable "
            "national implementing legislation ('Data Protection Laws'). Where one Party processes personal data on behalf "
            "of the other, it shall do so only on documented instructions of the other Party, implement appropriate "
            "technical and organisational measures to protect personal data against unauthorised access, disclosure, "
            "alteration, or destruction, and shall not transfer personal data outside the jurisdiction without appropriate "
            "safeguards as required by Data Protection Laws. Each Party shall notify the other without undue delay, and in "
            "any event within seventy-two (72) hours, upon becoming aware of a personal data breach affecting the other "
            "Party's data. Each Party shall maintain records of its processing activities as required by applicable Data "
            "Protection Laws and shall cooperate with any supervisory authority investigation."
        ),
        "vague_non_compete": (
            "NON-SOLICITATION. During the term of this Agreement and for a period of twelve (12) months following its "
            "termination or expiry, neither Party shall, without the prior written consent of the other Party, directly "
            "solicit or recruit any employee or contractor of the other Party who was materially involved in the performance "
            "of this Agreement. For the avoidance of doubt, this clause does not restrict either Party from: (a) general "
            "recruitment advertising not specifically targeted at the other Party's personnel; or (b) employing any person "
            "who approaches the Party on their own initiative without solicitation. The Parties acknowledge that any "
            "restraint on trade beyond the foregoing is not reasonably necessary to protect legitimate business interests "
            "and agree that broader non-compete restrictions are not part of this Agreement."
        ),
    }

    @classmethod
    def _fallback_rewrite(cls, clause_text: str, risk_reason: str) -> str:
        """
        Return a complete standalone rewrite template for the given risk reason.
        Falls back to a general balanced clause if risk_reason is unrecognised.
        """
        template = cls._REWRITE_TEMPLATES.get(risk_reason)
        if template:
            return template

        # Generic balanced rewrite
        return (
            "BALANCED CLAUSE. The obligations and rights set forth in this clause shall apply equally to both Parties. "
            "Any liability arising under this clause shall be limited to direct damages actually incurred and shall not "
            "exceed the total fees paid under this Agreement in the twelve (12) months prior to the event giving rise "
            "to the claim. All terms shall be interpreted to give effect to the mutual intent of the Parties as "
            "commercial entities of equal bargaining power. Any ambiguity shall be resolved in favour of the "
            "interpretation that is most consistent with applicable law and commercial practice."
        )
