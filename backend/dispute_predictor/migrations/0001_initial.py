from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='DisputePrediction',
            fields=[
                ('id', models.CharField(db_column='id', default=None, max_length=36, primary_key=True, serialize=False)),
                ('contract_id', models.CharField(db_column='contractId', db_index=True, max_length=36)),
                ('contract_title', models.CharField(blank=True, db_column='contractTitle', max_length=512)),
                ('dispute_probability', models.FloatField(db_column='disputeProbability', default=0.0)),
                ('arbitration_probability', models.FloatField(db_column='arbitrationProbability', default=0.0)),
                ('litigation_probability', models.FloatField(db_column='litigationProbability', default=0.0)),
                ('settlement_probability', models.FloatField(db_column='settlementProbability', default=0.0)),
                ('predicted_cost_usd', models.FloatField(db_column='predictedCostUsd', default=0.0)),
                ('legal_cost_exposure_usd', models.FloatField(db_column='legalCostExposureUsd', default=0.0)),
                ('contract_risk_score', models.FloatField(db_column='contractRiskScore', default=0.0)),
                ('financial_stress_score', models.FloatField(db_column='financialStressScore', default=0.0)),
                ('operational_risk_score', models.FloatField(db_column='operationalRiskScore', default=0.0)),
                ('geopolitical_risk_score', models.FloatField(db_column='geopoliticalRiskScore', default=0.0)),
                ('bayesian_risk_nodes', models.JSONField(db_column='bayesianRiskNodes', default=dict)),
                ('risk_propagation_path', models.JSONField(db_column='riskPropagationPath', default=list)),
                ('top_risk_drivers', models.JSONField(db_column='topRiskDrivers', default=list)),
                ('gnn_dispute_score', models.FloatField(blank=True, db_column='gnnDisputeScore', null=True)),
                ('gnn_confidence', models.FloatField(blank=True, db_column='gnnConfidence', null=True)),
                ('explanation', models.TextField(blank=True, db_column='explanation')),
                ('mitigation_recommendations', models.JSONField(db_column='mitigationRecommendations', default=list)),
                ('input_signals', models.JSONField(db_column='inputSignals', default=dict)),
                ('prediction_model_version', models.CharField(db_column='predictionModelVersion', default='v1.0', max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
                ('updated_at', models.DateTimeField(auto_now=True, db_column='updatedAt')),
            ],
            options={
                'db_table': 'dispute_predictions',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='DisputeScenario',
            fields=[
                ('id', models.CharField(db_column='id', default=None, max_length=36, primary_key=True, serialize=False)),
                ('prediction_id', models.CharField(db_column='predictionId', db_index=True, max_length=36)),
                ('contract_id', models.CharField(db_column='contractId', db_index=True, max_length=36)),
                ('scenario_name', models.CharField(db_column='scenarioName', max_length=255)),
                ('scenario_description', models.TextField(blank=True, db_column='scenarioDescription')),
                ('risk_overrides', models.JSONField(db_column='riskOverrides', default=dict)),
                ('dispute_probability', models.FloatField(db_column='disputeProbability', default=0.0)),
                ('arbitration_probability', models.FloatField(db_column='arbitrationProbability', default=0.0)),
                ('predicted_cost_usd', models.FloatField(db_column='predictedCostUsd', default=0.0)),
                ('contract_risk_score', models.FloatField(db_column='contractRiskScore', default=0.0)),
                ('dispute_probability_delta', models.FloatField(db_column='disputeProbabilityDelta', default=0.0)),
                ('cost_delta', models.FloatField(db_column='costDelta', default=0.0)),
                ('risk_nodes_snapshot', models.JSONField(db_column='riskNodesSnapshot', default=dict)),
                ('propagation_path', models.JSONField(db_column='propagationPath', default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
            ],
            options={
                'db_table': 'dispute_scenarios',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='DisputeRiskNode',
            fields=[
                ('id', models.CharField(db_column='id', default=None, max_length=36, primary_key=True, serialize=False)),
                ('node_id', models.CharField(db_column='nodeId', max_length=100, unique=True)),
                ('label', models.CharField(db_column='label', max_length=255)),
                ('cluster', models.CharField(db_column='cluster', max_length=100)),
                ('layer', models.IntegerField(db_column='layer', default=1)),
                ('base_probability', models.FloatField(db_column='baseProbability', default=0.1)),
                ('description', models.TextField(blank=True, db_column='description')),
            ],
            options={
                'db_table': 'dispute_risk_nodes',
            },
        ),
        migrations.CreateModel(
            name='DisputeRiskEdge',
            fields=[
                ('id', models.CharField(db_column='id', default=None, max_length=36, primary_key=True, serialize=False)),
                ('source_node_id', models.CharField(db_column='sourceNodeId', max_length=100)),
                ('target_node_id', models.CharField(db_column='targetNodeId', max_length=100)),
                ('conditional_probability', models.FloatField(db_column='conditionalProbability', default=0.5)),
                ('relation_type', models.CharField(blank=True, db_column='relationType', max_length=100)),
            ],
            options={
                'db_table': 'dispute_risk_edges',
            },
        ),
        migrations.AlterUniqueTogether(
            name='disputeriskedge',
            unique_together={('source_node_id', 'target_node_id')},
        ),
    ]
