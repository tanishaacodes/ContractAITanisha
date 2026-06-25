# Generated manually for risk analysis models

from django.db import migrations, models
import django.db.models.deletion
import core.models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_alter_role_name_to_varchar'),
    ]

    operations = [
        migrations.CreateModel(
            name='TemplateClause',
            fields=[
                ('id', models.CharField(default=core.models.generate_uuid, editable=False, max_length=36, primary_key=True, serialize=False)),
                ('contract_type', models.CharField(db_column='contractType', max_length=100)),
                ('clause_name', models.CharField(db_column='clauseName', max_length=150)),
                ('importance', models.CharField(choices=[('CRITICAL', 'Critical'), ('IMPORTANT', 'Important'), ('OPTIONAL', 'Optional')], default='IMPORTANT', max_length=20)),
                ('description', models.TextField(blank=True, null=True)),
                ('standard_language', models.TextField(blank=True, db_column='standardLanguage', null=True)),
                ('risk_keywords', models.JSONField(blank=True, db_column='riskKeywords', default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
                ('updated_at', models.DateTimeField(auto_now=True, db_column='updatedAt')),
            ],
            options={
                'db_table': 'template_clauses',
                'ordering': ['contract_type', 'importance', 'clause_name'],
            },
        ),
        migrations.CreateModel(
            name='ContractRiskAnalysis',
            fields=[
                ('id', models.CharField(default=core.models.generate_uuid, editable=False, max_length=36, primary_key=True, serialize=False)),
                ('risk_level', models.CharField(choices=[('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High')], db_column='riskLevel', max_length=20)),
                ('risk_score', models.IntegerField(db_column='riskScore', default=0)),
                ('total_deviations', models.IntegerField(db_column='totalDeviations', default=0)),
                ('critical_issues', models.IntegerField(db_column='criticalIssues', default=0)),
                ('medium_issues', models.IntegerField(db_column='mediumIssues', default=0)),
                ('low_issues', models.IntegerField(db_column='lowIssues', default=0)),
                ('analysis_summary', models.TextField(blank=True, db_column='analysisSummary', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
                ('updated_at', models.DateTimeField(auto_now=True, db_column='updatedAt')),
                ('contract', models.OneToOneField(db_column='contractId', on_delete=django.db.models.deletion.CASCADE, related_name='risk_analysis', to='core.contract')),
            ],
            options={
                'db_table': 'contract_risk_analysis',
            },
        ),
        migrations.CreateModel(
            name='ClauseDeviation',
            fields=[
                ('id', models.CharField(default=core.models.generate_uuid, editable=False, max_length=36, primary_key=True, serialize=False)),
                ('clause_name', models.CharField(db_column='clauseName', max_length=150)),
                ('deviation_type', models.CharField(choices=[('MISSING', 'Missing Clause'), ('UNFAVORABLE', 'Unfavorable Terms'), ('WEAK', 'Weak Protection')], db_column='deviationType', max_length=20)),
                ('severity', models.CharField(choices=[('HIGH', 'High'), ('MEDIUM', 'Medium'), ('LOW', 'Low')], max_length=20)),
                ('description', models.TextField()),
                ('recommendation', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
                ('updated_at', models.DateTimeField(auto_now=True, db_column='updatedAt')),
                ('risk_analysis', models.ForeignKey(db_column='riskAnalysisId', on_delete=django.db.models.deletion.CASCADE, related_name='deviations', to='core.contractriskanalysis')),
            ],
            options={
                'db_table': 'clause_deviations',
                'ordering': ['-severity', 'clause_name'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='templateclause',
            unique_together={('contract_type', 'clause_name')},
        ),
    ]
