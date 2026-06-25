import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract

contracts = Contract.objects.all()
print(f'Total contracts: {contracts.count()}')
print('\nLiability levels:')
for level in ['LOW', 'MEDIUM', 'HIGH', None]:
    count = contracts.filter(liability_level=level).count()
    print(f'  {level}: {count}')

print('\nContract details:')
for contract in contracts:
    print(f'  - {contract.filename}: liability_level={contract.liability_level}')
