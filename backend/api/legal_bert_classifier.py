"""
Legal-BERT Clause Classifier for Smart Search
Integrates nlpaueb/legal-bert-base-uncased for specialized legal text classification
"""
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import List, Dict, Tuple
import numpy as np
from functools import lru_cache


class LegalBERTClassifier:
    """
    Legal-BERT classifier for clause type classification and risk scoring.
    Uses nlpaueb/legal-bert-base-uncased model fine-tuned for contract clauses.
    """

    # Clause type labels (matching CUAD taxonomy)
    CLAUSE_TYPES = [
        "force_majeure",
        "liability",
        "indemnity",
        "termination",
        "payment",
        "confidentiality",
        "intellectual_property",
        "warranty",
        "dispute_resolution",
        "governing_law",
        "assignment",
        "amendment",
        "entire_agreement",
        "severability",
        "waiver",
        "notice",
        "other"
    ]

    # Risk level mapping
    RISK_LEVELS = {
        0: "LOW",
        1: "MEDIUM",
        2: "HIGH",
        3: "CRITICAL"
    }

    def __init__(self, model_name: str = "nlpaueb/legal-bert-base-uncased"):
        """Initialize Legal-BERT model and tokenizer."""
        self.model_name = model_name
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        print(f"Loading Legal-BERT model: {model_name} on {self.device}")

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                num_labels=len(self.CLAUSE_TYPES, low_cpu_mem_usage=False),
                problem_type="single_label_classification"
            )
            self.model.to(self.device)
            self.model.eval()
            print("✅ Legal-BERT loaded successfully")
        except Exception as e:
            print(f"⚠️  Failed to load Legal-BERT: {e}")
            print("Falling back to zero-shot classification")
            self.model = None
            self.tokenizer = None

    @lru_cache(maxsize=1000)
    def classify_clause(self, text: str, top_k: int = 3) -> List[Dict[str, float]]:
        """
        Classify a clause into clause types with confidence scores.

        Args:
            text: Clause text
            top_k: Number of top predictions to return

        Returns:
            List of dicts with 'label' and 'score' keys
        """
        if not self.model or not self.tokenizer:
            return self._fallback_classify(text, top_k)

        try:
            # Tokenize
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Predict
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probs = torch.softmax(logits, dim=-1)[0]

            # Get top-k predictions
            top_probs, top_indices = torch.topk(probs, min(top_k, len(self.CLAUSE_TYPES)))

            results = []
            for prob, idx in zip(top_probs.cpu().numpy(), top_indices.cpu().numpy()):
                results.append({
                    'label': self.CLAUSE_TYPES[idx],
                    'score': float(prob)
                })

            return results

        except Exception as e:
            print(f"Legal-BERT classification error: {e}")
            return self._fallback_classify(text, top_k)

    def _fallback_classify(self, text: str, top_k: int = 3) -> List[Dict[str, float]]:
        """Keyword-based fallback classification."""
        text_lower = text.lower()
        scores = {}

        # Keyword patterns for each clause type
        patterns = {
            'force_majeure': ['force majeure', 'act of god', 'pandemic', 'natural disaster', 'war'],
            'liability': ['liability', 'damages', 'loss', 'indemnify', 'liable'],
            'indemnity': ['indemnify', 'hold harmless', 'defend', 'indemnification'],
            'termination': ['termination', 'terminate', 'cancel', 'expiration', 'end date'],
            'payment': ['payment', 'pay', 'invoice', 'fee', 'compensation', 'price'],
            'confidentiality': ['confidential', 'confidentiality', 'proprietary', 'secret'],
            'intellectual_property': ['intellectual property', 'patent', 'copyright', 'trademark', 'ip'],
            'warranty': ['warranty', 'represent', 'guarantee', 'warranted'],
            'dispute_resolution': ['dispute', 'arbitration', 'mediation', 'litigation'],
            'governing_law': ['governing law', 'jurisdiction', 'venue', 'applicable law'],
            'assignment': ['assign', 'assignment', 'transfer'],
            'amendment': ['amendment', 'modify', 'change', 'amend'],
            'entire_agreement': ['entire agreement', 'integration', 'merger clause'],
            'severability': ['severability', 'severable', 'invalid'],
            'waiver': ['waiver', 'waive', 'relinquish'],
            'notice': ['notice', 'notify', 'notification', 'inform']
        }

        for clause_type, keywords in patterns.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[clause_type] = score / len(keywords)

        if not scores:
            scores['other'] = 0.5

        # Sort and return top-k
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [{'label': label, 'score': score} for label, score in sorted_results]

    def extract_risk_score(self, text: str) -> Tuple[float, str]:
        """
        Extract risk score and level from clause text.

        Args:
            text: Clause text

        Returns:
            Tuple of (risk_score: 0.0-1.0, risk_level: str)
        """
        # High-risk keywords
        high_risk_keywords = [
            'unlimited liability', 'no limitation', 'irrevocable', 'waive',
            'indemnify', 'hold harmless', 'defend', 'exclusive remedy',
            'no right to terminate', 'perpetual', 'unconditional'
        ]

        # Medium-risk keywords
        medium_risk_keywords = [
            'limitation of liability', 'subject to', 'reasonable efforts',
            'material breach', 'cure period', 'force majeure'
        ]

        # Protective keywords (reduce risk)
        protective_keywords = [
            'may terminate', 'right to cure', 'proportional', 'cap',
            'alternative performance', 'mitigation'
        ]

        text_lower = text.lower()

        # Calculate risk score
        high_count = sum(1 for kw in high_risk_keywords if kw in text_lower)
        medium_count = sum(1 for kw in medium_risk_keywords if kw in text_lower)
        protective_count = sum(1 for kw in protective_keywords if kw in text_lower)

        risk_score = 0.0
        risk_score += high_count * 0.25
        risk_score += medium_count * 0.10
        risk_score -= protective_count * 0.05

        # Normalize to 0-1
        risk_score = max(0.0, min(1.0, risk_score))

        # Determine risk level
        if risk_score >= 0.7:
            risk_level = "CRITICAL"
        elif risk_score >= 0.5:
            risk_level = "HIGH"
        elif risk_score >= 0.3:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return risk_score, risk_level

    def batch_classify(self, texts: List[str], top_k: int = 3) -> List[List[Dict[str, float]]]:
        """
        Classify multiple clauses in batch for efficiency.

        Args:
            texts: List of clause texts
            top_k: Number of top predictions per clause

        Returns:
            List of classification results
        """
        if not self.model or not self.tokenizer:
            return [self._fallback_classify(text, top_k) for text in texts]

        try:
            # Tokenize batch
            inputs = self.tokenizer(
                texts,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Predict
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probs = torch.softmax(logits, dim=-1)

            # Process each result
            results = []
            for prob_dist in probs:
                top_probs, top_indices = torch.topk(prob_dist, min(top_k, len(self.CLAUSE_TYPES)))

                clause_results = []
                for prob, idx in zip(top_probs.cpu().numpy(), top_indices.cpu().numpy()):
                    clause_results.append({
                        'label': self.CLAUSE_TYPES[idx],
                        'score': float(prob)
                    })
                results.append(clause_results)

            return results

        except Exception as e:
            print(f"Batch classification error: {e}")
            return [self._fallback_classify(text, top_k) for text in texts]

    def compare_with_benchmark(self, clause_text: str, clause_type: str = None) -> Dict:
        """
        Compare clause with industry benchmark for the detected type.

        Args:
            clause_text: The clause to analyze
            clause_type: Optional clause type (auto-detected if not provided)

        Returns:
            Dict with comparison results
        """
        # Auto-detect clause type if not provided
        if not clause_type:
            classification = self.classify_clause(clause_text, top_k=1)
            clause_type = classification[0]['label']

        # Get risk score
        risk_score, risk_level = self.extract_risk_score(clause_text)

        # Compare with typical risk levels for clause type
        benchmark_risks = {
            'force_majeure': 0.4,
            'liability': 0.6,
            'indemnity': 0.7,
            'termination': 0.3,
            'payment': 0.2,
            'confidentiality': 0.3,
            'intellectual_property': 0.5,
            'warranty': 0.4,
            'dispute_resolution': 0.3,
            'governing_law': 0.1,
            'assignment': 0.2,
            'amendment': 0.2,
            'entire_agreement': 0.1,
            'severability': 0.1,
            'waiver': 0.2,
            'notice': 0.1,
            'other': 0.3
        }

        benchmark_risk = benchmark_risks.get(clause_type, 0.3)
        risk_delta = risk_score - benchmark_risk

        if risk_delta > 0.2:
            verdict = "HIGHER_RISK_THAN_BENCHMARK"
            recommendation = "Consider revising to align with industry standards"
        elif risk_delta < -0.1:
            verdict = "LOWER_RISK_THAN_BENCHMARK"
            recommendation = "Well-protected clause"
        else:
            verdict = "ALIGNED_WITH_BENCHMARK"
            recommendation = "Standard risk level for this clause type"

        return {
            'clause_type': clause_type,
            'risk_score': risk_score,
            'risk_level': risk_level,
            'benchmark_risk': benchmark_risk,
            'risk_delta': risk_delta,
            'verdict': verdict,
            'recommendation': recommendation
        }


# Singleton instance
_legal_bert_classifier = None

def get_legal_bert_classifier() -> LegalBERTClassifier:
    """Get or create Legal-BERT classifier singleton."""
    global _legal_bert_classifier
    if _legal_bert_classifier is None:
        _legal_bert_classifier = LegalBERTClassifier()
    return _legal_bert_classifier
