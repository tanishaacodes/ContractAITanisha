"""
Analyze Imported Tender PDFs
Extracts: estimated value, deadlines, sections, requirements
Usage: python analyze_tenders.py
"""
import os
import sys
import django
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from tenders.models import Tender
from tenders.tender_parser import TenderParser


def analyze_tender(tender_id):
    """Analyze a single tender."""

    try:
        tender = Tender.objects.get(id=tender_id)
    except Tender.DoesNotExist:
        print(f'ERROR: Tender {tender_id} not found')
        return False

    print(f'\nAnalyzing Tender ID {tender_id}: {tender.title}')
    print('-' * 80)

    if not tender.pdf_file:
        print('ERROR: No PDF file attached')
        return False

    # Update status
    tender.status = 'ANALYZING'
    tender.save()

    try:
        # Parse the PDF
        parser = TenderParser()
        pdf_path = tender.pdf_file.path

        if not os.path.exists(pdf_path):
            print(f'ERROR: PDF file not found at {pdf_path}')
            return False

        print('Parsing PDF...')
        result = parser.parse_tender(pdf_path)

        # Update tender with extracted info
        if result:
            if result.get('estimated_value'):
                tender.estimated_value = result['estimated_value']
            if result.get('reference_number'):
                tender.reference_number = result['reference_number']
            if result.get('submission_deadline'):
                tender.submission_deadline = result['submission_deadline']
            if result.get('summary'):
                tender.summary = result['summary']
            if result.get('scope_of_work'):
                tender.scope_of_work = result['scope_of_work']

        tender.status = 'ANALYZED'
        tender.save()

        print(f'SUCCESS: Tender analyzed')
        print(f'  - Reference: {tender.reference_number or "N/A"}')
        print(f'  - Estimated Value: {tender.estimated_value or "N/A"}')
        print(f'  - Status: {tender.status}')

        return True

    except Exception as e:
        print(f'ERROR: {str(e)}')
        tender.status = 'DRAFT'
        tender.save()
        return False


if __name__ == '__main__':
    print('=' * 80)
    print('TENDER ANALYSIS')
    print('=' * 80)

    # Analyze the 3 new tenders
    tender_ids = [39, 40, 41]

    success_count = 0
    for tid in tender_ids:
        if analyze_tender(tid):
            success_count += 1

    print('\n' + '=' * 80)
    print(f'ANALYSIS COMPLETE - {success_count}/{len(tender_ids)} tenders analyzed')
    print('=' * 80)

    print('\nUpdated Tender Status:')
    for t in Tender.objects.filter(id__in=tender_ids):
        est_val = f'Rs.{t.estimated_value:,.0f}' if t.estimated_value else 'N/A'
        print(f'  - ID {t.id}: {t.title}')
        print(f'    Status: {t.status} | Value: {est_val}')
        print(f'    Reference: {t.reference_number or "N/A"}')
        print()

    print('Next Step: Go to http://localhost:5173/tenders')
    print('Click "Buyer Eval" on any analyzed tender to start bid evaluation!')
