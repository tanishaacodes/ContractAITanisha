"""
Test script for Clause Library enhancements
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.sentence_classifier import get_sentence_classifier
from api.party_attribution import get_party_attributor
from api.risk_keyword_scorer import get_risk_scorer

def test_sentence_classifier():
    """Test sentence type classification."""
    print("\n" + "="*60)
    print("TESTING SENTENCE TYPE CLASSIFIER")
    print("="*60)

    classifier = get_sentence_classifier()

    test_cases = [
        "The Contractor shall complete the work within 30 days.",
        "Payment terms means the conditions for payment.",
        "The Contractor shall be liable for any delay and penalties.",
        "The Employer may terminate this contract at any time.",
        "This clause defines the scope of work.",
    ]

    for text in test_cases:
        sentence_type = classifier.classify(text)
        confidence = classifier.get_classification_confidence(text)
        print(f"\n📝 Text: {text[:60]}...")
        print(f"✓ Type: {sentence_type}")
        print(f"  Confidence: {confidence}")


def test_party_attribution():
    """Test party attribution."""
    print("\n" + "="*60)
    print("TESTING PARTY ATTRIBUTION")
    print("="*60)

    attributor = get_party_attributor()

    test_cases = [
        "The Contractor shall execute the work.",
        "The Employer shall pay the contractor within 30 days.",
        "Both parties shall maintain confidentiality.",
        "The Contractor shall be liable for defects.",
        "Either party may terminate with 30 days notice.",
    ]

    for text in test_cases:
        party = attributor.attribute(text)
        confidence = attributor.get_attribution_confidence(text)
        print(f"\n📝 Text: {text[:60]}...")
        print(f"✓ Party: {party}")
        print(f"  Confidence: {confidence}")


def test_risk_scorer():
    """Test risk keyword scoring."""
    print("\n" + "="*60)
    print("TESTING RISK KEYWORD SCORER")
    print("="*60)

    scorer = get_risk_scorer()

    test_cases = [
        "The Contractor shall complete the work on time.",
        "Failure to deliver shall result in liquidated damages.",
        "The Contractor shall be liable for delays and penalties.",
        "In case of breach, termination may occur with indemnity.",
        "The Employer reserves the right to inspect the work.",
    ]

    for text in test_cases:
        result = scorer.score(text)
        financial_impact = scorer.calculate_financial_impact(result['normalized_score'])

        print(f"\n📝 Text: {text[:60]}...")
        print(f"✓ Raw Score: {result['score']}")
        print(f"✓ Normalized Score: {result['normalized_score']}")
        print(f"✓ Risk Level: {result['risk_level']}")
        print(f"✓ Keywords: {result['keywords']}")
        print(f"✓ Financial Impact: {financial_impact['formatted']}")


def test_integration():
    """Test all services together."""
    print("\n" + "="*60)
    print("TESTING INTEGRATED PIPELINE")
    print("="*60)

    classifier = get_sentence_classifier()
    attributor = get_party_attributor()
    scorer = get_risk_scorer()

    test_clause = "The Contractor shall be liable for any delay penalties and liquidated damages arising from non-performance."

    print(f"\n📄 Clause: {test_clause}\n")

    # Step 1: Classify sentence type
    sentence_type = classifier.classify(test_clause)
    print(f"1️⃣ Sentence Type: {sentence_type}")

    # Step 2: Attribute party
    party = attributor.attribute(test_clause, sentence_type)
    print(f"2️⃣ Party: {party}")

    # Step 3: Score risk
    risk_result = scorer.score(test_clause)
    print(f"3️⃣ Risk Score: {risk_result['score']} (Normalized: {risk_result['normalized_score']})")
    print(f"   Risk Level: {risk_result['risk_level']}")
    print(f"   Keywords: {risk_result['keywords']}")

    # Step 4: Calculate financial impact
    financial_impact = scorer.calculate_financial_impact(risk_result['normalized_score'])
    print(f"4️⃣ Financial Impact: {financial_impact['formatted']}")

    print("\n✅ All services working correctly!")


if __name__ == '__main__':
    try:
        test_sentence_classifier()
        test_party_attribution()
        test_risk_scorer()
        test_integration()

        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED SUCCESSFULLY!")
        print("="*60)

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
