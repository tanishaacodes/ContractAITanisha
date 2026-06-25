"""
Migration 0002 – Add EngineNegotiationSession, EngineNegotiationMessage,
                     EngineNegotiationOutcome
Generated manually for the AI Studio advanced negotiation engine.
Table names are prefixed with 'engine_' to avoid collisions with the
NegotiationSession / NegotiationMessage tables already owned by core.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("negotiation", "0001_initial"),
    ]

    operations = [
        # ── EngineNegotiationSession ──────────────────────────────────
        migrations.CreateModel(
            name="EngineNegotiationSession",
            fields=[
                ("session_id",               models.CharField(db_column="sessionId",       editable=False, max_length=36, primary_key=True, serialize=False)),
                ("contract_id",              models.CharField(blank=True,                  db_column="contractId",        max_length=36, null=True)),
                ("original_clause",          models.TextField(db_column="originalClause")),
                ("final_clause",             models.TextField(blank=True,                  db_column="finalClause")),
                ("best_clause",              models.TextField(blank=True,                  db_column="bestClause")),
                ("rounds_requested",         models.IntegerField(db_column="roundsRequested", default=3)),
                ("rounds_completed",         models.IntegerField(db_column="roundsCompleted", default=0)),
                ("converged",                models.BooleanField(default=False)),
                ("convergence_round",        models.IntegerField(blank=True,               db_column="convergenceRound",  null=True)),
                ("best_round",               models.IntegerField(db_column="bestRound",    default=1)),
                ("final_score",              models.FloatField(db_column="finalScore",     default=0.0)),
                ("score_trend",              models.CharField(db_column="scoreTrend",      default="stable", max_length=20)),
                ("round_scores",             models.JSONField(db_column="roundScores",     default=list)),
                ("clause_history",           models.JSONField(db_column="clauseHistory",   default=list)),
                ("agent_strategy_weights",   models.JSONField(db_column="agentStrategyWeights", default=dict)),
                ("reasoning",                models.TextField(blank=True)),
                ("created_at",               models.DateTimeField(auto_now_add=True,       db_column="createdAt")),
                ("updated_at",               models.DateTimeField(auto_now=True,           db_column="updatedAt")),
            ],
            options={
                "db_table":  "engine_negotiation_sessions",
                "ordering":  ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="enginenegotiationsession",
            index=models.Index(fields=["contract_id"], name="eng_sess_contract_idx"),
        ),
        migrations.AddIndex(
            model_name="enginenegotiationsession",
            index=models.Index(fields=["created_at"], name="eng_sess_created_idx"),
        ),
        migrations.AddIndex(
            model_name="enginenegotiationsession",
            index=models.Index(fields=["final_score"], name="eng_sess_score_idx"),
        ),

        # ── EngineNegotiationMessage ──────────────────────────────────
        migrations.CreateModel(
            name="EngineNegotiationMessage",
            fields=[
                ("message_id",       models.CharField(db_column="messageId",   editable=False, max_length=36, primary_key=True, serialize=False)),
                ("session",          models.ForeignKey(db_column="sessionId",  on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="negotiation.enginenegotiationsession")),
                ("round_number",     models.IntegerField(db_column="roundNumber")),
                ("agent_name",       models.CharField(db_column="agentName",   max_length=50)),
                ("agent_color",      models.CharField(db_column="agentColor",  max_length=30)),
                ("proposed_clause",  models.TextField(db_column="proposedClause")),
                ("justification",    models.TextField(blank=True)),
                ("risk_impact",      models.FloatField(db_column="riskImpact", default=0.30)),
                ("financial_impact", models.FloatField(db_column="financialImpact", default=0.00)),
                ("compliance_score", models.FloatField(db_column="complianceScore", default=0.60)),
                ("round_score",      models.FloatField(db_column="roundScore", default=0.00)),
                ("timestamp",        models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "engine_negotiation_messages",
                "ordering": ["round_number", "agent_name"],
            },
        ),
        migrations.AddIndex(
            model_name="enginenegotiationmessage",
            index=models.Index(fields=["session", "round_number"], name="eng_msg_sess_round_idx"),
        ),
        migrations.AddIndex(
            model_name="enginenegotiationmessage",
            index=models.Index(fields=["agent_name"], name="eng_msg_agent_idx"),
        ),

        # ── EngineNegotiationOutcome ──────────────────────────────────
        migrations.CreateModel(
            name="EngineNegotiationOutcome",
            fields=[
                ("id",                        models.AutoField(primary_key=True, serialize=False)),
                ("session",                   models.OneToOneField(db_column="sessionId", on_delete=django.db.models.deletion.CASCADE, related_name="outcome", to="negotiation.enginenegotiationsession")),
                ("deal_outcome",              models.CharField(choices=[("SUCCESS", "Success"), ("FAILURE", "Failure"), ("PARTIAL", "Partial Success"), ("ONGOING", "Ongoing")], db_column="dealOutcome", default="ONGOING", max_length=20)),
                ("profit_margin",             models.FloatField(db_column="profitMargin",  default=0.0)),
                ("delay_days",                models.IntegerField(db_column="delayDays",   default=0)),
                ("dispute_count",             models.IntegerField(db_column="disputeCount", default=0)),
                ("updated_strategy_weights",  models.JSONField(db_column="updatedStrategyWeights", default=dict)),
                ("rl_feedback_processed",     models.BooleanField(db_column="rlFeedbackProcessed", default=False)),
                ("evaluated_at",              models.DateTimeField(auto_now_add=True,       db_column="evaluatedAt")),
            ],
            options={
                "db_table": "engine_negotiation_outcomes",
                "ordering": ["-evaluated_at"],
            },
        ),
        migrations.AddIndex(
            model_name="enginenegotiationoutcome",
            index=models.Index(fields=["deal_outcome"], name="eng_outcome_deal_idx"),
        ),
        migrations.AddIndex(
            model_name="enginenegotiationoutcome",
            index=models.Index(fields=["evaluated_at"], name="eng_outcome_eval_idx"),
        ),
    ]
