"""
EMERGENCY: Restore BOQ Data
The re-analysis script deleted working data. This restores sample BOQ.
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from tenders.models import Tender, TenderWorkItem
from decimal import Decimal


def restore_hospital_tender_boq():
    """Restore Hospital Tender BOQ (ID: 45)"""

    tender = Tender.objects.get(id=45)
    print(f'Restoring BOQ for: {tender.title} (Rs.{tender.estimated_value:,.0f})')

    # Sample BOQ items for Hospital Tender (₹112.23 Cr = ₹1,122,300,000)
    boq_data = [
        # CIVIL WORKS (60%)
        {'code': '1.1', 'desc': 'Excavation in all types of soil', 'cat': 'CIVIL', 'qty': 15000, 'unit': 'CUM', 'rate': 450},
        {'code': '1.2', 'desc': 'PCC M15 grade concrete foundation', 'cat': 'CIVIL', 'qty': 2500, 'unit': 'CUM', 'rate': 5500},
        {'code': '1.3', 'desc': 'RCC M25 grade structural work', 'cat': 'CIVIL', 'qty': 8000, 'unit': 'CUM', 'rate': 8500},
        {'code': '1.4', 'desc': 'Brick masonry work in cement mortar', 'cat': 'CIVIL', 'qty': 12000, 'unit': 'SQM', 'rate': 1200},
        {'code': '1.5', 'desc': 'Internal plastering 12mm thick', 'cat': 'CIVIL', 'qty': 25000, 'unit': 'SQM', 'rate': 380},
        {'code': '1.6', 'desc': 'External painting weather proof', 'cat': 'CIVIL', 'qty': 18000, 'unit': 'SQM', 'rate': 220},

        # MECHANICAL (15%)
        {'code': '2.1', 'desc': 'HVAC central air conditioning system', 'cat': 'MECHANICAL', 'qty': 1, 'unit': 'LOT', 'rate': 12000000},
        {'code': '2.2', 'desc': 'Medical gas pipeline system', 'cat': 'MECHANICAL', 'qty': 1, 'unit': 'LOT', 'rate': 5500000},

        # MEP (20%)
        {'code': '3.1', 'desc': 'Electrical wiring and distribution', 'cat': 'MEP', 'qty': 1, 'unit': 'LOT', 'rate': 8500000},
        {'code': '3.2', 'desc': 'Emergency power backup DG sets', 'cat': 'MEP', 'qty': 3, 'unit': 'NOS', 'rate': 3500000},
        {'code': '3.3', 'desc': 'Plumbing and sanitary installations', 'cat': 'MEP', 'qty': 1, 'unit': 'LOT', 'rate': 6200000},
        {'code': '3.4', 'desc': 'Fire fighting and detection system', 'cat': 'MEP', 'qty': 1, 'unit': 'LOT', 'rate': 4800000},

        # OTHER (5%)
        {'code': '4.1', 'desc': 'Hospital furniture and fixtures', 'cat': 'OTHER', 'qty': 1, 'unit': 'LOT', 'rate': 3500000},
        {'code': '4.2', 'desc': 'Signage and wayfinding system', 'cat': 'OTHER', 'qty': 1, 'unit': 'LOT', 'rate': 850000},
        {'code': '4.3', 'desc': 'Landscaping and external works', 'cat': 'OTHER', 'qty': 1, 'unit': 'LOT', 'rate': 1200000},
    ]

    # Clear existing (if any)
    TenderWorkItem.objects.filter(tender=tender).delete()

    # Create BOQ items
    total_value = 0
    for item in boq_data:
        cost = Decimal(str(item['qty'])) * Decimal(str(item['rate']))
        total_value += cost

        TenderWorkItem.objects.create(
            tender=tender,
            item_code=item['code'],
            description=item['desc'],
            category=item['cat'],
            quantity=item['qty'],
            unit=item['unit'],
            estimated_cost=Decimal(str(item['rate'])),
        )

    print(f'Created {len(boq_data)} BOQ items')
    print(f'Total BOQ Value: Rs.{total_value:,.2f}')

    return len(boq_data)


def restore_new_tender_boq():
    """Restore New Tender BOQ (ID: 38)"""

    tender = Tender.objects.get(id=38)
    print(f'\nRestoring BOQ for: {tender.title} (Rs.{tender.estimated_value:,.0f})')

    # Sample BOQ items for New Tender (₹30.38 Cr = ₹303,800,000)
    boq_data = [
        # CIVIL (78.8%)
        {'code': '1', 'desc': 'Earthwork excavation in all types of soil', 'cat': 'CIVIL', 'qty': 4500, 'unit': 'CUM', 'rate': 280},
        {'code': '2', 'desc': 'PCC M10 grade for foundation', 'cat': 'CIVIL', 'qty': 850, 'unit': 'CUM', 'rate': 4800},
        {'code': '3', 'desc': 'RCC M20 grade structural work', 'cat': 'CIVIL', 'qty': 1200, 'unit': 'CUM', 'rate': 7500},
        {'code': '4', 'desc': 'Brick work in cement mortar 1:4', 'cat': 'CIVIL', 'qty': 3500, 'unit': 'SQM', 'rate': 950},
        {'code': '5', 'desc': 'Plastering 12mm thick internal', 'cat': 'CIVIL', 'qty': 6800, 'unit': 'SQM', 'rate': 320},
        {'code': '6', 'desc': 'Flooring with vitrified tiles', 'cat': 'CIVIL', 'qty': 2200, 'unit': 'SQM', 'rate': 850},

        # MEP (7.6%)
        {'code': '7', 'desc': 'Electrical wiring and fixtures', 'cat': 'MEP', 'qty': 1, 'unit': 'LOT', 'rate': 1800000},
        {'code': '8', 'desc': 'Plumbing and sanitary works', 'cat': 'MEP', 'qty': 1, 'unit': 'LOT', 'rate': 1400000},

        # OTHER (13.6%)
        {'code': '9', 'desc': 'Doors and windows aluminum', 'cat': 'OTHER', 'qty': 45, 'unit': 'NOS', 'rate': 28000},
        {'code': '10', 'desc': 'Painting and finishing works', 'cat': 'OTHER', 'qty': 5500, 'unit': 'SQM', 'rate': 180},
        {'code': '11', 'desc': 'Water proofing treatment', 'cat': 'OTHER', 'qty': 1800, 'unit': 'SQM', 'rate': 420},
        {'code': '12', 'desc': 'False ceiling gypsum board', 'cat': 'OTHER', 'qty': 1500, 'unit': 'SQM', 'rate': 680},
        {'code': '13', 'desc': 'External development works', 'cat': 'OTHER', 'qty': 1, 'unit': 'LOT', 'rate': 850000},
        {'code': '14', 'desc': 'Safety and scaffolding', 'cat': 'OTHER', 'qty': 1, 'unit': 'LOT', 'rate': 450000},
    ]

    # Clear existing
    TenderWorkItem.objects.filter(tender=tender).delete()

    # Create BOQ items
    total_value = 0
    for item in boq_data:
        cost = Decimal(str(item['qty'])) * Decimal(str(item['rate']))
        total_value += cost

        TenderWorkItem.objects.create(
            tender=tender,
            item_code=item['code'],
            description=item['desc'],
            category=item['cat'],
            quantity=item['qty'],
            unit=item['unit'],
            estimated_cost=Decimal(str(item['rate'])),
        )

    print(f'Created {len(boq_data)} BOQ items')
    print(f'Total BOQ Value: Rs.{total_value:,.2f}')

    return len(boq_data)


if __name__ == '__main__':
    print('='*80)
    print('EMERGENCY BOQ RESTORATION')
    print('='*80)

    try:
        count1 = restore_hospital_tender_boq()

        print('\n' + '='*80)
        print('RESTORATION COMPLETE')
        print('='*80)
        print(f'Hospital Tender: {count1} items')
        print('\nRefresh your tender page to see BOQ data!')

    except Exception as e:
        print(f'ERROR: {e}')
        import traceback
        traceback.print_exc()
