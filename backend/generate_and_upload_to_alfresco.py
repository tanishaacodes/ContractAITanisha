"""
Generate 100 Sample Contracts and Upload Directly to Alfresco
Bypasses Django database - uploads straight to Alfresco CMS
"""
import requests
import io
from datetime import datetime, timedelta
import random

# Alfresco Configuration
ALFRESCO_URL = 'http://localhost:8080/alfresco'
ALFRESCO_USER = 'admin'
ALFRESCO_PASSWORD = 'admin'

# Sample contract templates
CONTRACT_TEMPLATES = {
    'Software_License_Agreement': """
SOFTWARE LICENSE AGREEMENT

This Agreement is entered into on {date} between:

Licensor: {company_a}
Licensee: {company_b}

1. LICENSE GRANT
The Licensor grants to the Licensee a non-exclusive, non-transferable license to use the Software.

2. TERM
This Agreement shall commence on {date} and continue for {duration} months.

3. FEES
The Licensee shall pay ${amount:,} for the license.

4. WARRANTIES
The Software is provided "as is" without warranties of any kind.

5. LIMITATION OF LIABILITY
In no event shall Licensor be liable for damages exceeding ${amount:,}.

6. TERMINATION
Either party may terminate this agreement with 30 days written notice.

7. GOVERNING LAW
This Agreement shall be governed by the laws of {jurisdiction}.

Signed this {date}

_____________________          _____________________
{company_a}                    {company_b}
Authorized Signatory           Authorized Signatory
""",

    'Service_Agreement': """
PROFESSIONAL SERVICES AGREEMENT

Agreement Date: {date}

Service Provider: {company_a}
Client: {company_b}

1. SCOPE OF SERVICES
The Service Provider agrees to provide {service_type} services to the Client for a period of {duration} months.

2. DELIVERABLES
- Monthly progress reports
- {service_type} implementation
- Documentation and training

3. COMPENSATION
Total Contract Value: ${amount:,}
Payment Schedule: Monthly installments of ${monthly:,}

4. TERM AND TERMINATION
Term: {duration} months from {date}
Termination: Either party may terminate with 30 days notice.

5. CONFIDENTIALITY
Both parties agree to maintain strict confidentiality of all proprietary information.

6. LIABILITY
Total liability is limited to ${amount:,}.

7. GOVERNING LAW
Jurisdiction: {jurisdiction}

_____________________          _____________________
{company_a}                    {company_b}
""",

    'Supply_Agreement': """
SUPPLY AGREEMENT

Date: {date}

Supplier: {company_a}
Purchaser: {company_b}

1. PRODUCTS
The Supplier agrees to supply {product_type} to the Purchaser.

2. QUANTITY AND PRICING
Quantity: {quantity} units per month
Unit Price: ${unit_price}
Total Monthly Value: ${monthly:,}

3. DELIVERY TERMS
- Delivery Location: {location}
- Shipping Terms: FOB {location}
- Delivery Schedule: First Monday of each month

4. PAYMENT TERMS
Payment: Net 30 days from invoice date
Total Contract Value: ${amount:,}

5. QUALITY STANDARDS
All products must meet ISO 9001 standards and pass quality inspection.

6. WARRANTIES
12-month warranty on all products against defects in materials and workmanship.

7. TERM
Contract Period: {duration} months from {date}
Renewal: Automatic renewal unless 60 days written notice provided.

8. TERMINATION
Either party may terminate with 60 days written notice.

_____________________          _____________________
{company_a}                    {company_b}
""",

    'Employment_Agreement': """
EMPLOYMENT AGREEMENT

Effective Date: {date}

Employer: {company_a}
Employee: {employee_name}

1. POSITION AND DUTIES
Position: {position}
Reports To: Chief Executive Officer
Location: {location}

2. COMPENSATION
Base Salary: ${amount:,} annually
Bonus: Up to 20% of base salary based on performance
Benefits: Health insurance, 401(k) matching, {duration} days PTO

3. WORKING HOURS
Standard: 40 hours per week, Monday through Friday

4. EMPLOYMENT AT-WILL
This is an at-will employment relationship. Either party may terminate at any time.

5. NON-COMPETE CLAUSE
Employee agrees not to engage in competing business for {duration} months post-employment within {location}.

6. CONFIDENTIALITY
All company information, trade secrets, and proprietary data must remain confidential.

7. INTELLECTUAL PROPERTY
All inventions, discoveries, and creative work performed during employment belong to the Employer.

8. TERMINATION
Termination requires 2 weeks notice from either party.

_____________________          _____________________
{company_a}                    {employee_name}
Employer Signature             Employee Signature
""",

    'Non_Disclosure_Agreement': """
NON-DISCLOSURE AGREEMENT (NDA)

Date: {date}

Disclosing Party: {company_a}
Receiving Party: {company_b}

1. DEFINITION OF CONFIDENTIAL INFORMATION
Any information marked as "Confidential", "Proprietary", or that should reasonably be considered confidential.

2. OBLIGATIONS OF RECEIVING PARTY
The Receiving Party agrees to:
- Maintain strict confidentiality
- Use information only for authorized business purposes
- Not disclose to third parties without written consent
- Return all materials upon request

3. EXCLUSIONS
This agreement does not apply to information that:
- Is publicly available
- Was known prior to disclosure
- Is independently developed
- Is required to be disclosed by law

4. TERM
Duration: {duration} years from {date}

5. DAMAGES FOR BREACH
Breach may result in:
- Injunctive relief
- Monetary damages up to ${amount:,}
- Legal fees and costs

6. NON-SOLICITATION
Neither party shall solicit the other's employees for {duration} months.

7. GOVERNING LAW
This Agreement is governed by the laws of {jurisdiction}.

_____________________          _____________________
{company_a}                    {company_b}
""",

    'Master_Services_Agreement': """
MASTER SERVICES AGREEMENT

Effective Date: {date}

Company A: {company_a}
Company B: {company_b}

1. SERVICES
{company_a} will provide {service_type} services as detailed in individual Statements of Work.

2. TERM
Initial Term: {duration} months
Renewal: Automatic annual renewal

3. FEES AND PAYMENT
Estimated Annual Value: ${amount:,}
Payment Terms: Net 30 days
Late Payment: 1.5% monthly interest

4. INTELLECTUAL PROPERTY
- Pre-existing IP remains with original owner
- New IP created under this agreement belongs to {company_b}

5. WARRANTIES
{company_a} warrants that services will be performed in a professional manner consistent with industry standards.

6. LIMITATION OF LIABILITY
Total liability capped at ${amount:,} or fees paid in preceding 12 months, whichever is less.

7. INDEMNIFICATION
Each party indemnifies the other against third-party claims arising from their breach.

8. CONFIDENTIALITY
Both parties agree to maintain confidentiality of all proprietary information.

9. TERMINATION
- For convenience: 90 days written notice
- For cause: Immediate upon material breach

10. GOVERNING LAW
Jurisdiction: {jurisdiction}

_____________________          _____________________
{company_a}                    {company_b}
"""
}

