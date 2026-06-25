"""
Debug Negotiation Predictor
Investigates why predictor returns default values instead of real data
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from ai.vectorstore import get_qdrant_client, NEGOTIATION_HISTORY_COLLECTION
from ai.embedding import embed
from ai.negotiation_predictor import predict_outcome
from core.models import Contract, Clause
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def investigate_qdrant_data():
    """Check what's actually in Qdrant"""
    client = get_qdrant_client()

    logger.info("=" * 60)
    logger.info("QDRANT DATA INVESTIGATION")
    logger.info("=" * 60)

    # Get collection info
    collection_info = client.get_collection(NEGOTIATION_HISTORY_COLLECTION)
    logger.info(f"\nCollection: {NEGOTIATION_HISTORY_COLLECTION}")
    logger.info(f"Total vectors: {collection_info.points_count}")
    logger.info(f"Vector size: {collection_info.config.params.vectors.size}")

    # Scroll through first 20 records
    logger.info("\n--- Sample Records ---")
    results = client.scroll(
        collection_name=NEGOTIATION_HISTORY_COLLECTION,
        limit=20,
        with_payload=True,
        with_vectors=False
    )

    points = results[0]

    # Collect clause types
    clause_types = {}
    counterparties = set()
    redline_counts = []
    stall_risks = []

    for i, point in enumerate(points, 1):
        payload = point.payload
        clause_type = payload.get('clause_type', 'UNKNOWN')
        counterparty = payload.get('counterparty', 'UNKNOWN')
        redlines = payload.get('redline_rounds', 0)
        stalled = payload.get('stalled', False)
        accepted = payload.get('accepted', False)

        clause_types[clause_type] = clause_types.get(clause_type, 0) + 1
        counterparties.add(counterparty)
        redline_counts.append(redlines)
        stall_risks.append(1 if stalled else 0)

        if i <= 5:
            logger.info(f"\n  Record {i}:")
            logger.info(f"    ID: {point.id}")
            logger.info(f"    Clause Type: {clause_type}")
            logger.info(f"    Counterparty: {counterparty}")
            logger.info(f"    Redline Rounds: {redlines}")
            logger.info(f"    Accepted: {accepted}")
            logger.info(f"    Stalled: {stalled}")
            logger.info(f"    Clause Text: {payload.get('clause_text', '')[:100]}...")

    logger.info(f"\n--- Statistics from {len(points)} records ---")
    logger.info(f"Unique clause types: {len(clause_types)}")
    logger.info(f"Clause type distribution:")
    for ct, count in sorted(clause_types.items(), key=lambda x: -x[1])[:10]:
        logger.info(f"  {ct}: {count}")

    logger.info(f"\nUnique counterparties: {len(counterparties)}")
    logger.info(f"Counterparties: {', '.join(list(counterparties)[:5])}...")

    logger.info(f"\nRedline counts: min={min(redline_counts)}, max={max(redline_counts)}, avg={sum(redline_counts)/len(redline_counts):.1f}")
    logger.info(f"Stall rate: {sum(stall_risks)/len(stall_risks)*100:.1f}%")


def test_predictor_with_real_clause():
    """Test predictor with an actual clause from database"""
    logger.info("\n" + "=" * 60)
    logger.info("PREDICTOR TEST WITH REAL CLAUSE")
    logger.info("=" * 60)

    # Get a clause from the database
    clause = Clause.objects.select_related('contract').first()

    if not clause:
        logger.error("No clauses found in database!")
        return

    clause_text = clause.extracted_text or clause.clause_name or "Test clause"
    clause_type = clause.clause_type
    counterparty = getattr(clause.contract, 'counterparty', None) or clause.contract.original_filename.replace('.pdf', '').replace('.docx', '')

    logger.info(f"\nTest Clause:")
    logger.info(f"  Type: {clause_type}")
    logger.info(f"  Counterparty: {counterparty}")
    logger.info(f"  Text: {clause_text[:200]}...")

    # Test prediction
    logger.info("\n--- Running Prediction ---")
    result = predict_outcome(clause_text, clause_type, counterparty)

    logger.info(f"\nPrediction Result:")
    logger.info(f"  Acceptance Probability: {result['acceptance_probability']}")
    logger.info(f"  Expected Redlines: {result['expected_redlines']}")
    logger.info(f"  Stall Risk: {result['stall_risk']}")
    logger.info(f"  Similar Cases: {result['similar_cases']}")

    if result['similar_cases'] == 0:
        logger.warning("\n⚠️  NO SIMILAR CASES FOUND - This is the problem!")
        logger.warning("Predictor is falling back to defaults.")


