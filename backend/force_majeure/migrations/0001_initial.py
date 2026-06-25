"""
Force Majeure Intelligence Engine — Initial Migration
Creates tables: fm_prediction, fm_clause_audit, fm_scenario, fm_war_risk, fm_global_alert
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        # --- fm_prediction ---
        migrations.CreateModel(
            name='FMPrediction',
            fields=[
                ('id', models.CharField(db_column='id', default=None, max_length=36, primary_key=True, serialize=False)),
                ('contract_id', models.CharField(db_column='contractId', db_index=True, max_length=36)),
                ('contract_title', models.CharField(blank=True, db_column='contractTitle', max_length=512)),
                ('contract_text', models.TextField(blank=True, db_column='contractText')),
                ('fm_risk_score', models.FloatField(db_column='fmRiskScore', default=0.0)),
                ('fm_invocation_probability', models.FloatField(db_column='fmInvocationProbability', default=0.0)),
                ('project_delay_probability', models.FloatField(db_column='projectDelayProbability', default=0.0)),
                ('cost_overrun_probability', models.FloatField(db_column='costOverrunProbability', default=0.0)),
                ('contract_suspension_probability', models.FloatField(db_column='contractSuspensionProbability', default=0.0)),
                ('contract_termination_probability', models.FloatField(db_column='contractTerminationProbability', default=0.0)),
                ('event_probabilities', models.JSONField(db_column='eventProbabilities', default=dict)),
                ('expected_loss_usd', models.FloatField(db_column='expectedLossUsd', default=0.0)),
                ('worst_case_loss_usd', models.FloatField(db_column='worstCaseLossUsd', default=0.0)),
                ('p50_loss_usd', models.FloatField(db_column='p50LossUsd', default=0.0)),
                ('p95_loss_usd', models.FloatField(db_column='p95LossUsd', default=0.0)),
                ('p99_loss_usd', models.FloatField(db_column='p99LossUsd', default=0.0)),
                ('bayesian_nodes', models.JSONField(db_column='bayesianNodes', default=dict)),
                ('top_risk_drivers', models.JSONField(db_column='topRiskDrivers', default=list)),
                ('causal_chain', models.JSONField(db_column='causalChain', default=list)),
                ('clause_strength_score', models.FloatField(db_column='clauseStrengthScore', default=0.0)),
                ('missing_protections', models.JSONField(db_column='missingProtections', default=list)),
                ('covered_events', models.JSONField(db_column='coveredEvents', default=list)),
                ('explanation', models.TextField(blank=True, db_column='explanation')),
                ('mitigation_suggestions', models.JSONField(db_column='mitigationSuggestions', default=list)),
                ('contract_value', models.FloatField(db_column='contractValue', default=0.0)),
                ('jurisdiction', models.CharField(blank=True, db_column='jurisdiction', max_length=128)),
                ('industry', models.CharField(blank=True, db_column='industry', max_length=128)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
                ('updated_at', models.DateTimeField(auto_now=True, db_column='updatedAt')),
            ],
            options={'db_table': 'fm_prediction', 'ordering': ['-created_at']},
        ),

        # --- fm_clause_audit ---
        migrations.CreateModel(
            name='FMClauseAudit',
            fields=[
                ('id', models.CharField(db_column='id', default=None, max_length=36, primary_key=True, serialize=False)),
                ('contract_id', models.CharField(db_column='contractId', db_index=True, max_length=36)),
                ('contract_title', models.CharField(blank=True, db_column='contractTitle', max_length=512)),
                ('raw_clause_text', models.TextField(blank=True, db_column='rawClauseText')),
                ('status', models.CharField(
                    choices=[('strong', 'Strong Clause'), ('weak', 'Weak Clause'), ('missing', 'Missing Clause')],
                    db_column='status', default='missing', max_length=16,
                )),
                ('strength_score', models.FloatField(db_column='strengthScore', default=0.0)),
                ('covered_events', models.JSONField(db_column='coveredEvents', default=list)),
                ('missing_events', models.JSONField(db_column='missingEvents', default=list)),
                ('weak_events', models.JSONField(db_column='weakEvents', default=list)),
                ('original_clause', models.TextField(blank=True, db_column='originalClause')),
                ('corrected_clause', models.TextField(blank=True, db_column='correctedClause')),
                ('correction_applied', models.BooleanField(db_column='correctionApplied', default=False)),
                ('risk_reduction_before', models.FloatField(db_column='riskReductionBefore', default=0.0)),
                ('risk_reduction_after', models.FloatField(db_column='riskReductionAfter', default=0.0)),
                ('benchmark_fidic_score', models.FloatField(blank=True, db_column='benchmarkFidicScore', null=True)),
                ('benchmark_nec_score', models.FloatField(blank=True, db_column='benchmarkNecScore', null=True)),
                ('benchmark_icc_score', models.FloatField(blank=True, db_column='benchmarkIccScore', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
                ('updated_at', models.DateTimeField(auto_now=True, db_column='updatedAt')),
            ],
            options={'db_table': 'fm_clause_audit', 'ordering': ['-created_at']},
        ),

        # --- fm_scenario ---
        migrations.CreateModel(
            name='FMScenario',
            fields=[
                ('id', models.CharField(db_column='id', default=None, max_length=36, primary_key=True, serialize=False)),
                ('contract_id', models.CharField(blank=True, db_column='contractId', db_index=True, max_length=36)),
                ('prediction_id', models.CharField(blank=True, db_column='predictionId', max_length=36)),
                ('name', models.CharField(db_column='name', max_length=256)),
                ('scenario_type', models.CharField(
                    choices=[
                        ('war', 'War / Military Conflict'),
                        ('pandemic', 'Pandemic / Epidemic'),
                        ('natural_disaster', 'Natural Disaster'),
                        ('supply_chain', 'Supply Chain Disruption'),
                        ('sanctions', 'Trade Sanctions / Embargo'),
                        ('cyber', 'Cyber Warfare'),
                        ('energy_crisis', 'Energy Crisis'),
                        ('political_coup', 'Political Coup'),
                        ('custom', 'Custom Scenario'),
                    ],
                    db_column='scenarioType', default='custom', max_length=32,
                )),
                ('description', models.TextField(blank=True, db_column='description')),
                ('input_params', models.JSONField(db_column='inputParams', default=dict)),
                ('iterations', models.IntegerField(db_column='iterations', default=5000)),
                ('expected_loss_usd', models.FloatField(db_column='expectedLossUsd', default=0.0)),
                ('p50_loss_usd', models.FloatField(db_column='p50LossUsd', default=0.0)),
                ('p95_loss_usd', models.FloatField(db_column='p95LossUsd', default=0.0)),
                ('p99_loss_usd', models.FloatField(db_column='p99LossUsd', default=0.0)),
                ('worst_case_loss_usd', models.FloatField(db_column='worstCaseLossUsd', default=0.0)),
                ('delay_days_expected', models.FloatField(db_column='delayDaysExpected', default=0.0)),
                ('delay_days_worst', models.FloatField(db_column='delayDaysWorstCase', default=0.0)),
                ('fm_invocation_prob', models.FloatField(db_column='fmInvocationProb', default=0.0)),
                ('project_delay_prob', models.FloatField(db_column='projectDelayProb', default=0.0)),
                ('contract_termination_prob', models.FloatField(db_column='contractTerminationProb', default=0.0)),
                ('loss_breakdown', models.JSONField(db_column='lossBreakdown', default=dict)),
                ('explanation', models.TextField(blank=True, db_column='explanation')),
                ('recommended_mitigations', models.JSONField(db_column='recommendedMitigations', default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
            ],
            options={'db_table': 'fm_scenario', 'ordering': ['-created_at']},
        ),

        # --- fm_war_risk ---
        migrations.CreateModel(
            name='FMWarRisk',
            fields=[
                ('id', models.CharField(db_column='id', default=None, max_length=36, primary_key=True, serialize=False)),
                ('contract_id', models.CharField(db_column='contractId', db_index=True, max_length=36)),
                ('contract_title', models.CharField(blank=True, db_column='contractTitle', max_length=512)),
                ('war_risk_score', models.FloatField(db_column='warRiskScore', default=0.0)),
                ('event_risks', models.JSONField(db_column='eventRisks', default=dict)),
                ('supply_chain_routes', models.JSONField(db_column='supplyChainRoutes', default=list)),
                ('disrupted_routes', models.JSONField(db_column='disruptedRoutes', default=list)),
                ('war_loss_expected_usd', models.FloatField(db_column='warLossExpectedUsd', default=0.0)),
                ('war_loss_worst_usd', models.FloatField(db_column='warLossWorstUsd', default=0.0)),
                ('top_threats', models.JSONField(db_column='topThreats', default=list)),
                ('project_location', models.CharField(blank=True, db_column='projectLocation', max_length=256)),
                ('supplier_locations', models.JSONField(db_column='supplierLocations', default=list)),
                ('shipping_routes', models.JSONField(db_column='shippingRoutes', default=list)),
                ('war_mitigation_clauses', models.JSONField(db_column='warMitigationClauses', default=list)),
                ('explanation', models.TextField(blank=True, db_column='explanation')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
                ('updated_at', models.DateTimeField(auto_now=True, db_column='updatedAt')),
            ],
            options={'db_table': 'fm_war_risk', 'ordering': ['-created_at']},
        ),

        # --- fm_global_alert ---
        migrations.CreateModel(
            name='FMGlobalAlert',
            fields=[
                ('id', models.CharField(db_column='id', default=None, max_length=36, primary_key=True, serialize=False)),
                ('event_type', models.CharField(
                    choices=[
                        ('war', 'War / Military Conflict'),
                        ('sanctions', 'Trade Sanctions'),
                        ('pandemic', 'Pandemic'),
                        ('earthquake', 'Earthquake'),
                        ('flood', 'Flood'),
                        ('hurricane', 'Hurricane'),
                        ('port_closure', 'Port Closure'),
                        ('airspace_closure', 'Airspace Closure'),
                        ('energy_shortage', 'Energy Shortage'),
                        ('cyber_attack', 'Cyber Attack'),
                        ('political_coup', 'Political Coup'),
                        ('supply_disruption', 'Supply Chain Disruption'),
                    ],
                    db_column='eventType', max_length=32,
                )),
                ('event_title', models.CharField(db_column='eventTitle', max_length=512)),
                ('event_description', models.TextField(blank=True, db_column='eventDescription')),
                ('event_location', models.CharField(blank=True, db_column='eventLocation', max_length=256)),
                ('severity', models.CharField(
                    choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')],
                    db_column='severity', default='medium', max_length=16,
                )),
                ('affected_contract_ids', models.JSONField(db_column='affectedContractIds', default=list)),
                ('affected_contracts_count', models.IntegerField(db_column='affectedContractsCount', default=0)),
                ('total_portfolio_exposure_usd', models.FloatField(db_column='totalPortfolioExposureUsd', default=0.0)),
                ('suggested_actions', models.JSONField(db_column='suggestedActions', default=list)),
                ('clause_updates_required', models.IntegerField(db_column='clauseUpdatesRequired', default=0)),
                ('is_active', models.BooleanField(db_column='isActive', default=True)),
                ('is_resolved', models.BooleanField(db_column='isResolved', default=False)),
                ('detected_at', models.DateTimeField(auto_now_add=True, db_column='detectedAt')),
                ('resolved_at', models.DateTimeField(blank=True, db_column='resolvedAt', null=True)),
            ],
            options={'db_table': 'fm_global_alert', 'ordering': ['-detected_at']},
        ),
    ]
