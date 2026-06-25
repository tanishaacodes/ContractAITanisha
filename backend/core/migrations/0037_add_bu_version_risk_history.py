# Generated migration for Business Unit, Version, and Risk History features

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0036_add_embedding_first_models'),
    ]

    operations = [
        # Add business_unit to contracts table
        migrations.AddField(
            model_name='contract',
            name='business_unit',
            field=models.CharField(
                max_length=100,
                null=True,
                blank=True,
                db_column='businessUnit',
                help_text='Business unit (EPC, Oil & Gas, Defense, etc.)'
            ),
        ),
        # Add version field to contracts table
        migrations.AddField(
            model_name='contract',
            name='version',
            field=models.IntegerField(default=1, db_column='version', help_text='Contract version number'),
        ),
        # Add version_date field
        migrations.AddField(
            model_name='contract',
            name='version_date',
            field=models.DateTimeField(
                null=True,
                blank=True,
                db_column='versionDate',
                help_text='Date of this version'
            ),
        ),
        # Add total_liability field for financial analysis
        migrations.AddField(
            model_name='contract',
            name='total_liability',
            field=models.DecimalField(
                max_digits=18,
                decimal_places=2,
                default=0,
                db_column='totalLiability',
                help_text='Total liability exposure in contract'
            ),
        ),
        # Create ContractRiskHistory table
        migrations.CreateModel(
            name='ContractRiskHistory',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('contract_id', models.CharField(
                    max_length=36,
                    db_column='contractId',
                    help_text='Contract ID (UUID)'
                )),
                ('version', models.IntegerField(db_column='version')),
                ('overall_risk', models.FloatField(db_column='overallRisk')),
                ('ip_risk', models.FloatField(db_column='ipRisk', default=0)),
                ('liability_risk', models.FloatField(db_column='liabilityRisk', default=0)),
                ('geography_risk', models.FloatField(db_column='geographyRisk', default=0)),
                ('recorded_at', models.DateTimeField(auto_now_add=True, db_column='recordedAt')),
            ],
            options={
                'db_table': 'contract_risk_history',
                'ordering': ['contract', 'version'],
            },
        ),
    ]
