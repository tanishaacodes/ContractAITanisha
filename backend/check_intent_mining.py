import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract, Intent, ClauseIntent, IntentObligation, IntentRight

# Get the latest contract
contract = Contract.objects.order_by('-uploaded_at').first()
if not contract:
    print('No contracts found')
    exit(1)

print(f'Contract: {contract.original_filename}')
print(f'Contract ID: {contract.id}')

# Check intents
clause_intents = ClauseIntent.objects.filter(clause__contract=contract)
print(f'\nClause Intents found: {clause_intents.count()}')

total_obligations = 0
total_rights = 0

for ci in clause_intents:
    print(f'\n  Intent: {ci.intent.name}')
    print(f'  Confidence: {ci.confidence}')

    # Check obligations
    obligations = IntentObligation.objects.filter(intent=ci.intent, clause__contract=contract)
    total_obligations += obligations.count()
    print(f'  Obligations: {obligations.count()}')
    for ob in obligations[:2]:
        print(f'    - {ob.action[:50]}...')

    # Check rights
    rights = IntentRight.objects.filter(intent=ci.intent, clause__contract=contract)
    total_rights += rights.count()
    print(f'  Rights: {rights.count()}')
    for r in rights[:2]:
        print(f'    - {r.entitlement[:50]}...')

print(f'\n\nTOTAL OBLIGATIONS: {total_obligations}')
print(f'TOTAL RIGHTS: {total_rights}')

# Check if there's any data at all
all_obligations = IntentObligation.objects.all()
all_rights = IntentRight.objects.all()
print(f'\nAll obligations in DB: {all_obligations.count()}')
print(f'All rights in DB: {all_rights.count()}')
