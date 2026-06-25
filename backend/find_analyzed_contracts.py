"""
Find the 5 most analyzed contracts (with intelligence data)
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract, ContractIntelligence, VectorEmbedding


def find_analyzed_contracts():
    """Find contracts with most analysis data"""
    print("\n" + "="*60)
    print("FIND MOST ANALYZED CONTRACTS")
    print("="*60)

    all_contracts = Contract.objects.all().order_by('uploaded_at')
    print(f"\n[INFO] Total contracts: {all_contracts.count()}")

    # Check which contracts have intelligence data
    analyzed_contracts = []

    for contract in all_contracts:
        analysis_score = 0
        details = {}

        # Check full text
        if contract.full_text:
            analysis_score += 10
            details['has_text'] = True

        # Check contract type
        if contract.contract_type and contract.contract_type != 'Contract Agreement':
            analysis_score += 5
            details['contract_type'] = contract.contract_type

        # Check intelligence
        try:
            intelligence = ContractIntelligence.objects.get(contract=contract)
            analysis_score += 20
            details['has_intelligence'] = True
            details['parties'] = len(intelligence.parties) if intelligence.parties else 0
        except ContractIntelligence.DoesNotExist:
            details['has_intelligence'] = False

        # Check embeddings
        embeddings_count = VectorEmbedding.objects.filter(contract=contract).count()
        if embeddings_count > 0:
            analysis_score += embeddings_count
            details['embeddings'] = embeddings_count

        # Check other fields
        if contract.counterparty:
            analysis_score += 3
            details['has_counterparty'] = True

        if contract.contract_value:
            analysis_score += 2
            details['has_value'] = True

        if contract.liability_level:
            analysis_score += 3
            details['liability_level'] = contract.liability_level

        if analysis_score > 0:
            analyzed_contracts.append({
                'contract': contract,
                'score': analysis_score,
                'details': details
            })

    # Sort by score
    analyzed_contracts.sort(key=lambda x: x['score'], reverse=True)

    print(f"\n[INFO] Contracts with analysis data: {len(analyzed_contracts)}")
    print("\nTop 10 most analyzed contracts:")
    print("="*60)

    for idx, item in enumerate(analyzed_contracts[:10], 1):
        contract = item['contract']
        score = item['score']
        details = item['details']

        print(f"\n{idx}. {contract.original_filename or contract.filename}")
        print(f"   ID: {str(contract.id)[:8]}...")
        print(f"   Uploaded: {contract.uploaded_at}")
        print(f"   Analysis Score: {score}")
        print(f"   Details:")
        for key, value in details.items():
            print(f"     - {key}: {value}")

    print("\n" + "="*60)

    # Show recommendation
    if len(analyzed_contracts) >= 5:
        print("\n[RECOMMENDATION] Keep these 5 contracts:")
        for idx, item in enumerate(analyzed_contracts[:5], 1):
            contract = item['contract']
            print(f"  {idx}. {contract.original_filename or contract.filename}")
            print(f"     ID: {str(contract.id)[:8]}...")

        print("\n[ACTION] Do you want to keep only these 5? (y/n)")
    else:
        print(f"\n[WARNING] Found only {len(analyzed_contracts)} analyzed contracts")

    print("="*60)

    return analyzed_contracts


if __name__ == '__main__':
    try:
        find_analyzed_contracts()
    except Exception as e:
        print(f"\n\n[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()
