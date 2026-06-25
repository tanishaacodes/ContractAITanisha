#!/usr/bin/env python
"""
Populate Contract Concept Profiles
===================================
Extracts concept strengths from all uploaded contracts and stores in Neo4j.

This script backfills existing contracts with concept profiles by:
1. Fetching all contracts from MySQL
2. Extracting concept scores from each contract's clauses
3. Storing concept profiles in Neo4j

Usage:
    python populate_contract_concepts.py

Optional Arguments:
    --limit N         Process only N contracts (for testing)
    --contract-id ID  Process only specific contract
    --dry-run         Show what would be done without writing to Neo4j
"""

import os
import sys
import django
import argparse

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract, Clause
from api.services.concept_correlation_service import ConceptCorrelationService

def main():
    parser = argparse.ArgumentParser(description='Populate contract concept profiles in Neo4j')
    parser.add_argument('--limit', type=int, help='Process only N contracts')
    parser.add_argument('--contract-id', type=str, help='Process only specific contract ID')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without writing')
    args = parser.parse_args()

    print("=" * 70)
    print("  Contract Concept Profile Population")
    print("  Backfilling Existing Contracts")
    print("=" * 70)

    # Initialize service
    service = ConceptCorrelationService()

    if not service.neo4j_available:
        print("\n[ERROR] Neo4j is not available!")
        print("\nPlease ensure:")
        print("  1. Neo4j is running")
        print("  2. populate_concept_graph.py has been run to create schema")
        print("\nRun: python populate_concept_graph.py")
        sys.exit(1)

    print(f"\n✓ Connected to Neo4j")

    # Query contracts
    if args.contract_id:
        try:
            contracts = [Contract.objects.get(id=args.contract_id)]
            print(f"\nProcessing single contract: {args.contract_id}")
        except Contract.DoesNotExist:
            print(f"\n[ERROR] Contract {args.contract_id} not found")
            sys.exit(1)
    else:
        contracts = Contract.objects.all().order_by('-uploaded_at')
        if args.limit:
            contracts = contracts[:args.limit]
            print(f"\nProcessing {args.limit} most recent contracts (limited)")
        else:
            print(f"\nProcessing all {contracts.count()} contracts")

    if args.dry_run:
        print("\n[DRY RUN MODE] - No data will be written to Neo4j")

    # Process contracts
    processed = 0
    skipped = 0
    errors = 0

    print("\n" + "-" * 70)

    for i, contract in enumerate(contracts, 1):
        try:
            print(f"\n[{i}/{len(contracts)}] {contract.original_filename}")
            print(f"  Contract ID: {contract.id}")
            print(f"  Type: {contract.contract_type or 'Unknown'}")

            # Count clauses
            clause_count = Clause.objects.filter(contract=contract).count()
            if clause_count == 0:
                print(f"  [SKIP] No clauses found")
                skipped += 1
                continue

            print(f"  Clauses: {clause_count}")

            # Extract concept strengths
            concept_strengths = service.extract_concept_scores_from_contract(str(contract.id))

            # Show top concepts
            top_concepts = sorted(concept_strengths.items(), key=lambda x: x[1], reverse=True)[:3]
            print(f"  Top Concepts: {', '.join([f'{c}={s:.2f}' for c, s in top_concepts])}")

            # Store in Neo4j (unless dry run)
            if not args.dry_run:
                success = service.schema.create_contract_concept_profile(
                    contract_id=str(contract.id),
                    contract_type=contract.contract_type or "MSA",
                    concept_strengths=concept_strengths
                )

                if success:
                    print(f"  [OK] Concept profile created in Neo4j")
                    processed += 1
                else:
                    print(f"  [WARN] Failed to store in Neo4j")
                    errors += 1
            else:
                print(f"  [DRY RUN] Would create concept profile")
                processed += 1

        except Exception as e:
            print(f"  [ERROR] {e}")
            errors += 1

    # Summary
    print("\n" + "=" * 70)
    print("  Summary")
    print("=" * 70)
    print(f"Total contracts: {len(contracts)}")
    print(f"Successfully processed: {processed}")
    print(f"Skipped (no clauses): {skipped}")
    print(f"Errors: {errors}")

    if args.dry_run:
        print("\n[DRY RUN COMPLETE] - No data was written to Neo4j")
        print("Remove --dry-run flag to actually populate data")
    else:
        print("\n✓ Contract concept profiles populated in Neo4j!")

    print("\nNext steps:")
    print("  1. Verify in Neo4j Browser:")
    print("     MATCH (con:Contract)-[r:EXHIBITS_CONCEPT]->(c:Concept)")
    print("     RETURN con.id, c.name, r.strength ORDER BY r.strength DESC")
    print("\n  2. Test API endpoint:")
    print(f"     GET /api/concept-graph/contract/{contracts[0].id}/")
    print("\n  3. Compare two contracts:")
    print("     POST /api/concept-graph/compare/")
    print(f"     Body: {{'contract_id_1': '...', 'contract_id_2': '...'}}")

    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