COMPANIES = [
    'Acme Corporation', 'TechVision Inc', 'Global Solutions Ltd', 'InnovateCo',
    'DataTech Systems', 'CloudFirst Technologies', 'Enterprise Dynamics',
    'FutureSoft Solutions', 'PrimeLogistics LLC', 'Quantum Industries',
    'Nexus Technologies', 'Stellar Enterprises', 'Apex Manufacturing',
    'Velocity Logistics', 'Catalyst Group', 'Meridian Systems',
    'Zenith Corporation', 'Horizon Tech', 'Vertex Solutions', 'Atlas Global',
    'Summit Partners', 'Pacific Technologies', 'BlueSky Systems', 'RedLine Industries'
]

LOCATIONS = ['New York, NY', 'San Francisco, CA', 'Austin, TX', 'Chicago, IL', 'Boston, MA', 'Seattle, WA']
JURISDICTIONS = ['New York', 'California', 'Texas', 'Delaware', 'Illinois', 'Washington']
SERVICE_TYPES = ['consulting', 'software development', 'IT support', 'maintenance', 'training', 'implementation']
PRODUCT_TYPES = ['computer hardware', 'software licenses', 'raw materials', 'office equipment', 'industrial supplies']
POSITIONS = ['Software Engineer', 'Project Manager', 'Sales Director', 'Operations Manager', 'Data Analyst']
EMPLOYEE_NAMES = ['John Smith', 'Sarah Johnson', 'Michael Chen', 'Emily Davis', 'David Wilson', 'Lisa Anderson']


def authenticate_alfresco():
    """Authenticate with Alfresco"""
    print("\n[1/4] Connecting to Alfresco...")
    session = requests.Session()
    session.auth = (ALFRESCO_USER, ALFRESCO_PASSWORD)

    try:
        test_url = f"{ALFRESCO_URL}/api/-default-/public/alfresco/versions/1/nodes/-root-"
        response = session.get(test_url, timeout=10)

        if response.status_code == 200:
            print(f"  [OK] Connected to Alfresco at {ALFRESCO_URL}")
            return session
        else:
            print(f"  [ERROR] Alfresco returned status {response.status_code}")
            return None
    except Exception as e:
        print(f"  [ERROR] Cannot connect to Alfresco: {e}")
        print("\n  Start Alfresco with:")
        print("    docker run -p 8080:8080 alfresco/alfresco-content-repository-community")
        return None


