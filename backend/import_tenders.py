"""
Import Tender PDFs
Usage: python import_tenders.py
"""
import os
import sys
import django
import shutil
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from tenders.models import Tender
from django.contrib.auth import get_user_model
from django.core.files import File

User = get_user_model()

def import_tender_pdf(pdf_path):
    """Import a single tender PDF."""

    if not os.path.exists(pdf_path):
        print(f'ERROR: File not found: {pdf_path}')
        return None

    # Get or create user
    user = User.objects.first()
    if not user:
        user = User.objects.create_user(
            username='admin',
            password='admin',
            email='admin@example.com'
        )

    filename = os.path.basename(pdf_path)
    print(f'\nProcessing: {filename}')
    print('-' * 80)

    # Copy to uploads directory
    upload_dir = Path('uploaded_contracts')
    upload_dir.mkdir(exist_ok=True)
    dest_path = upload_dir / filename
    shutil.copy2(pdf_path, dest_path)

    # Extract title from filename
    title = filename.replace('.pdf', '').replace('_', ' ')

    # Check if already exists
    existing = Tender.objects.filter(title=title).first()
    if existing:
        print(f'SKIP: Tender already exists (ID: {existing.id})')
        return existing

    # Create tender record
    with open(dest_path, 'rb') as f:
        tender = Tender.objects.create(
            title=title,
            uploaded_by=user,
            status='DRAFT',
            pdf_file=File(f, name=filename)
        )

    print(f'SUCCESS: Created Tender ID: {tender.id}')
    print(f'         Title: {tender.title}')
    print(f'         Status: {tender.status}')

    return tender


if __name__ == '__main__':
    print('=' * 80)
    print('TENDER PDF IMPORT')
    print('=' * 80)

    # List of PDFs to import
    tender_pdfs = [
        r'C:\Users\Admin\Downloads\1761304916_LTEMinistry.pdf',
        r'C:\Users\Admin\Downloads\tender_(1)918P.pdf',
        r'C:\Users\Admin\Downloads\Tender Civil AMC22.pdf'
    ]

    imported = []

    for pdf_path in tender_pdfs:
        tender = import_tender_pdf(pdf_path)
        if tender:
            imported.append(tender)

    print('\n' + '=' * 80)
    print(f'IMPORT COMPLETE - {len(imported)} tenders imported')
    print('=' * 80)

    print('\nAll Tenders in System:')
    for t in Tender.objects.all().order_by('-created_at')[:10]:
        print(f'  - ID {t.id}: {t.title} [{t.status}]')

    print('\nNext Steps:')
    print('  1. Analyze tenders: http://localhost:5173/tenders')
    print('  2. Click "Open" on each tender to parse and analyze')
    print('  3. Once analyzed, click "Buyer Eval" to add vendor bids')
