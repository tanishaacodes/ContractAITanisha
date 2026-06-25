import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract, RiskAnalysis

contracts = Contract.objects.all()
print(f'Updating liability levels for {contracts.count()} contracts...\n')

for contract in contracts:
    # Check if contract has risk analysis
    try:
        risk_analysis = RiskAnalysis.objects.filter(contract=contract).first()

        if risk_analysis and risk_analysis.risk_score is not None:
            risk_score = risk_analysis.risk_score

            # Classify based on risk score
            if risk_score >= 70:
                new_level = 'HIGH'
            elif risk_score >= 40:
                new_level = 'MEDIUM'
            else:
                new_level = 'LOW'
        else:
            # No risk analysis - use filename heuristic
            filename = contract.filename.upper()

            # High risk indicators
            if any(word in filename for word in ['HIGH_RISK', 'CONSTRUCTION', 'LIABILITY']):
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

        print(f'✓ {contract.filename}')
        print(f'  {old_level} → {new_level}')

    except Exception as e:
        print(f'✗ {contract.filename}: {e}')

print('\n=== Updated Liability Levels ===')
for level in ['LOW', 'MEDIUM', 'HIGH']:
    count = Contract.objects.filter(liability_level=level).count()
    print(f'{level}: {count} contracts')
