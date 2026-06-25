"""
Test Fusion Classification
==========================
Quick test to verify BERTopic + Contracts-BERT fusion is working
"""

import os
import sys
import django

# Django setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "contractai.settings")
django.setup()

from api.bertopic_classifier import classify_with_bertopic
from api.bert_intent_extractor import get_bert_extractor
from api.fusion_classifier import get_fusion_classifier

# Sample contract text (Master Service Agreement)
SAMPLE_CONTRACT = """
MASTER SERVICE AGREEMENT

This Master Service Agreement ("Agreement") is entered into as of January 1, 2024
between Company A ("Client") and Company B ("Service Provider").

1. SERVICES
Service Provider shall provide professional consulting services to Client as described
in separate Statements of Work.

2. PAYMENT TERMS
Client shall pay Service Provider within 30 days of invoice receipt. All fees are
in US Dollars.

3. LIABILITY AND INDEMNIFICATION
Service Provider's liability under this Agreement shall be limited to the fees paid
by Client. Service Provider shall indemnify Client against third-party claims arising
from Service Provider's negligence.

4. TERMINATION
Either party may terminate this Agreement with 30 days written notice.

5. CONFIDENTIALITY
Both parties agree to maintain the confidentiality of proprietary information shared
during the term of this Agreement.
"""

def test_fusion_classification():
    print("=" * 60)
    print("TESTING FUSION CLASSIFICATION")
    print("=" * 60)

    # Step 1: BERTopic Classification
    print("\n[1] BERTopic Classification...")
    topic_result = classify_with_bertopic(SAMPLE_CONTRACT)
    print(f"   Topic: {topic_result.get('contractType')}")
    print(f"   Confidence: {topic_result.get('confidenceScore')}%")
    print(f"   Topic ID: {topic_result.get('topicId')}")

    # Step 2: BERT Intent Extraction
    print("\n[2] Contracts-BERT Intent Extraction...")
    bert_extractor = get_bert_extractor()
    intent_distribution = bert_extractor.extract_intents_from_text(SAMPLE_CONTRACT)
    print(f"   Found {len(intent_distribution)} intents:")
    for intent, weight in sorted(intent_distribution.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"   - {intent}: {weight:.2%}")

    # Step 3: Fusion Classification
    print("\n[3] Fusion Classification...")
    fusion_classifier = get_fusion_classifier()
    result = fusion_classifier.classify_contract(topic_result, intent_distribution)

    print(f"\n   PRIMARY CLASSIFICATION: {result['primary_class']}")
    print(f"   CONFIDENCE: {result['confidence']:.1f}%")
    print(f"   CLASSIFIER: {result['classifier']}")

    print(f"\n   EXPLANATION:")
    print(f"   {result['explanation']}")

    print(f"\n   TOP 5 FUSED SCORES:")
    for contract_type, score in sorted(result['fused_scores'].items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"   - {contract_type}: {score:.1%}")

    print("\n" + "=" * 60)
    print("✅ FUSION CLASSIFICATION TEST COMPLETED SUCCESSFULLY")
    print("=" * 60)

    return result

if __name__ == "__main__":
    try:
        result = test_fusion_classification()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
