"""
Generate Sample Contracts for Testing
Creates 100 sample contract documents with realistic content
"""
import os
import sys
import django
from pathlib import Path
from datetime import datetime, timedelta
import random

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Contract, User
from django.core.files.base import ContentFile
from django.conf import settings

# Sample contract templates
CONTRACT_TEMPLATES = {
    'Software License Agreement': """
SOFTWARE LICENSE AGREEMENT

This Agreement is entered into on {date} between:

Licensor: {company_a}
Licensee: {company_b}

1. LICENSE GRANT
The Licensor grants to the Licensee a non-exclusive, non-transferable license to use the Software.

2. TERM
This Agreement shall commence on {date} and continue for {duration} months.

3. FEES
The Licensee shall pay {amount} for the license.

4. WARRANTIES
The Software is provided "as is" without warranties of any kind.

5. LIMITATION OF LIABILITY
In no event shall Licensor be liable for damages exceeding {amount}.

Signed this {date}

{company_a}                    {company_b}
""",

    'Service Agreement': """
PROFESSIONAL SERVICES AGREEMENT

Agreement Date: {date}

Service Provider: {company_a}
Client: {company_b}

SCOPE OF SERVICES:
The Service Provider agrees to provide {service_type} services to the Client.

TERM: {duration} months from {date}

COMPENSATION: ${amount} payable in monthly installments

TERMINATION: Either party may terminate with 30 days notice.

CONFIDENTIALITY: Both parties agree to maintain confidentiality.

LIABILITY: Liability limited to ${amount}

GOVERNING LAW: {jurisdiction}

{company_a}                    {company_b}
""",

    'Supply Agreement': """
SUPPLY AGREEMENT

Date: {date}

Supplier: {company_a}
Purchaser: {company_b}

PRODUCTS:
The Supplier agrees to supply {product_type} to the Purchaser.

QUANTITY: {quantity} units per month

PRICE: ${amount} per unit

DELIVERY TERMS: FOB {location}

PAYMENT: Net 30 days

TERM: {duration} months

QUALITY STANDARDS: Products must meet industry standards.

WARRANTIES: 12-month warranty on all products.

TERMINATION: 60 days written notice required.

{company_a}                    {company_b}
""",

    'Employment Agreement': """
EMPLOYMENT AGREEMENT

Effective Date: {date}

Employer: {company_a}
Employee: {employee_name}

POSITION: {position}

COMPENSATION: ${amount} annually

BENEFITS: Health insurance, 401(k), {duration} days PTO

WORKING HOURS: 40 hours per week

TERMINATION: At-will employment

NON-COMPETE: {duration} months post-employment

CONFIDENTIALITY: All company information is confidential.

INTELLECTUAL PROPERTY: All work product belongs to Employer.

{company_a}                    {employee_name}
""",

    'Non-Disclosure Agreement': """
NON-DISCLOSURE AGREEMENT

Date: {date}

Disclosing Party: {company_a}
Receiving Party: {company_b}

CONFIDENTIAL INFORMATION:
Any information marked as confidential or proprietary.

OBLIGATIONS:
1. Maintain confidentiality
2. Use only for authorized purposes
3. Return all materials upon request

TERM: {duration} years from {date}

DAMAGES: Breach may result in damages up to ${amount}

NON-SOLICITATION: {duration} months

GOVERNING LAW: {jurisdiction}

{company_a}                    {company_b}
""",
}

COMPANIES = [
    'Acme Corporation', 'TechVision Inc', 'Global Solutions Ltd', 'InnovateCo',
    'DataTech Systems', 'CloudFirst Technologies', 'Enterprise Dynamics',
    'FutureSoft Solutions', 'PrimeLogistics LLC', 'Quantum Industries',
    'Nexus Technologies', 'Stellar Enterprises', 'Apex Manufacturing',
    'Velocity Logistics', 'Catalyst Group', 'Meridian Systems',
    'Zenith Corporation', 'Horizon Tech', 'Vertex Solutions', 'Atlas Global'
]

LOCATIONS = ['New York', 'California', 'Texas', 'Illinois', 'Delaware', 'Florida']
SERVICE_TYPES = ['consulting', 'development', 'support', 'maintenance', 'training']
PRODUCT_TYPES = ['hardware', 'software', 'raw materials', 'equipment', 'supplies']
POSITIONS = ['Software Engineer', 'Project Manager', 'Sales Director', 'Operations Manager']
EMPLOYEE_NAMES = ['John Smith', 'Sarah Johnson', 'Michael Chen', 'Emily Davis', 'David Wilson']