def create_contracts_folder(session):
    """Create Contracts folder in Alfresco"""
    print("\n[2/4] Creating Contracts folder...")

    try:
        create_url = f"{ALFRESCO_URL}/api/-default-/public/alfresco/versions/1/nodes/-root-/children"

        folder_data = {
            "name": "Contracts",
            "nodeType": "cm:folder",
            "properties": {
                "cm:title": "Contract Documents",
                "cm:description": "Generated sample contracts for testing"
            }
        }

        response = session.post(
            create_url,
            json=folder_data,
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code in [201, 409]:
            if response.status_code == 201:
                folder_id = response.json()['entry']['id']
                print(f"  [OK] Created Contracts folder")
            else:
                # Get existing folder ID
                list_url = f"{ALFRESCO_URL}/api/-default-/public/alfresco/versions/1/nodes/-root-/children"
                list_response = session.get(list_url)

                if list_response.status_code == 200:
                    entries = list_response.json().get('list', {}).get('entries', [])
                    contracts_folder = next(
                        (e for e in entries if e['entry']['name'] == 'Contracts'),
                        None
                    )
                    if contracts_folder:
                        folder_id = contracts_folder['entry']['id']
                        print(f"  [OK] Using existing Contracts folder")
                    else:
                        folder_id = '-root-'
                else:
                    folder_id = '-root-'

            return folder_id
        else:
            print(f"  [WARN] Using root folder")
            return '-root-'

    except Exception as e:
        print(f"  [WARN] Error: {e}, using root folder")
        return '-root-'


def generate_contract_content(template_name):
    """Generate contract content from template"""
    template = CONTRACT_TEMPLATES[template_name]

    start_date = datetime.now() - timedelta(days=random.randint(0, 365))
    amount = random.choice([50000, 100000, 250000, 500000, 750000, 1000000, 2500000, 5000000])
    duration = random.choice([6, 12, 18, 24, 36, 48])
    quantity = random.randint(100, 10000)
    unit_price = random.randint(10, 500)
    monthly = amount / duration if duration > 0 else amount

    company_a = random.choice(COMPANIES)
    company_b = random.choice([c for c in COMPANIES if c != company_a])

    data = {
        'date': start_date.strftime('%B %d, %Y'),
        'company_a': company_a,
        'company_b': company_b,
        'amount': amount,
        'monthly': int(monthly),
        'duration': duration,
        'location': random.choice(LOCATIONS),
        'jurisdiction': random.choice(JURISDICTIONS),
        'service_type': random.choice(SERVICE_TYPES),
        'product_type': random.choice(PRODUCT_TYPES),
        'quantity': quantity,
        'unit_price': unit_price,
        'position': random.choice(POSITIONS),
        'employee_name': random.choice(EMPLOYEE_NAMES),
    }

    return template.format(**data)


def upload_contract_to_alfresco(session, folder_id, filename, content):
    """Upload a single contract to Alfresco"""
    try:
        upload_url = f"{ALFRESCO_URL}/api/-default-/public/alfresco/versions/1/nodes/{folder_id}/children"

        # Prepare file
        files = {
            'filedata': (filename, io.BytesIO(content.encode('utf-8')), 'text/plain')
        }

        response = session.post(upload_url, files=files, timeout=30)

        if response.status_code == 201:
            node_id = response.json()['entry']['id']
            return {'status': 'success', 'node_id': node_id}
        else:
            return {'status': 'error', 'error': f'HTTP {response.status_code}'}

    except Exception as e:
        return {'status': 'error', 'error': str(e)}


def generate_and_upload(count=100):
    """Generate contracts and upload directly to Alfresco"""
    print("\n" + "="*60)
    print(f"GENERATE {count} CONTRACTS -> UPLOAD TO ALFRESCO")
    print("="*60)

    # Authenticate
    session = authenticate_alfresco()
    if not session:
        return

    # Create folder
    folder_id = create_contracts_folder(session)

    # Generate and upload
    print(f"\n[3/4] Generating and uploading {count} contracts...")
    print()

    template_names = list(CONTRACT_TEMPLATES.keys())
    success_count = 0
    error_count = 0

    for i in range(1, count + 1):
        template_name = random.choice(template_names)
        filename = f"{template_name}_{i:03d}.txt"

        print(f"  [{i}/{count}] {template_name.replace('_', ' ')}...", end=' ')

        # Generate content
        content = generate_contract_content(template_name)

        # Upload to Alfresco
        result = upload_contract_to_alfresco(session, folder_id, filename, content)

        if result['status'] == 'success':
            print(f"[OK] OK ({result['node_id'][:8]}...)")
            success_count += 1
        else:
            print(f"[FAIL] FAILED: {result['error']}")
            error_count += 1

    # Summary
    print("\n[4/4] Summary")
    print("="*60)
    print(f"  Total requested:  {count}")
    print(f"  Successfully uploaded: {success_count}")
    print(f"  Failed: {error_count}")
    print()

    if success_count > 0:
        print(f"[OK] {success_count} contracts uploaded to Alfresco!")
        print(f"\n  View in Alfresco:")
        print(f"    {ALFRESCO_URL}/share/page/repository#filter=path|/Contracts")
        print(f"\n  Sync to your app:")
        print(f"    http://localhost:5173/alfresco-sync")

    print("="*60)


if __name__ == '__main__':
    import sys

    count = 100
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
        except ValueError:
            print(f"Invalid count: {sys.argv[1]}, using default 100")

    try:
        generate_and_upload(count)
    except KeyboardInterrupt:
        print("\n\n[WARN] Upload interrupted")
    except Exception as e:
        print(f"\n\n[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()