def test_vector_search_directly():
    """Test vector search with different filters"""
    logger.info("\n" + "=" * 60)
    logger.info("DIRECT VECTOR SEARCH TEST")
    logger.info("=" * 60)

    client = get_qdrant_client()

    # Get a sample clause
    clause = Clause.objects.first()
    if not clause:
        logger.error("No clauses found!")
        return

    clause_text = clause.extracted_text or clause.clause_name or "Test clause"
    clause_type = clause.clause_type

    logger.info(f"\nSearching for: {clause_type}")
    logger.info(f"Text: {clause_text[:100]}...")

    # Generate embedding
    vector = embed(clause_text)
    logger.info(f"Vector generated: shape={len(vector)}")

    # Test 1: Search WITHOUT filter
    logger.info("\n--- Test 1: Search WITHOUT clause_type filter ---")
    results_no_filter = client.query_points(
        collection_name=NEGOTIATION_HISTORY_COLLECTION,
        query=vector,
        limit=10
    ).points

    logger.info(f"Results found: {len(results_no_filter)}")
    if results_no_filter:
        for i, result in enumerate(results_no_filter[:3], 1):
            logger.info(f"  {i}. Score: {result.score:.4f}")
            logger.info(f"     Clause Type: {result.payload.get('clause_type')}")
            logger.info(f"     Redlines: {result.payload.get('redline_rounds')}")
            logger.info(f"     Stalled: {result.payload.get('stalled')}")

    # Test 2: Search WITH filter
    logger.info(f"\n--- Test 2: Search WITH clause_type filter = '{clause_type}' ---")
    from qdrant_client.http import models

    query_filter = models.Filter(
        must=[
            models.FieldCondition(
                key="clause_type",
                match=models.MatchValue(value=clause_type)
            )
        ]
    )

    results_with_filter = client.query_points(
        collection_name=NEGOTIATION_HISTORY_COLLECTION,
        query=vector,
        limit=10,
        query_filter=query_filter
    ).points

    logger.info(f"Results found: {len(results_with_filter)}")
    if results_with_filter:
        for i, result in enumerate(results_with_filter[:3], 1):
            logger.info(f"  {i}. Score: {result.score:.4f}")
            logger.info(f"     Clause Type: {result.payload.get('clause_type')}")
            logger.info(f"     Redlines: {result.payload.get('redline_rounds')}")
            logger.info(f"     Stalled: {result.payload.get('stalled')}")
    else:
        logger.warning(f"⚠️  NO RESULTS with filter for '{clause_type}'")
        logger.warning("This might be why predictor is returning defaults!")

        # Check what clause types actually exist
        logger.info("\n--- Checking actual clause types in Qdrant ---")
        all_points = client.scroll(
            collection_name=NEGOTIATION_HISTORY_COLLECTION,
            limit=100,
            with_payload=True,
            with_vectors=False
        )[0]

        existing_types = set()
        for point in all_points:
            existing_types.add(point.payload.get('clause_type', 'UNKNOWN'))

        logger.info(f"Clause types in Qdrant: {existing_types}")
        logger.info(f"Searching for: '{clause_type}'")
        logger.info(f"Match found: {clause_type in existing_types}")


if __name__ == '__main__':
    investigate_qdrant_data()
    test_predictor_with_real_clause()
    test_vector_search_directly()

    logger.info("\n" + "=" * 60)
    logger.info("DEBUG COMPLETE")
    logger.info("=" * 60)
