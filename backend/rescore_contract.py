"""
Re-score Contract Clauses
=========================
Fixes contracts that were uploaded without risk scores.

Usage:
    python rescore_contract.py <contract_id_or_filename>
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract, Clause
from api.services.clause_graph import ClauseGraphBuilder
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def rescore_contract(contract_identifier):
    """Re-score all clauses for a contract"""

    # Find contract
    try:
        if len(contract_identifier) == 36 or '-' in contract_identifier:
            # Looks like UUID
            contract = Contract.objects.get(id=contract_identifier)
        else:
            # Search by filename
            contract = Contract.objects.filter(filename__icontains=contract_identifier).first()

        if not contract:
            print(f"[ERROR] Contract not found: {contract_identifier}")
            return False

    except Exception as e:
        print(f"[ERROR] Error finding contract: {e}")
        return False

    print(f"\n[Contract] Contract: {contract.filename}")
    print(f"   ID: {contract.id}")
    print(f"   Uploaded: {contract.created_at}")

    # Get clauses
    clauses = list(Clause.objects.filter(contract=contract, found=True))
    print(f"   Clauses: {len(clauses)}")

    if not clauses:
        print("[ERROR] No clauses found")
        return False

    # Check current state
    scored_count = sum(1 for c in clauses if c.risk_score is not None)
    print(f"   Currently scored: {scored_count}/{len(clauses)}")

    # Build graph to infer risk scores
    print(f"\n[INFO] Building interaction graph...")
    graph_builder = ClauseGraphBuilder()

    updated_count = 0
    for clause in clauses:
        old_risk = clause.risk_score

        # Infer risk score from clause text and type
        clause_text = (
            clause.extracted_text or
            clause.context_sentences or
            clause.text_spans or
            ""
        )
        clause_type = clause.clause_type or clause.clause_name or "general"

        # Use the graph builder's risk inference
        risk_score = graph_builder._infer_risk_score(clause_type, clause_text)

        # Also set clause_type if missing
        if not clause.clause_type:
            clause.clause_type = graph_builder._normalize_clause_type(clause_type)

        # Update if changed
        if clause.risk_score != risk_score or not clause.clause_type:
            clause.risk_score = risk_score
            clause.save()
            updated_count += 1

            status = "[OK]" if old_risk is None else "[UPDATE]"
            print(f"   {status} {clause.clause_name}: {old_risk} -> {risk_score:.3f} ({clause.clause_type})")

    print(f"\n[OK] Updated {updated_count} clauses")
    print(f"   Now scored: {len([c for c in clauses if c.risk_score is not None])}/{len(clauses)}")

    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\n[ERROR] Usage: python rescore_contract.py <contract_id_or_filename>")
        print("\nExamples:")
        print("  python rescore_contract.py 1770035642471")
        print("  python rescore_contract.py High_Risk_Construction")
        print("  python rescore_contract.py a681e832-c1ef-4a34-a59f-6313b6e9a227")
        sys.exit(1)

    contract_id = sys.argv[1]
    success = rescore_contract(contract_id)

    sys.exit(0 if success else 1)
