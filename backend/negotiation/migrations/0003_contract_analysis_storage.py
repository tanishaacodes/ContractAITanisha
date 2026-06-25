"""
Migration 0003 – Add ContractAnalysisResult, AnalysisClause,
                     AnalysisClauseRisk, AnalysisNegotiationResult

These tables are the persistent output store for the Contract Intelligence
Orchestrator pipeline.  Every other module reads from here instead of
re-running the pipeline.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("negotiation", "0002_negotiation_engine_models"),
        ("core", "0001_initial"),          # ContractAnalysisResult has optional FK to core.Contract
    ]

    operations = [

        # ── ContractAnalysisResult ────────────────────────────────────────────
        migrations.CreateModel(
            name="ContractAnalysisResult",
            fields=[
                ("id",               models.CharField(db_column="id",              editable=False, max_length=36, primary_key=True, serialize=False)),
                ("analysis_id",      models.CharField(db_column="analysisId",      max_length=36,  unique=True)),
                ("contract",         models.ForeignKey(blank=True,                 db_column="contractId", null=True,
                                                       on_delete=django.db.models.deletion.SET_NULL,
                                                       related_name="orchestrator_analyses",
                                                       to="core.contract",
                                                       db_constraint=False)),
                ("contract_id_ref",  models.CharField(blank=True,                  db_column="contractIdRef", max_length=36, null=True)),
                ("jurisdiction",     models.CharField(default="india",             max_length=10)),
                ("contract_value",   models.FloatField(db_column="contractValue",  default=0)),
                ("duration_months",  models.IntegerField(db_column="durationMonths", default=12)),
                ("final_score",      models.FloatField(db_column="finalScore",     default=0)),
                ("decision",         models.CharField(default="RENEGOTIATE",       max_length=20)),
                ("score_breakdown",  models.JSONField(db_column="scoreBreakdown",  default=dict)),
                ("risk_summary",     models.JSONField(db_column="riskSummary",     default=dict)),
                ("cfo_result",       models.JSONField(db_column="cfoResult",       default=dict)),
                ("recommendations",  models.JSONField(default=list)),
                ("pipeline_trace",   models.JSONField(db_column="pipelineTrace",   default=list)),
                ("total_duration_ms", models.FloatField(db_column="totalDurationMs", default=0)),
                ("input_source",     models.CharField(db_column="inputSource",     default="raw_text", max_length=20)),
                ("status",           models.CharField(default="complete",          max_length=20)),
                ("created_at",       models.DateTimeField(auto_now_add=True,       db_column="createdAt")),
            ],
            options={
                "db_table": "contract_analysis_results",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="contractanalysisresult",
            index=models.Index(fields=["contract_id_ref"], name="idx_car_contract_ref"),
        ),
        migrations.AddIndex(
            model_name="contractanalysisresult",
            index=models.Index(fields=["decision"], name="idx_car_decision"),
        ),
        migrations.AddIndex(
            model_name="contractanalysisresult",
            index=models.Index(fields=["created_at"], name="idx_car_created"),
        ),

        # ── AnalysisClause ────────────────────────────────────────────────────
        migrations.CreateModel(
            name="AnalysisClause",
            fields=[
                ("id",             models.CharField(db_column="id",          editable=False, max_length=36, primary_key=True, serialize=False)),
                ("analysis",       models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                                     related_name="stored_clauses",
                                                     to="negotiation.contractanalysisresult")),
                ("clause_ref_id",  models.CharField(db_column="clauseRefId", max_length=100)),
                ("title",          models.CharField(max_length=500)),
                ("text",           models.TextField()),
                ("clause_type",    models.CharField(db_column="clauseType",  default="general", max_length=100)),
            ],
            options={"db_table": "analysis_clauses"},
        ),
        migrations.AddIndex(
            model_name="analysisclause",
            index=models.Index(fields=["analysis"], name="idx_ac_analysis"),
        ),

        # ── AnalysisClauseRisk ────────────────────────────────────────────────
        migrations.CreateModel(
            name="AnalysisClauseRisk",
            fields=[
                ("id",                models.CharField(db_column="id",              editable=False, max_length=36, primary_key=True, serialize=False)),
                ("analysis",          models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                                        related_name="stored_clause_risks",
                                                        to="negotiation.contractanalysisresult")),
                ("clause",            models.ForeignKey(blank=True, null=True,
                                                        on_delete=django.db.models.deletion.SET_NULL,
                                                        related_name="risks",
                                                        to="negotiation.analysisclause")),
                ("clause_ref_id",     models.CharField(db_column="clauseRefId",     max_length=100)),
                ("clause_title",      models.CharField(db_column="clauseTitle",     max_length=500)),
                ("risk_level",        models.CharField(db_column="riskLevel",       max_length=20)),
                ("compliance_status", models.CharField(blank=True,                  db_column="complianceStatus", max_length=100)),
                ("confidence_score",  models.FloatField(db_column="confidenceScore", default=0.5)),
                ("issues",            models.JSONField(default=list)),
                ("explanation",       models.TextField(blank=True)),
                ("suggested_clause",  models.TextField(blank=True,                  db_column="suggestedClause")),
                ("rule_flags",        models.JSONField(db_column="ruleFlags",       default=list)),
            ],
            options={"db_table": "analysis_clause_risks"},
        ),
        migrations.AddIndex(
            model_name="analysisclauserisk",
            index=models.Index(fields=["analysis", "risk_level"], name="idx_acr_analysis_risk"),
        ),

        # ── AnalysisNegotiationResult ─────────────────────────────────────────
        migrations.CreateModel(
            name="AnalysisNegotiationResult",
            fields=[
                ("id",               models.CharField(db_column="id",              editable=False, max_length=36, primary_key=True, serialize=False)),
                ("analysis",         models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                                       related_name="stored_negotiation_results",
                                                       to="negotiation.contractanalysisresult")),
                ("clause_ref_id",    models.CharField(db_column="clauseRefId",     max_length=100)),
                ("clause_title",     models.CharField(db_column="clauseTitle",     max_length=500)),
                ("original_risk",    models.CharField(db_column="originalRisk",    max_length=20)),
                ("final_clause",     models.TextField(blank=True,                  db_column="finalClause")),
                ("best_clause",      models.TextField(blank=True,                  db_column="bestClause")),
                ("final_score",      models.FloatField(db_column="finalScore",     default=0)),
                ("converged",        models.BooleanField(default=False)),
                ("rounds_completed", models.IntegerField(db_column="roundsCompleted", default=0)),
                ("score_trend",      models.CharField(blank=True,                  db_column="scoreTrend", max_length=50)),
            ],
            options={"db_table": "analysis_negotiation_results"},
        ),
        migrations.AddIndex(
            model_name="analysisnegotiationresult",
            index=models.Index(fields=["analysis"], name="idx_anr_analysis"),
        ),
    ]
