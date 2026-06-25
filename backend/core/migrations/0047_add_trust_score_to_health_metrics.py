# Generated manually for Clause Trust Score (CTS) feature

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0046_add_negotiation_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='clausehealthmetrics',
            name='trust_score',
            field=models.FloatField(blank=True, db_column='trustScore', default=None, help_text='Clause Trust Score (CTS) - outcome-based trust (0-1)', null=True),
        ),
        migrations.AddField(
            model_name='clausehealthmetrics',
            name='trust_level',
            field=models.CharField(blank=True, db_column='trustLevel', help_text='Trust level: EXCELLENT, GOOD, FAIR, POOR, CRITICAL', max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='clausehealthmetrics',
            name='trust_badge',
            field=models.CharField(blank=True, db_column='trustBadge', help_text='Trust badge: COURT_PROVEN, DEAL_MAKER, NEGOTIATION_FRAGILE, etc.', max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='clausehealthmetrics',
            name='ambiguity_score',
            field=models.FloatField(blank=True, db_column='ambiguityScore', default=None, help_text='Legal ambiguity score (0-1, higher = more ambiguous)', null=True),
        ),
        migrations.AddField(
            model_name='clausehealthmetrics',
            name='litigation_survival_score',
            field=models.FloatField(blank=True, db_column='litigationSurvivalScore', default=None, help_text='Litigation survival score (0-1)', null=True),
        ),
    ]
