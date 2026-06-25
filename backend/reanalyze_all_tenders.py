"""
Re-analyze All Tenders to Extract BOQ
Triggers BOQ extraction from tender PDFs
Usage: python reanalyze_all_tenders.py
"""
import os
import sys
import requests
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from tenders.models import Tender
from django.contrib.auth import get_user_model

User = get_user_model()


def get_auth_token():
    """Get or create authentication token."""
    # For development, we'll use a simple approach
    # In production, you'd use proper authentication
    return None  # We'll call the view directly instead


def reanalyze_tender_direct(tender_id):
    """Directly trigger tender reanalysis."""
    from tenders.views import TenderViewSet
    from rest_framework.test import APIRequestFactory
    from rest_framework.request import Request

    try:
        tender = Tender.objects.get(id=tender_id)
    except Tender.DoesNotExist:
        print(f'  ERROR: Tender {tender_id} not found')
        return False

    print(f'\n  Analyzing: {tender.title} (ID: {tender_id})')
    print(f'  Status: {tender.status}')

    if not tender.pdf_file:
        print('  ERROR: No PDF file')
        return False

    try:
        # Create a mock request
        factory = APIRequestFactory()
        request = factory.post(f'/api/tenders/tenders/{tender_id}/reanalyze/')

        # Get the user
        user = User.objects.first()
        if user:
            request.user = user

        # Call the viewset directly
        viewset = TenderViewSet()
        viewset.kwargs = {'pk': tender_id}

        # Import the reanalyze method logic inline
        from tenders.tender_parser import TenderParser
        from tenders.boq_optimizer import BOQClassifier
        from tenders.models import TenderSection
        from decimal import Decimal

        pdf_path = tender.pdf_file.path

        print('  Clearing old data...')
        tender.sections.all().delete()
        tender.work_items.all().delete()

        tender.status = 'ANALYZING'
        tender.save()

        print('  Parsing PDF...')
        parser = TenderParser()
        parsed_data = parser.parse_pdf(pdf_path)

        print('  Extracting metadata...')
        metadata = parsed_data.get('metadata', {})
        if metadata.get('estimated_value'):
            tender.estimated_value = Decimal(str(metadata['estimated_value']))
            print(f'  Estimated Value: Rs.{tender.estimated_value:,.0f}')

        print('  Extracting sections...')
        for section_data in parsed_data.get('sections', []):
            TenderSection.objects.create(
                tender=tender,
                section_number=section_data['number'],
                title=section_data['title'],
                content=section_data.get('content', ''),
                level=section_data.get('level', 0),
            )

        print('  Extracting BOQ items...')
        boq_classifier = BOQClassifier()
        boq_items = parser.extract_boq_items(parsed_data.get('tables', []))

        if boq_items:
            print(f'  Found {len(boq_items)} BOQ items!')
            from tenders.models import TenderWorkItem
            for item in boq_items[:100]:  # Limit to first 100
                TenderWorkItem.objects.create(
                    tender=tender,
                    item_code=str(item.get('item_code', ''))[:500],
                    description=item.get('description', ''),
                    category=boq_classifier.classify_item(item.get('description', '')),
                    quantity=item.get('quantity'),
                    unit=item.get('unit', ''),
                    estimated_cost=item.get('rate'),
                )
        else:
            print('  No BOQ items found in tables')

        tender.status = 'ANALYZED'
        tender.save()

        print('  SUCCESS: Analysis complete!')
        return True

    except Exception as e:
        print(f'  ERROR: {str(e)}')
        tender.status = 'DRAFT'
        tender.save()
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print('=' * 80)
    print('BULK TENDER RE-ANALYSIS (BOQ EXTRACTION)')
    print('=' * 80)

    # Get all tenders
    tender_ids = [38, 39, 40, 41]  # Your 4 tenders

    print(f'\nProcessing {len(tender_ids)} tenders...')

    success_count = 0
    for tid in tender_ids:
        try:
            if reanalyze_tender_direct(tid):
                success_count += 1
        except Exception as e:
            print(f'  FAILED: {e}')

    print('\n' + '=' * 80)
    print(f'COMPLETE: {success_count}/{len(tender_ids)} tenders analyzed')
    print('=' * 80)

    if success_count > 0:
        print('\nBOQ items have been extracted!')
        print('Refresh your tender pages to see the BOQ data.')
        print('\nNext: Use Buyer Eval to add vendor bids!')
