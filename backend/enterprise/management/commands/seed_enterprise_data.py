"""
Management command to seed enterprise risk data
Usage: python manage.py seed_enterprise_data
"""
from django.core.management.base import BaseCommand
from decimal import Decimal
from enterprise.models import Supplier, Commodity, GeoPoliticalRisk


class Command(BaseCommand):
    help = 'Seed enterprise risk intelligence data (suppliers, commodities, geo-political risks)'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding enterprise data...')

        # Create Suppliers
        suppliers_data = [
            {
                'name': 'Tata Steel',
                'tier': 'TIER_1',
                'country': 'India',
                'risk_level': 'LOW',
                'risk_score': 0.25,
                'exposure_amount': Decimal('15000000'),
                'is_single_source': False,
                'dependency_score': 0.6,
                'has_sanctions': False,
                'political_stability_index': 0.75
            },
            {
                'name': 'China Steel Corp',
                'tier': 'TIER_1',
                'country': 'China',
                'risk_level': 'MEDIUM',
                'risk_score': 0.55,
                'exposure_amount': Decimal('22000000'),
                'is_single_source': True,
                'dependency_score': 0.85,
                'has_sanctions': False,
                'political_stability_index': 0.65
            },
            {
                'name': 'Russian Metals Inc',
                'tier': 'TIER_2',
                'country': 'Russia',
                'risk_level': 'HIGH',
                'risk_score': 0.82,
                'exposure_amount': Decimal('8000000'),
                'is_single_source': False,
                'dependency_score': 0.45,
                'has_sanctions': True,
                'political_stability_index': 0.35
            },
            {
                'name': 'German Manufacturing GmbH',
                'tier': 'TIER_1',
                'country': 'Germany',
                'risk_level': 'LOW',
                'risk_score': 0.15,
                'exposure_amount': Decimal('18000000'),
                'is_single_source': False,
                'dependency_score': 0.55,
                'has_sanctions': False,
                'political_stability_index': 0.90
            },
            {
                'name': 'Brazil Mining Co',
                'tier': 'TIER_2',
                'country': 'Brazil',
                'risk_level': 'MEDIUM',
                'risk_score': 0.45,
                'exposure_amount': Decimal('9000000'),
                'is_single_source': False,
                'dependency_score': 0.40,
                'has_sanctions': False,
                'political_stability_index': 0.68
            },
            {
                'name': 'US Steel Partners',
                'tier': 'TIER_1',
                'country': 'USA',
                'risk_level': 'LOW',
                'risk_score': 0.18,
                'exposure_amount': Decimal('25000000'),
                'is_single_source': False,
                'dependency_score': 0.70,
                'has_sanctions': False,
                'political_stability_index': 0.88
            },
        ]

        for supplier_data in suppliers_data:
            supplier, created = Supplier.objects.get_or_create(
                name=supplier_data['name'],
                defaults=supplier_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created supplier: {supplier.name}'))
            else:
                self.stdout.write(f'Supplier already exists: {supplier.name}')

        # Create Commodities
        commodities_data = [
            {
                'name': 'Steel',
                'category': 'Metals',
                'current_price': Decimal('800'),
                'currency': 'USD',
                'unit': 'per ton',
                'volatility': 0.30,
                'drift': 0.05,
                'total_exposure': Decimal('12000000')
            },
            {
                'name': 'Copper',
                'category': 'Metals',
                'current_price': Decimal('9500'),
                'currency': 'USD',
                'unit': 'per ton',
                'volatility': 0.40,
                'drift': 0.08,
                'total_exposure': Decimal('5000000')
            },
            {
                'name': 'Oil',
                'category': 'Energy',
                'current_price': Decimal('85'),
                'currency': 'USD',
                'unit': 'per barrel',
                'volatility': 0.50,
                'drift': 0.03,
                'total_exposure': Decimal('8000000')
            },
            {
                'name': 'Aluminum',
                'category': 'Metals',
                'current_price': Decimal('2400'),
                'currency': 'USD',
                'unit': 'per ton',
                'volatility': 0.25,
                'drift': 0.06,
                'total_exposure': Decimal('4000000')
            },
            {
                'name': 'Gold',
                'category': 'Precious Metals',
                'current_price': Decimal('2050'),
                'currency': 'USD',
                'unit': 'per ounce',
                'volatility': 0.20,
                'drift': 0.04,
                'total_exposure': Decimal('3000000')
            },
        ]

        for commodity_data in commodities_data:
            commodity, created = Commodity.objects.get_or_create(
                name=commodity_data['name'],
                defaults=commodity_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created commodity: {commodity.name}'))
            else:
                self.stdout.write(f'Commodity already exists: {commodity.name}')

        # Create Geopolitical Risks
        geo_risks_data = [
            {
                'country': 'India',
                'region': 'South Asia',
                'latitude': 20.5937,
                'longitude': 78.9629,
                'political_stability_score': 0.75,
                'risk_severity': 'MEDIUM',
                'has_active_sanctions': False,
                'sanction_details': None,
                'gdp_growth_rate': 7.2,
                'inflation_rate': 5.4,
                'currency_stability': 0.72,
                'total_exposure': Decimal('45000000')
            },
            {
                'country': 'China',
                'region': 'East Asia',
                'latitude': 35.8617,
                'longitude': 104.1954,
                'political_stability_score': 0.65,
                'risk_severity': 'MEDIUM',
                'has_active_sanctions': False,
                'sanction_details': None,
                'gdp_growth_rate': 5.0,
                'inflation_rate': 2.1,
                'currency_stability': 0.78,
                'total_exposure': Decimal('62000000')
            },
            {
                'country': 'Russia',
                'region': 'Eastern Europe',
                'latitude': 61.5240,
                'longitude': 105.3188,
                'political_stability_score': 0.35,
                'risk_severity': 'HIGH',
                'has_active_sanctions': True,
                'sanction_details': 'Comprehensive economic sanctions due to geopolitical conflicts',
                'gdp_growth_rate': -2.1,
                'inflation_rate': 6.8,
                'currency_stability': 0.45,
                'total_exposure': Decimal('18000000')
            },
            {
                'country': 'Germany',
                'region': 'Western Europe',
                'latitude': 51.1657,
                'longitude': 10.4515,
                'political_stability_score': 0.90,
                'risk_severity': 'LOW',
                'has_active_sanctions': False,
                'sanction_details': None,
                'gdp_growth_rate': 0.8,
                'inflation_rate': 3.2,
                'currency_stability': 0.95,
                'total_exposure': Decimal('38000000')
            },
            {
                'country': 'USA',
                'region': 'North America',
                'latitude': 37.0902,
                'longitude': -95.7129,
                'political_stability_score': 0.88,
                'risk_severity': 'LOW',
                'has_active_sanctions': False,
                'sanction_details': None,
                'gdp_growth_rate': 2.5,
                'inflation_rate': 3.7,
                'currency_stability': 0.92,
                'total_exposure': Decimal('55000000')
            },
            {
                'country': 'Brazil',
                'region': 'South America',
                'latitude': -14.2350,
                'longitude': -51.9253,
                'political_stability_score': 0.68,
                'risk_severity': 'MEDIUM',
                'has_active_sanctions': False,
                'sanction_details': None,
                'gdp_growth_rate': 2.9,
                'inflation_rate': 4.5,
                'currency_stability': 0.65,
                'total_exposure': Decimal('22000000')
            },
        ]

        for geo_data in geo_risks_data:
            geo_risk, created = GeoPoliticalRisk.objects.get_or_create(
                country=geo_data['country'],
                defaults=geo_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created geopolitical risk: {geo_risk.country}'))
            else:
                self.stdout.write(f'Geopolitical risk already exists: {geo_risk.country}')

        self.stdout.write(self.style.SUCCESS('[SUCCESS] Enterprise data seeding completed!'))
