import os
import django
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract

# Contract data
contract_data = {
    'High_Risk_Construction': {
        'contract_value': '₹85,00,000',
        'party_a': 'BuildTech Constructions Ltd',
        'party_b': 'Metro Infrastructure Corp',
        'start_date': date(2024, 1, 15),
        'end_date': date(2026, 1, 14),
        'jurisdiction': 'Mumbai, India',
        'payment_terms': 'Milestone-based, 30% advance',
        'contract_type': 'Construction Agreement'
    },
    'SOFTWARE_DEVELOPMENT': {
        'contract_value': '$15,000,000',
        'party_a': 'TechSolutions Inc',
        'party_b': 'Global Enterprises Ltd',
        'start_date': date(2024, 3, 1),
        'end_date': date(2027, 2, 28),
        'jurisdiction': 'Delaware, USA',
        'payment_terms': 'Monthly milestone payments',
        'contract_type': 'Software Development'
    },
    'MANUFACTURING': {
        'contract_value': '₹85,000,000',
        'party_a': 'AutoParts Manufacturing Co',
        'party_b': 'Premium Motors Ltd',
        'start_date': date(2023, 6, 1),
        'end_date': date(2026, 5, 31),
        'jurisdiction': 'Pune, India',
        'payment_terms': 'NET 60 days',
        'contract_type': 'Manufacturing & Supply'
    },
    'EXCLUSIVE_DISTRIBUTION': {
        'contract_value': '₹7,74,50,00,000',
        'party_a': 'Nordic Wellness Solutions',
        'party_b': 'HealthFirst Distributors',
        'start_date': date(2024, 1, 1),
        'end_date': date(2029, 12, 31),
        'jurisdiction': 'Dubai, UAE',
        'payment_terms': 'NET 45 days',
        'contract_type': 'Exclusive Distribution'
    },
    'COMMERCIAL_LEASE': {
        'contract_value': '₹7,50,00,000',
        'party_a': 'Prime Properties LLC',
        'party_b': 'Retail Ventures Pvt Ltd',
        'start_date': date(2024, 4, 1),
        'end_date': date(2034, 3, 31),
        'jurisdiction': 'Bangalore, India',
        'payment_terms': 'Monthly rent due on 1st',
        'contract_type': 'Commercial Lease'
    }
}

print("Populating contract data...\n")

for keyword, data in contract_data.items():
    try:
        contract = Contract.objects.filter(filename__icontains=keyword).first()
        if contract:
            contract.contract_value = data['contract_value']
            contract.party_a = data['party_a']
            contract.party_b = data['party_b']
            contract.party_name = data['party_b']  # Set party_name for backward compatibility
            contract.start_date = data['start_date']
            contract.end_date = data['end_date']
            contract.jurisdiction = data['jurisdiction']
            contract.payment_terms = data['payment_terms']
            contract.contract_type = data['contract_type']

            # Calculate duration in days
            duration_days = (data['end_date'] - data['start_date']).days
            contract.contract_duration = f"{duration_days // 365} years"

            contract.save()

            print(f"OK: {contract.filename}")
            print(f"  Value: {data['contract_value']}")
            print(f"  Parties: {data['party_a']} <-> {data['party_b']}")
            print(f"  Duration: {contract.contract_duration}")
            print()
    except Exception as e:
        print(f"ERROR: {keyword}: {e}\n")

print("=== Complete ===")
print("Refresh the dashboard to see updated data!")
