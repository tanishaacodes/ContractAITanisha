# Hand-written migration – backfills the five CreateModel operations that were
# accidentally omitted before 0038 was generated.  The field definitions here
# represent the state *before* 0038 alters them (0038 depends on this migration
# and will apply its own AlterField / RemoveIndex / AddIndex on top).

import core.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0037_add_bu_version_risk_history'),
    ]

    operations = [
        # ── ClauseDeviationScore ──────────────────────────────────────────
        migrations.CreateModel(
            name='ClauseDeviationScore',
            fields=[
                ('id', models.CharField(default=core.models.generate_uuid, editable=False, max_length=36, primary_key=True, serialize=False)),
                ('clause_id', models.CharField(db_column='clauseId', max_length=36, unique=True)),
                ('contract_id', models.CharField(db_column='contractId', max_length=36)),
                ('gold_standard_similarity', models.FloatField(blank=True, db_column='goldStandardSimilarity', null=True)),
                ('industry_benchmark_similarity', models.FloatField(blank=True, db_column='industryBenchmarkSimilarity', null=True)),
                ('past_accepted_similarity', models.FloatField(blank=True, db_column='pastAcceptedSimilarity', null=True)),
                ('overall_risk_level', models.CharField(db_column='overallRiskLevel', help_text='LOW, MEDIUM, HIGH', max_length=20)),
                ('overall_deviation_score', models.FloatField(db_column='overallDeviationScore')),
                ('risk_type', models.CharField(blank=True, db_column='riskType', max_length=100, null=True)),
                ('suggested_replacement_text', models.TextField(blank=True, db_column='suggestedReplacementText', null=True)),
                ('suggested_from_template_id', models.CharField(blank=True, db_column='suggestedFromTemplateId', max_length=36, null=True)),
                ('explanation', models.TextField(blank=True, help_text='Why this clause deviates', null=True)),
                ('court_precedent', models.TextField(blank=True, db_column='courtPrecedent', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
                ('updated_at', models.DateTimeField(auto_now=True, db_column='updatedAt')),
                ('gold_standard_id', models.CharField(blank=True, db_column='goldStandardId', max_length=36, null=True)),
                ('industry_benchmark_id', models.CharField(blank=True, db_column='industryBenchmarkId', max_length=36, null=True)),
            ],
            options={
                'db_table': 'clause_deviation_scores',
                'unique_together': {('clause_id', 'contract_id')},
            },
        ),
        migrations.AddIndex(
            model_name='clausedeviationscore',
            index=models.Index(fields=['clause_id'], name='clause_devi_clauseI_247023_idx'),
        ),

        # ── GoldStandardTemplate ──────────────────────────────────────────
        migrations.CreateModel(
            name='GoldStandardTemplate',
            fields=[
                ('id', models.CharField(default=core.models.generate_uuid, editable=False, max_length=36, primary_key=True, serialize=False)),
                ('template_name', models.CharField(db_column='templateName', max_length=255)),
                ('clause_category', models.CharField(db_column='clauseCategory', max_length=50)),
                ('approved_clause_text', models.TextField(db_column='approvedClauseText')),
                ('embedding', models.JSONField(default=list)),
                ('embedding_model', models.CharField(db_column='embeddingModel', max_length=100)),
                ('safe_threshold', models.FloatField(db_column='safeThreshold', help_text='Similarity threshold for safe clauses')),
                ('review_threshold', models.FloatField(db_column='reviewThreshold', help_text='Similarity threshold requiring review')),
                ('jurisdiction', models.CharField(blank=True, max_length=100, null=True)),
                ('legal_notes', models.TextField(blank=True, db_column='legalNotes', null=True)),
                ('is_active', models.BooleanField(db_column='isActive', default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
                ('updated_at', models.DateTimeField(auto_now=True, db_column='updatedAt')),
                # 0038 will remove this and add created_by (CharField)
                ('created_by_id', models.CharField(blank=True, db_column='createdBy', max_length=36, null=True)),
            ],
            options={
                'db_table': 'gold_standard_templates',
                'indexes': [
                    models.Index(fields=['clause_category', 'is_active'], name='gold_standa_clauseC_64bd52_idx'),
                    models.Index(fields=['jurisdiction'], name='gold_standa_jurisdi_2831be_idx'),
                ],
            },
        ),

        # ── ExpectedObligation ────────────────────────────────────────────
        migrations.CreateModel(
            name='ExpectedObligation',
            fields=[
                ('id', models.CharField(default=core.models.generate_uuid, editable=False, max_length=36, primary_key=True, serialize=False)),
                ('obligation_name', models.CharField(db_column='obligationName', max_length=255)),
                ('obligation_category', models.CharField(db_column='obligationCategory', max_length=50)),
                ('criticality', models.CharField(db_column='criticality', help_text='CRITICAL, HIGH, MEDIUM, LOW', max_length=20)),
                ('expected_clause_text', models.TextField(db_column='expectedClauseText', help_text='Example text of what we expect to see')),
                ('embedding', models.JSONField(default=list)),
                ('embedding_model', models.CharField(db_column='embeddingModel', max_length=100)),
                ('presence_threshold', models.FloatField(db_column='presenceThreshold', help_text='Similarity threshold to consider obligation present')),
                ('absence_risk_description', models.TextField(db_column='absenceRiskDescription', help_text='What risk occurs if this is missing')),
                ('absence_risk_example', models.TextField(blank=True, db_column='absenceRiskExample', null=True)),
                ('suggested_clause_text', models.TextField(blank=True, db_column='suggestedClauseText', null=True)),
                ('contract_type', models.CharField(blank=True, db_column='contractType', max_length=100, null=True)),
                ('party_protected', models.CharField(blank=True, db_column='partyProtected', max_length=50, null=True)),
                ('jurisdiction', models.CharField(blank=True, max_length=100, null=True)),
                ('is_active', models.BooleanField(db_column='isActive', default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
                ('updated_at', models.DateTimeField(auto_now=True, db_column='updatedAt')),
            ],
            options={
                'db_table': 'expected_obligations',
                'indexes': [
                    models.Index(fields=['obligation_category'], name='expected_ob_obligat_252b79_idx'),
                    models.Index(fields=['criticality'], name='expected_ob_critica_5eed0d_idx'),
                    models.Index(fields=['contract_type'], name='expected_ob_contrac_82c0cc_idx'),
                ],
            },
        ),

        # ── IndustryBenchmark ─────────────────────────────────────────────
        migrations.CreateModel(
            name='IndustryBenchmark',
            fields=[
                ('id', models.CharField(default=core.models.generate_uuid, editable=False, max_length=36, primary_key=True, serialize=False)),
                ('benchmark_name', models.CharField(db_column='benchmarkName', max_length=255)),
                ('clause_category', models.CharField(db_column='clauseCategory', max_length=50)),
                ('industry', models.CharField(blank=True, max_length=100, null=True)),
                ('benchmark_clause_text', models.TextField(db_column='benchmarkClauseText')),
                ('embedding', models.JSONField(default=list)),
                ('embedding_model', models.CharField(db_column='embeddingModel', max_length=100)),
                ('adoption_rate', models.FloatField(db_column='adoptionRate', help_text='How common this clause is (0-1)')),
                ('source', models.CharField(blank=True, help_text='Source of benchmark data', max_length=255, null=True)),
                ('jurisdiction', models.CharField(blank=True, max_length=100, null=True)),
                ('is_active', models.BooleanField(db_column='isActive', default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
                ('updated_at', models.DateTimeField(auto_now=True, db_column='updatedAt')),
            ],
            options={
                'db_table': 'industry_benchmarks',
                'indexes': [
                    models.Index(fields=['clause_category'], name='industry_be_clauseC_62338b_idx'),
                    models.Index(fields=['industry'], name='industry_be_industr_313d87_idx'),
                    models.Index(fields=['jurisdiction'], name='industry_be_jurisdi_e77173_idx'),
                ],
            },
        ),

        # ── MissingSafeguardDetection ─────────────────────────────────────
        migrations.CreateModel(
            name='MissingSafeguardDetection',
            fields=[
                ('id', models.CharField(default=core.models.generate_uuid, editable=False, max_length=36, primary_key=True, serialize=False)),
                ('contract_id', models.CharField(db_column='contractId', max_length=36)),
                ('status', models.CharField(db_column='status', help_text='MISSING, WEAK, PRESENT', max_length=20)),
                ('confidence', models.FloatField(help_text='Confidence in this detection (0-1)')),
                ('matched_clause_id', models.CharField(blank=True, db_column='matchedClauseId', max_length=36, null=True)),
                ('matched_similarity', models.FloatField(blank=True, db_column='matchedSimilarity', null=True)),
                ('ai_insight', models.TextField(db_column='aiInsight', help_text='AI explanation of the detection')),
                ('risk_explanation', models.TextField(db_column='riskExplanation')),
                ('suggested_action', models.TextField(db_column='suggestedAction')),
                ('suggested_clause_text', models.TextField(blank=True, db_column='suggestedClauseText', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
                ('updated_at', models.DateTimeField(auto_now=True, db_column='updatedAt')),
                ('expected_obligation_id', models.CharField(db_column='expectedObligationId', max_length=36)),
            ],
            options={
                'db_table': 'missing_safeguard_detections',
                'unique_together': {('contract_id', 'expected_obligation_id')},
                'indexes': [
                    models.Index(fields=['contract_id'], name='missing_saf_contrac_f5cc72_idx'),
                    models.Index(fields=['status'], name='missing_saf_status_29b27e_idx'),
                    models.Index(fields=['expected_obligation_id'], name='missing_saf_expecte_c7edd4_idx'),
                ],
            },
        ),
    ]
