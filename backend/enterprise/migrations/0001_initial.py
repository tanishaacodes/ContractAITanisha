# Generated migration for enterprise app
from django.db import migrations, models
import django.db.models.deletion
import core.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '__latest__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Commodity',
            fields=[
                ('id', models.CharField(default=core.models.generate_uuid, editable=False, max_length=36, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('category', models.CharField(blank=True, max_length=100, null=True)),
                ('current_price', models.DecimalField(decimal_places=2, db_column='currentPrice', max_digits=18)),
                ('currency', models.CharField(default='USD', max_length=10)),
                ('unit', models.CharField(help_text='e.g., per ton, per barrel', max_length=50)),
                ('volatility', models.FloatField(default=0.3, help_text='Annual volatility (sigma)')),
                ('drift', models.FloatField(default=0.05, help_text='Expected drift (mu)')),
                ('total_exposure', models.DecimalField(db_column='totalExposure', decimal_places=2, default=0, max_digits=18)),
                ('last_updated', models.DateTimeField(auto_now=True, db_column='lastUpdated')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
            ],
            options={
                'db_table': 'enterprise_commodities',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='GeoPoliticalRisk',
            fields=[
                ('id', models.CharField(default=core.models.generate_uuid, editable=False, max_length=36, primary_key=True, serialize=False)),
                ('country', models.CharField(max_length=100, unique=True)),
                ('region', models.CharField(max_length=100)),
                ('latitude', models.FloatField()),
                ('longitude', models.FloatField()),
                ('political_stability_score', models.FloatField(db_column='politicalStabilityScore', help_text='0.0 - 1.0')),
                ('risk_severity', models.CharField(choices=[('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High'), ('CRITICAL', 'Critical')], db_column='riskSeverity', max_length=20)),
                ('has_active_sanctions', models.BooleanField(db_column='hasActiveSanctions', default=False)),
                ('sanction_details', models.TextField(blank=True, db_column='sanctionDetails', null=True)),
                ('gdp_growth_rate', models.FloatField(blank=True, db_column='gdpGrowthRate', null=True)),
                ('inflation_rate', models.FloatField(blank=True, db_column='inflationRate', null=True)),
                ('currency_stability', models.FloatField(blank=True, db_column='currencyStability', null=True)),
                ('total_exposure', models.DecimalField(db_column='totalExposure', decimal_places=2, default=0, max_digits=18)),
                ('last_updated', models.DateTimeField(auto_now=True, db_column='lastUpdated')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
            ],
            options={
                'db_table': 'enterprise_geopolitical_risks',
                'ordering': ['country'],
            },
        ),
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('id', models.CharField(default=core.models.generate_uuid, editable=False, max_length=36, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('tier', models.CharField(choices=[('TIER_1', 'Tier 1 - Direct'), ('TIER_2', 'Tier 2 - Indirect'), ('TIER_3', 'Tier 3 - Sub-supplier')], max_length=20)),
                ('country', models.CharField(max_length=100)),
                ('risk_level', models.CharField(choices=[('LOW', 'Low Risk'), ('MEDIUM', 'Medium Risk'), ('HIGH', 'High Risk'), ('CRITICAL', 'Critical Risk')], db_column='riskLevel', max_length=20)),
                ('risk_score', models.FloatField(db_column='riskScore', default=0.0, help_text='Risk score 0.0 - 1.0')),
                ('exposure_amount', models.DecimalField(db_column='exposureAmount', decimal_places=2, default=0, max_digits=18)),
                ('is_single_source', models.BooleanField(db_column='isSingleSource', default=False)),
                ('dependency_score', models.FloatField(db_column='dependencyScore', default=0.0)),
                ('has_sanctions', models.BooleanField(db_column='hasSanctions', default=False)),
                ('political_stability_index', models.FloatField(db_column='politicalStabilityIndex', default=0.5)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
                ('updated_at', models.DateTimeField(auto_now=True, db_column='updatedAt')),
            ],
            options={
                'db_table': 'enterprise_suppliers',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='MonteCarloSimulation',
            fields=[
                ('id', models.CharField(default=core.models.generate_uuid, editable=False, max_length=36, primary_key=True, serialize=False)),
                ('iterations', models.IntegerField(default=30000)),
                ('confidence_level', models.FloatField(db_column='confidenceLevel', default=0.95)),
                ('mean_exposure', models.DecimalField(db_column='meanExposure', decimal_places=2, max_digits=18)),
                ('median_exposure', models.DecimalField(db_column='medianExposure', decimal_places=2, max_digits=18)),
                ('std_dev', models.DecimalField(db_column='stdDev', decimal_places=2, max_digits=18)),
                ('var_90', models.DecimalField(db_column='var90', decimal_places=2, max_digits=18)),
                ('var_95', models.DecimalField(db_column='var95', decimal_places=2, max_digits=18)),
                ('var_99', models.DecimalField(db_column='var99', decimal_places=2, max_digits=18)),
                ('cvar_95', models.DecimalField(db_column='cvar95', decimal_places=2, max_digits=18)),
                ('cvar_99', models.DecimalField(db_column='cvar99', decimal_places=2, max_digits=18)),
                ('min_exposure', models.DecimalField(db_column='minExposure', decimal_places=2, max_digits=18)),
                ('max_exposure', models.DecimalField(db_column='maxExposure', decimal_places=2, max_digits=18)),
                ('distribution_data', models.JSONField(db_column='distributionData', help_text='Histogram distribution data')),
                ('convergence_data', models.JSONField(db_column='convergenceData', help_text='Convergence path data')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
                ('contract', models.ForeignKey(db_column='contractId', on_delete=django.db.models.deletion.CASCADE, related_name='monte_carlo_simulations', to='core.contract', to_field='id')),
            ],
            options={
                'db_table': 'enterprise_monte_carlo_simulations',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ContractSupplier',
            fields=[
                ('id', models.CharField(default=core.models.generate_uuid, editable=False, max_length=36, primary_key=True, serialize=False)),
                ('exposure_amount', models.DecimalField(db_column='exposureAmount', decimal_places=2, max_digits=18)),
                ('dependency_level', models.CharField(choices=[('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High'), ('CRITICAL', 'Critical')], db_column='dependencyLevel', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
                ('contract', models.ForeignKey(db_column='contractId', on_delete=django.db.models.deletion.CASCADE, related_name='contract_suppliers', to='core.contract', to_field='id')),
                ('supplier', models.ForeignKey(db_column='supplierId', on_delete=django.db.models.deletion.CASCADE, related_name='supplier_contracts', to='enterprise.supplier', to_field='id')),
            ],
            options={
                'db_table': 'enterprise_contract_suppliers',
                'unique_together': {('contract', 'supplier')},
            },
        ),
        migrations.CreateModel(
            name='ContractCommodity',
            fields=[
                ('id', models.CharField(default=core.models.generate_uuid, editable=False, max_length=36, primary_key=True, serialize=False)),
                ('quantity', models.DecimalField(decimal_places=4, max_digits=18)),
                ('unit_price', models.DecimalField(db_column='unitPrice', decimal_places=2, max_digits=18)),
                ('total_value', models.DecimalField(db_column='totalValue', decimal_places=2, max_digits=18)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
                ('commodity', models.ForeignKey(db_column='commodityId', on_delete=django.db.models.deletion.CASCADE, related_name='commodity_contracts', to='enterprise.commodity', to_field='id')),
                ('contract', models.ForeignKey(db_column='contractId', on_delete=django.db.models.deletion.CASCADE, related_name='contract_commodities', to='core.contract', to_field='id')),
            ],
            options={
                'db_table': 'enterprise_contract_commodities',
                'unique_together': {('contract', 'commodity')},
            },
        ),
    ]
