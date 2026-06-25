# Generated manually for Temporal Clause Evolution feature

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0047_add_trust_score_to_health_metrics'),
    ]

    operations = [
        # Clause Usage History (by year, industry, geography)
        migrations.CreateModel(
            name='ClauseUsageHistory',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('clause_id', models.CharField(db_column='clauseId', max_length=36, help_text='Clause ID (no FK constraint)')),
                ('year', models.IntegerField(help_text='Year of usage')),
                ('usage_count', models.IntegerField(default=0, db_column='usageCount')),
                ('industry', models.CharField(max_length=100, blank=True, null=True)),
                ('geography', models.CharField(max_length=100, blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
            ],
            options={
                'db_table': 'clause_usage_history',
                'ordering': ['clause_id', '-year'],
                'indexes': [
                    models.Index(fields=['clause_id', '-year'], name='idx_usage_clause_year'),
                    models.Index(fields=['year', 'industry'], name='idx_usage_year_industry'),
                ],
            },
        ),

        # Clause Risk/Trust Timeline
        migrations.CreateModel(
            name='ClauseRiskTimeline',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('clause_id', models.CharField(db_column='clauseId', max_length=36, help_text='Clause ID (no FK constraint)')),
                ('year', models.IntegerField(help_text='Year of snapshot')),
                ('risk_score', models.FloatField(db_column='riskScore', help_text='Risk score at this time')),
                ('trust_score', models.FloatField(blank=True, null=True, db_column='trustScore', help_text='Trust score at this time')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
            ],
            options={
                'db_table': 'clause_risk_timeline',
                'ordering': ['clause_id', '-year'],
                'indexes': [
                    models.Index(fields=['clause_id', '-year'], name='idx_risk_clause_year'),
                ],
            },
        ),

        # Legal Events (regulatory changes, case law)
        migrations.CreateModel(
            name='LegalEvent',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('year', models.IntegerField(help_text='Year of event')),
                ('jurisdiction', models.CharField(max_length=100, help_text='Jurisdiction affected')),
                ('event_type', models.CharField(
                    max_length=20,
                    choices=[('REGULATION', 'Regulation'), ('CASE_LAW', 'Case Law')],
                    db_column='eventType'
                )),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('impact_severity', models.CharField(
                    max_length=20,
                    choices=[('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High'), ('CRITICAL', 'Critical')],
                    db_column='impactSeverity',
                    default='MEDIUM'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
            ],
            options={
                'db_table': 'legal_events',
                'ordering': ['-year'],
                'indexes': [
                    models.Index(fields=['-year', 'jurisdiction'], name='idx_legal_year_juris'),
                    models.Index(fields=['event_type', 'jurisdiction'], name='idx_legal_type_juris'),
                ],
            },
        ),
    ]
