# Generated manually for executive summary feature

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_risk_analysis_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='contractriskanalysis',
            name='executive_summary',
            field=models.TextField(blank=True, db_column='executiveSummary', null=True),
        ),
        migrations.AddField(
            model_name='contractriskanalysis',
            name='summary_generated_at',
            field=models.DateTimeField(blank=True, db_column='summaryGeneratedAt', null=True),
        ),
    ]
