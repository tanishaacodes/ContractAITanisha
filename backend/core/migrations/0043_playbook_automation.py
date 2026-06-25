# Manual migration – Playbook Automation tables
# Depends on 0042 (the last existing migration).
# Does NOT touch any pre-existing model – only adds the 4 new tables.

from django.db import migrations, models


def generate_uuid():
    import uuid
    return str(uuid.uuid4())


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0042_add_counterparty_to_contract'),
    ]

    operations = [
        # ── 1. LegalPlaybook ──────────────────────────────────────────
        migrations.CreateModel(
            name='LegalPlaybook',
            fields=[
                ('id', models.CharField(default=generate_uuid, editable=False, max_length=36, primary_key=True, serialize=False)),
                ('clause_type', models.CharField(
                    choices=[
                        ('LIABILITY', 'Liability'), ('TERMINATION', 'Termination'),
                        ('INDEMNIFICATION', 'Indemnification'), ('IP_OWNERSHIP', 'IP Ownership'),
                        ('CONFIDENTIALITY', 'Confidentiality'), ('PAYMENT', 'Payment'),
                        ('GOVERNING_LAW', 'Governing Law'), ('FORCE_MAJEURE', 'Force Majeure'),
                        ('DATA_PRIVACY', 'Data Privacy'), ('NON_COMPETE', 'Non-Compete'),
                        ('LIMITATION_OF_DAMAGES', 'Limitation of Damages'),
                        ('ASSIGNMENT', 'Assignment'), ('RENEWAL', 'Renewal'),
                        ('DISPUTE_RESOLUTION', 'Dispute Resolution'), ('OTHER', 'Other'),
                    ],
                    db_column='clauseType', max_length=50,
                )),
                ('jurisdiction', models.CharField(default='global', max_length=100)),
                ('standard_clause', models.TextField(db_column='standardClause')),
                ('fallback_clause', models.TextField(db_column='fallbackClause')),
                ('embedding', models.JSONField(blank=True, default=list)),
                ('embedding_model', models.CharField(db_column='embeddingModel', default='all-MiniLM-L6-v2', max_length=100)),
                ('similarity_threshold', models.FloatField(db_column='similarityThreshold', default=0.85)),
                ('mandatory', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
                ('updated_at', models.DateTimeField(auto_now=True, db_column='updatedAt')),
            ],
            options={
                'db_table': 'legal_playbooks',
                'ordering': ['clause_type', 'jurisdiction'],
            },
        ),
        migrations.AddIndex(
            model_name='legalplaybook',
            index=models.Index(fields=['clause_type', 'jurisdiction'], name='legal_playb_clauseT_idx001'),
        ),
        migrations.AddIndex(
            model_name='legalplaybook',
            index=models.Index(fields=['mandatory'], name='legal_playb_mandato_idx002'),
        ),

        # ── 2. ClausePlaybookResult ───────────────────────────────────
        migrations.CreateModel(
            name='ClausePlaybookResult',
            fields=[
                ('id', models.CharField(default=generate_uuid, editable=False, max_length=36, primary_key=True, serialize=False)),
                ('similarity_score', models.FloatField(db_column='similarityScore')),
                ('is_standard', models.BooleanField(db_column='isStandard')),
                ('suggested_text', models.TextField(blank=True, db_column='suggestedText', null=True)),
                ('fallback_accepted', models.BooleanField(db_column='fallbackAccepted', default=False)),
                ('accepted_at', models.DateTimeField(blank=True, db_column='acceptedAt', null=True)),
                ('evaluated_at', models.DateTimeField(auto_now_add=True, db_column='evaluatedAt')),
                ('clause_id', models.CharField(db_column='clauseId', max_length=36)),
                ('playbook_id', models.CharField(db_column='playbookId', max_length=36)),
            ],
            options={
                'db_table': 'clause_playbook_results',
                'ordering': ['-evaluated_at'],
            },
        ),
        migrations.AddIndex(
            model_name='clauseplaybookresult',
            index=models.Index(fields=['clause_id', 'playbook_id'], name='clause_play_clauseI_idx003'),
        ),
        migrations.AddIndex(
            model_name='clauseplaybookresult',
            index=models.Index(fields=['is_standard'], name='clause_play_isStand_idx004'),
        ),

        # ── 3. PlaybookDriftSnapshot ──────────────────────────────────
        migrations.CreateModel(
            name='PlaybookDriftSnapshot',
            fields=[
                ('id', models.CharField(default=generate_uuid, editable=False, max_length=36, primary_key=True, serialize=False)),
                ('clause_type', models.CharField(db_column='clauseType', max_length=50)),
                ('jurisdiction', models.CharField(max_length=100)),
                ('avg_similarity', models.FloatField(db_column='avgSimilarity')),
                ('non_standard_rate', models.FloatField(db_column='nonStandardRate')),
                ('snapshot_date', models.DateField(auto_now_add=True, db_column='snapshotDate')),
            ],
            options={
                'db_table': 'playbook_drift_snapshots',
                'ordering': ['-snapshot_date'],
            },
        ),
        migrations.AddIndex(
            model_name='playbookdriftsnapshot',
            index=models.Index(fields=['clause_type', 'jurisdiction', '-snapshot_date'], name='playbook_dr_clauseT_idx005'),
        ),

        # ── 4. PlaybookUpdateSuggestion ───────────────────────────────
        migrations.CreateModel(
            name='PlaybookUpdateSuggestion',
            fields=[
                ('id', models.CharField(default=generate_uuid, editable=False, max_length=36, primary_key=True, serialize=False)),
                ('clause_type', models.CharField(db_column='clauseType', max_length=50)),
                ('jurisdiction', models.CharField(max_length=100)),
                ('reason', models.TextField()),
                ('suggested_standard', models.TextField(db_column='suggestedStandard')),
                ('avg_similarity', models.FloatField(db_column='avgSimilarity')),
                ('non_standard_rate', models.FloatField(db_column='nonStandardRate')),
                ('status', models.CharField(
                    choices=[('OPEN', 'Open'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')],
                    default='OPEN', max_length=20,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
                ('updated_at', models.DateTimeField(auto_now=True, db_column='updatedAt')),
            ],
            options={
                'db_table': 'playbook_update_suggestions',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='playbookupdatesuggestion',
            index=models.Index(fields=['status', 'clause_type'], name='playbook_up_status_idx006'),
        ),
    ]