def generate_contract_content(template_name):
    """Generate realistic contract content from template"""
    template = CONTRACT_TEMPLATES[template_name]

    # Generate random data
    start_date = datetime.now() - timedelta(days=random.randint(0, 365))
    amount = random.choice([50000, 100000, 250000, 500000, 1000000, 2500000])
    duration = random.choice([6, 12, 24, 36, 48])
    quantity = random.randint(100, 10000)

    data = {
        'date': start_date.strftime('%B %d, %Y'),
        'company_a': random.choice(COMPANIES),
        'company_b': random.choice([c for c in COMPANIES]),  # Different company
        'amount': f'{amount:,}',
        'duration': duration,
        'location': random.choice(LOCATIONS),
        'jurisdiction': random.choice(LOCATIONS),
        'service_type': random.choice(SERVICE_TYPES),
        'product_type': random.choice(PRODUCT_TYPES),
        'quantity': quantity,
        'position': random.choice(POSITIONS),
        'employee_name': random.choice(EMPLOYEE_NAMES),
    }

    return template.format(**data)


def create_sample_contract(user, template_name, index):
    """Create a single sample contract"""
    try:
        # Generate content
        content = generate_contract_content(template_name)

        # Create filename
        filename = f"{template_name.replace(' ', '_')}_{index}.txt"

        # Determine risk level based on content
        risk_keywords = {
            'HIGH': ['unlimited liability', 'no warranty', 'as is', 'gross negligence'],
            'MEDIUM': ['limited warranty', '30 days notice', 'damages'],
            'LOW': ['standard terms', 'mutual', 'reasonable']
        }

        risk_level = 'MEDIUM'  # Default
        if any(keyword in content.lower() for keyword in risk_keywords['HIGH']):
            risk_level = 'HIGH'
        elif any(keyword in content.lower() for keyword in risk_keywords['LOW']):
            risk_level = 'LOW'

        # Create contract
        contract = Contract.objects.create(
            user=user,
            original_filename=filename,
            filename=filename,
            risk_level=risk_level,
            risk_score=random.uniform(0.3, 0.9),
            full_text=content,
            key_terms=f"{template_name} between parties",
            obligations=f"Standard {template_name.lower()} obligations",
            start_date=datetime.now().date(),
            end_date=(datetime.now() + timedelta(days=random.randint(180, 1095))).date(),
            total_value=random.randint(50000, 5000000),
            status='active'
        )

        # Save file
        file_content = ContentFile(content.encode('utf-8'))
        contract.file.save(filename, file_content, save=True)

        return contract

    except Exception as e:
        print(f"  [ERROR] Failed to create contract: {e}")
        return None


def generate_contracts(count=100):
    """Generate multiple sample contracts"""
    print("\n" + "="*60)
    print(f"GENERATE {count} SAMPLE CONTRACTS")
    print("="*60)

    # Get or create user
    print("\n[1/3] Setting up user...")
    try:
        user = User.objects.filter(is_superuser=False).first()
        if not user:
            user = User.objects.create_user(
                username='demo',
                email='demo@example.com',
                password='demo123',
                subscription_plan='enterprise'
            )
            print("  [OK] Created demo user")
        else:
            print(f"  [OK] Using existing user: {user.username}")
    except Exception as e:
        print(f"  [ERROR] User setup failed: {e}")
        return

    # Generate contracts
    print(f"\n[2/3] Generating {count} contracts...")
    print()

    template_names = list(CONTRACT_TEMPLATES.keys())
    success_count = 0

    for i in range(1, count + 1):
        template_name = random.choice(template_names)
        print(f"  [{i}/{count}] {template_name}...", end=' ')

        contract = create_sample_contract(user, template_name, i)

        if contract:
            print(f"✓ OK ({contract.id[:8]}...)")
            success_count += 1
        else:
            print("✗ FAILED")

    # Summary
    print("\n[3/3] Summary")
    print("="*60)
    print(f"  Total requested:  {count}")
    print(f"  Successfully created: {success_count}")
    print(f"  Failed: {count - success_count}")
    print()

    if success_count > 0:
        print(f"✓ {success_count} sample contracts created!")
        print(f"\n  View them at:")
        print(f"    http://localhost:5173/contracts")
        print(f"\n  Upload to Alfresco:")
        print(f"    python bulk_upload_to_alfresco.py {success_count}")

    print("="*60)


if __name__ == '__main__':
    import sys

    # Get count from command line or use default
    count = 100
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
        except ValueError:
            print(f"Invalid count: {sys.argv[1]}, using default 100")

    try:
        generate_contracts(count)
    except KeyboardInterrupt:
        print("\n\n[WARN] Generation interrupted by user")
    except Exception as e:
        print(f"\n\n[ERROR] Generation failed: {e}")
        import traceback
        traceback.print_exc()
