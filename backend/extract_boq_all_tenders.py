"""
Extract BOQ from All Tenders
Analyzes tender PDFs and extracts Bill of Quantities
Usage: python extract_boq_all_tenders.py
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from tenders.models import Tender
from django.db import connection


def analyze_tender_for_boq(tender_id):
    """Trigger BOQ analysis for a tender."""

    try:
        tender = Tender.objects.get(id=tender_id)
    except Tender.DoesNotExist:
        print(f'  ERROR: Tender {tender_id} not found')
        return False

    print(f'\n  Analyzing: {tender.title} (ID: {tender_id})')

    if not tender.pdf_file:
        print('  ERROR: No PDF file attached')
        return False

    pdf_path = tender.pdf_file.path
    if not os.path.exists(pdf_path):
        print(f'  ERROR: PDF not found at {pdf_path}')
        return False

    # For now, let's just check if we can trigger re-analysis
    # The actual BOQ extraction requires the frontend to call the re-analyze endpoint
    print(f'  PDF exists: {os.path.basename(pdf_path)}')
    print('  Status: Ready for analysis')
    print('  Next: Use UI "Re-analyze Document" button or API call')

    return True


if __name__ == '__main__':
    print('=' * 80)
    print('BOQ EXTRACTION - BULK ANALYSIS')
    print('=' * 80)

    # Get all tenders
    tenders = Tender.objects.all().order_by('-created_at')[:10]

    if not tenders:
        print('\nNo tenders found!')
        sys.exit(1)

    print(f'\nFound {len(tenders)} tenders:')
    print('-' * 80)

    for tender in tenders:
        analyze_tender_for_boq(tender.id)

    print('\n' + '=' * 80)
    print('ANALYSIS SUMMARY')
    print('=' * 80)
    print('\nTo extract BOQ items, you need to:')
    print('1. Go to each tender in the UI: http://localhost:5173/tenders')
    print('2. Click "Open" button')
    print('3. Click "Re-analyze Document" (orange button)')
    print('\nOR use the API endpoint:')
    print('POST http://localhost:8002/api/tenders/tenders/{tender_id}/reanalyze/')
    print('\nThis will extract:')
    print('  - BOQ line items')
    print('  - Quantities and units')
    print('  - Estimated costs')
    print('  - Categories (Civil, MEP, etc.)')
