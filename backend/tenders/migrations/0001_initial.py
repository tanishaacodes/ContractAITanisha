# Manual migration for tenders app

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Tender',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=500)),
                ('reference_number', models.CharField(blank=True, max_length=200, null=True)),
                ('estimated_value', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('bid_security', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('emd_amount', models.DecimalField(blank=True, decimal_places=2, help_text='Earnest Money Deposit', max_digits=20, null=True)),
                ('submission_deadline', models.DateTimeField(blank=True, null=True)),
                ('technical_opening_date', models.DateTimeField(blank=True, null=True)),
                ('financial_opening_date', models.DateTimeField(blank=True, null=True)),
                ('completion_period_days', models.IntegerField(blank=True, null=True)),
                ('pdf_file', models.FileField(blank=True, null=True, upload_to='tenders/')),
                ('pdf_url', models.URLField(blank=True, null=True)),
                ('summary', models.TextField(blank=True, null=True)),
                ('scope_of_work', models.TextField(blank=True, null=True)),
                ('status', models.CharField(choices=[('DRAFT', 'Draft'), ('ANALYZING', 'Analyzing'), ('ANALYZED', 'Analyzed'), ('BIDDING', 'Bidding'), ('SUBMITTED', 'Submitted'), ('WON', 'Won'), ('LOST', 'Lost')], default='DRAFT', max_length=50)),
                ('organization', models.CharField(blank=True, max_length=300, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('uploaded_by_id', models.CharField(max_length=36, db_column='uploadedById')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='CompanyProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('company_name', models.CharField(max_length=300)),
                ('registration_number', models.CharField(blank=True, max_length=100, null=True)),
                ('annual_turnover', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('net_worth', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('years_in_business', models.IntegerField(blank=True, null=True)),
                ('total_projects_completed', models.IntegerField(default=0)),
                ('similar_projects_completed', models.IntegerField(default=0)),
                ('past_win_rate', models.FloatField(default=0.0)),
                ('average_project_margin', models.FloatField(default=0.0)),
                ('technical_capabilities', models.JSONField(blank=True, null=True)),
                ('certifications', models.JSONField(blank=True, null=True)),
                ('key_equipment', models.JSONField(blank=True, null=True)),
                ('key_personnel', models.JSONField(blank=True, null=True)),
                ('company_strengths', models.TextField(blank=True, null=True)),
                ('competitive_advantages', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user_id', models.CharField(max_length=36, db_column='userId', unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='TenderSection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('section_number', models.CharField(max_length=50)),
                ('title', models.TextField()),
                ('level', models.IntegerField(default=0)),
                ('content', models.TextField()),
                ('vector_id', models.CharField(blank=True, max_length=100, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('parent_id', models.BigIntegerField(blank=True, null=True)),
                ('tender_id', models.BigIntegerField()),
            ],
            options={
                'ordering': ['section_number'],
            },
        ),
        migrations.CreateModel(
            name='TenderWorkItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('item_code', models.CharField(blank=True, max_length=100, null=True)),
                ('description', models.TextField()),
                ('category', models.CharField(choices=[('CIVIL', 'Civil Work'), ('MECHANICAL', 'Mechanical Work'), ('MEP', 'MEP Work'), ('ELECTRICAL', 'Electrical Work'), ('PLUMBING', 'Plumbing Work'), ('HVAC', 'HVAC Work'), ('OTHER', 'Other')], max_length=50)),
                ('quantity', models.FloatField(blank=True, null=True)),
                ('unit', models.CharField(blank=True, max_length=50, null=True)),
                ('estimated_cost', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('base_material_cost', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('base_labor_cost', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('base_equipment_cost', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('overhead_percentage', models.FloatField(default=10.0)),
                ('risk_factor', models.FloatField(default=0.05)),
                ('final_unit_cost', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('tender_id', models.BigIntegerField()),
            ],
            options={
                'ordering': ['item_code'],
            },
        ),
        migrations.CreateModel(
            name='TenderEligibility',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('min_turnover', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('turnover_multiplier', models.FloatField(blank=True, help_text='Turnover required as multiple of tender value', null=True)),
                ('min_net_worth', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('min_projects', models.IntegerField(blank=True, null=True)),
                ('min_project_value', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('similar_work_required', models.BooleanField(default=False)),
                ('technical_criteria', models.JSONField(blank=True, null=True)),
                ('other_requirements', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tender_id', models.BigIntegerField(unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='TenderRisk',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('category', models.CharField(choices=[('UNLIMITED_LIABILITY', 'Unlimited Liability'), ('HIGH_LD', 'High Liquidated Damages'), ('ONE_SIDED_TERMINATION', 'One-Sided Termination'), ('PAYMENT_TERMS', 'Unfavorable Payment Terms'), ('PERFORMANCE_GUARANTEE', 'High Performance Guarantee'), ('WARRANTY_PERIOD', 'Extended Warranty Period'), ('FORCE_MAJEURE', 'Limited Force Majeure'), ('INDEMNITY', 'Broad Indemnity Clause'), ('DISPUTE_RESOLUTION', 'Unfavorable Dispute Resolution'), ('SCOPE_AMBIGUITY', 'Scope Ambiguity'), ('OTHER', 'Other Risk')], max_length=100)),
                ('description', models.TextField()),
                ('clause_reference', models.CharField(blank=True, max_length=200, null=True)),
                ('financial_exposure', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('severity', models.CharField(choices=[('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High'), ('CRITICAL', 'Critical')], default='MEDIUM', max_length=20)),
                ('severity_score', models.FloatField(default=0.5)),
                ('mitigation_suggestion', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('tender_id', models.BigIntegerField()),
            ],
            options={
                'ordering': ['-severity_score', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='TenderConflict',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('clause_a', models.TextField()),
                ('clause_a_reference', models.CharField(blank=True, max_length=200, null=True)),
                ('clause_b', models.TextField()),
                ('clause_b_reference', models.CharField(blank=True, max_length=200, null=True)),
                ('contradiction_score', models.FloatField(default=0.0)),
                ('explanation', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('tender_id', models.BigIntegerField()),
            ],
            options={
                'ordering': ['-contradiction_score', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='BidScenario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('margin_percentage', models.FloatField()),
                ('total_cost', models.DecimalField(decimal_places=2, max_digits=20)),
                ('bid_price', models.DecimalField(decimal_places=2, max_digits=20)),
                ('win_probability', models.FloatField()),
                ('expected_profit', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('is_recommended', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('tender_id', models.BigIntegerField()),
            ],
            options={
                'ordering': ['-win_probability'],
            },
        ),
        migrations.CreateModel(
            name='TenderProposal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('technical_compliance', models.TextField(blank=True, null=True)),
                ('construction_methodology', models.TextField(blank=True, null=True)),
                ('resource_mobilization', models.TextField(blank=True, null=True)),
                ('risk_mitigation', models.TextField(blank=True, null=True)),
                ('commercial_positioning', models.TextField(blank=True, null=True)),
                ('schedule_assurance', models.TextField(blank=True, null=True)),
                ('value_engineering', models.TextField(blank=True, null=True)),
                ('full_proposal', models.TextField(blank=True, null=True)),
                ('competitor_analysis', models.JSONField(blank=True, null=True)),
                ('competitive_advantage', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tender_id', models.BigIntegerField(unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='TenderNegotiation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('issue_type', models.CharField(max_length=100)),
                ('original_clause', models.TextField()),
                ('clause_reference', models.CharField(blank=True, max_length=200, null=True)),
                ('counter_proposal', models.TextField()),
                ('rationale', models.TextField(blank=True, null=True)),
                ('negotiation_status', models.CharField(choices=[('OPEN', 'Open'), ('IN_PROGRESS', 'In Progress'), ('ACCEPTED', 'Accepted'), ('REJECTED', 'Rejected'), ('PARTIAL', 'Partially Accepted')], default='OPEN', max_length=20)),
                ('acceptance_probability', models.FloatField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tender_id', models.BigIntegerField()),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PreBidQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('category', models.CharField(choices=[('COMMERCIAL', 'Commercial'), ('TECHNICAL', 'Technical'), ('ELIGIBILITY', 'Eligibility'), ('RISK', 'Risk Allocation'), ('TIMELINE', 'Timeline'), ('SCOPE', 'Scope Clarification'), ('OTHER', 'Other')], max_length=50)),
                ('question', models.TextField()),
                ('rationale', models.TextField(blank=True, null=True)),
                ('is_submitted', models.BooleanField(default=False)),
                ('response', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('tender_id', models.BigIntegerField()),
            ],
            options={
                'ordering': ['category', '-created_at'],
            },
        ),
    ]
