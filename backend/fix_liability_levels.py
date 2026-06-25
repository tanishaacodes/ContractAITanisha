import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract

contracts = Contract.objects.all()
print(f'Updating liability levels for {contracts.count()} contracts...\n')

for contract in contracts:
    try:
        filename = contract.filename.upper()

        # High risk indicators
        if any(word in filename for word in ['HIGH_RISK', 'CONSTRUCTION']):
            new_level = 'HIGH'
        # Medium risk indicators
        elif any(word in filename for word in ['SOFTWARE', 'DEVELOPMENT', 'MANUFACTURING']):
            new_level = 'MEDIUM'
        # Low risk indicators
        elif any(word in filename for word in ['LEASE', 'DISTRIBUTION']):
            new_level = 'LOW'
        else:
            new_level = 'MEDIUM'  # Default

        old_level = contract.liability_level
        contract.liability_level = new_level
        contract.save()

        print(f'{contract.filename}')
        print(f'  {old_level} -> {new_level}')

    except Exception as e:
        print(f'Error {contract.filename}: {e}')

print('\n=== Updated Liability Levels ===')
for level in ['LOW', 'MEDIUM', 'HIGH']:
    count = Contract.objects.filter(liability_level=level).count()
    print(f'{level}: {count} contracts')
