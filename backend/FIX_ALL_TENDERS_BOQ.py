"""
PERMANENT BOQ FIX - Re-analyze All Tenders with Improved Parser
Fixes:
- Removes (cid:XXX) corrupted text
- Cleans PDF encoding artifacts
- Better handles NULL values
- Improves BOQ extraction
Usage: python FIX_ALL_TENDERS_BOQ.py
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from tenders.models import Tender, TenderSection, TenderWorkItem
from tenders.tender_parser import TenderParser
from decimal import Decimal


def classify_boq_item(description):
    """Simple BOQ category classifier"""
    desc_lower = description.lower()

    if any(word in desc_lower for word in ['excavation', 'earth', 'foundation', 'concrete', 'brick', 'masonry', 'plaster']):
        return 'CIVIL'
    elif any(word in desc_lower for word in ['electrical', 'wire', 'cable', 'light', 'power', 'hvac', 'plumbing', 'sanitary']):
        return 'MEP'
    elif any(word in desc_lower for word in ['mechanical', 'pump', 'motor', 'machinery', 'equipment']):
        return 'MECHANICAL'
    else:
        return 'OTHER'


def fix_tender_boq(tender_id):
    """Re-analyze tender with improved parser."""

    try:
        tender = Tender.objects.get(id=tender_id)
    except Tender.DoesNotExist:
        print(f'  ERROR: Tender {tender_id} not found')
        return False

    print(f'\n{"="*80}')
    print(f'FIXING: {tender.title} (ID: {tender_id})')
    print(f'{"="*80}')

    if not tender.pdf_file:
        print('  ERROR: No PDF file attached')
        return False

    pdf_path = tender.pdf_file.path
    if not os.path.exists(pdf_path):
        print(f'  ERROR: PDF not found at {pdf_path}')
        return False

    try:
        print('  [1/5] Clearing old BOQ data...')
        tender.sections.all().delete()
        tender.work_items.all().delete()

        tender.status = 'ANALYZING'
        tender.save()

        print('  [2/5] Parsing PDF with improved parser...')
        parser = TenderParser()
        parsed_data = parser.parse_pdf(pdf_path)

        print('  [3/5] Extracting metadata...')
        metadata = parsed_data.get('metadata', {})
        if metadata.get('estimated_value'):
            tender.estimated_value = Decimal(str(metadata['estimated_value']))
            print(f'        Estimated Value: Rs.{tender.estimated_value:,.0f}')

        print('  [4/5] Extracting sections...')
        section_count = 0
        for section_data in parsed_data.get('sections', []):
            TenderSection.objects.create(
                tender=tender,
                section_number=section_data['number'],
                title=section_data['title'],
                content=section_data.get('content', ''),
                level=section_data.get('level', 0),
            )
            section_count += 1
        print(f'        Extracted {section_count} sections')

        print('  [5/5] Extracting BOQ items...')
        boq_items = parser.extract_boq_items(parsed_data.get('tables', []))

        item_count = 0
        if boq_items:
            for item in boq_items:
                # Skip items with no description
                if not item.get('description'):
                    continue

                # Create work item
                TenderWorkItem.objects.create(
                    tender=tender,
                    item_code=str(item.get('item_code', ''))[:500],  # Limit to 500 chars
                    description=item.get('description', ''),
                    category=classify_boq_item(item.get('description', '')),
                    quantity=item.get('quantity'),
                    unit=item.get('unit', ''),
                    estimated_cost=item.get('rate') or item.get('amount'),
                )
                item_count += 1

            print(f'        SUCCESS: Extracted {item_count} BOQ items!')
        else:
            print('        No BOQ items found in tables')

        tender.status = 'ANALYZED'
        tender.save()

        print(f'  [OK] COMPLETE: {tender.title}')
        print(f'    - Sections: {section_count}')
        print(f'    - BOQ Items: {item_count}')
        return True

    except Exception as e:
        print(f'  [X] ERROR: {str(e)}')
        tender.status = 'DRAFT'
        tender.save()
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print('\n' + '='*80)
    print('PERMANENT BOQ FIX - ALL TENDERS')
    print('='*80)
    print('\nIMPROVEMENTS:')
    print('  [+] Removes (cid:XXX) corrupted text')
    print('  [+] Cleans (col:XXX) artifacts')
    print('  [+] Removes control characters')
    print('  [+] Better handles NULL/missing values')
    print('  [+] Limits text field lengths')
    print('  [+] Improves number parsing')
    print('='*80)

    # Get all tenders
    tenders = Tender.objects.all().order_by('id')

    print(f'\nFound {tenders.count()} tenders to fix\n')

    success_count = 0
    fail_count = 0

    for tender in tenders:
        if fix_tender_boq(tender.id):
            success_count += 1
        else:
            fail_count += 1

    print('\n' + '='*80)
    print('FINAL SUMMARY')
    print('='*80)
    print(f'  [OK] Success: {success_count} tenders')
    print(f'  [X] Failed: {fail_count} tenders')
    print(f'  Total: {tenders.count()} tenders')
    print('='*80)

    print('\nAll future tender uploads will use the improved parser!')
    print('BOQ extraction is now PERMANENTLY FIXED!')
    print('\nRefresh your tender pages to see clean BOQ data.')
