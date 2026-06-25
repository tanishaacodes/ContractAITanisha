"""
Test Predictor Fix
Verify that predictor now returns varied values from real data
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from ai.negotiation_predictor import predict_outcome
from core.models import Contract, Clause
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_predictor_with_multiple_clauses():
    """Test predictor with multiple clauses to see if values vary"""
    logger.info("=" * 60)
    logger.info("TESTING PREDICTOR WITH MULTIPLE CLAUSES")
    logger.info("=" * 60)

    # Get several clauses with different types
    clauses = Clause.objects.select_related('contract')[:10]

    if clauses.count() == 0:
        logger.error("No clauses found!")
        return

    logger.info(f"\nTesting with {clauses.count()} clauses...")

    # Track if we see varied values
    all_redlines = set()
    all_stall_risks = set()
    all_acceptance_probs = set()

    for i, clause in enumerate(clauses, 1):
        clause_text = clause.extracted_text or clause.clause_name or "Test clause"
        clause_type = clause.clause_type
        counterparty = getattr(clause.contract, 'counterparty', None) or \
                      clause.contract.original_filename.replace('.pdf', '').replace('.docx', '')

        # Run prediction
        result = predict_outcome(clause_text, clause_type, counterparty)

        logger.info(f"\nClause {i}:")
        logger.info(f"  Type: {clause_type}")
        logger.info(f"  Expected Redlines: {result['expected_redlines']}")
        logger.info(f"  Stall Risk: {result['stall_risk']}  ({result['stall_risk']*100:.0f}%)")
        logger.info(f"  Acceptance Prob: {result['acceptance_probability']}")
        logger.info(f"  Similar Cases: {result['similar_cases']}")

        all_redlines.add(result['expected_redlines'])
        all_stall_risks.add(result['stall_risk'])
        all_acceptance_probs.add(result['acceptance_probability'])

    logger.info("\n" + "=" * 60)
    logger.info("RESULTS SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Unique redline counts: {sorted(all_redlines)}")
    logger.info(f"Unique stall risks: {sorted(all_stall_risks)}")
    logger.info(f"Unique acceptance probs: {sorted(all_acceptance_probs)}")

    # Check if values are varied
    if len(all_redlines) > 1 and len(all_stall_risks) > 1:
        logger.info("\n✅ SUCCESS! Predictor is returning VARIED values from real data!")
    else:
        logger.warning("\n⚠️  STILL RETURNING SAME VALUES - More debugging needed")


if __name__ == '__main__':
    test_predictor_with_multiple_clauses()
