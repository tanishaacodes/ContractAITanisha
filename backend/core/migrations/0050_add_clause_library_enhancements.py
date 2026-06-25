# Generated migration for Clause Library enhancements
# Adds sentence_type, party, cluster_id, financial_impact, and keywords fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0049_add_contract_links'),
    ]

    operations = [
        migrations.AddField(
            model_name='clause',
            name='sentence_type',
            field=models.CharField(
                max_length=50,
                blank=True,
                null=True,
                db_column='sentenceType',
                help_text='Sentence classification: Heading, Definition, Obligation, Risk, or Right',
                choices=[
                    ('HEADING', 'Heading'),
                    ('DEFINITION', 'Definition'),
                    ('OBLIGATION', 'Obligation'),
                    ('RISK', 'Risk'),
                    ('RIGHT', 'Right'),
                ]
            ),
        ),
        migrations.AddField(
            model_name='clause',
            name='party',
            field=models.CharField(
                max_length=50,
                blank=True,
                null=True,
                db_column='party',
                help_text='Party attribution: Contractor, Employer, or Shared',
                choices=[
                    ('CONTRACTOR', 'Contractor'),
                    ('EMPLOYER', 'Employer'),
                    ('SHARED', 'Shared'),
                ]
            ),
        ),
        migrations.AddField(
            model_name='clause',
            name='cluster_id',
            field=models.IntegerField(
                blank=True,
                null=True,
                db_column='clusterId',
                help_text='Numeric cluster ID from KMeans clustering'
            ),
        ),
        migrations.AddField(
            model_name='clause',
            name='financial_impact',
            field=models.FloatField(
                blank=True,
                null=True,
                db_column='financialImpact',
                help_text='Calculated financial impact in currency (risk_score × ₹100,000)'
            ),
        ),
        migrations.AddField(
            model_name='clause',
            name='keywords',
            field=models.JSONField(
                default=dict,
                blank=True,
                db_column='keywords',
                help_text='Risk keywords detected and their weights'
            ),
        ),
        # Add index for efficient querying
        migrations.AddIndex(
            model_name='clause',
            index=models.Index(
                fields=['sentence_type', 'party'],
                name='clause_sent_party_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='clause',
            index=models.Index(
                fields=['cluster_id'],
                name='clause_cluster_idx'
            ),
        ),
    ]
