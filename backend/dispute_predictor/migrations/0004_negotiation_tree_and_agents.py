# Generated migration for negotiation tree and multi-agent system

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dispute_predictor', '0002_add_contract_text'),
    ]

    operations = [
        # Negotiation States table (for MCTS tree)
        migrations.CreateModel(
            name='NegotiationState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('contract_id', models.IntegerField(db_index=True)),
                ('parent_state_id', models.IntegerField(null=True, blank=True, db_index=True)),
                ('level', models.IntegerField(default=0)),
                ('state_data', models.JSONField(help_text='Contract parameters: price, delivery_days, liability_cap, etc.')),
                ('score', models.FloatField(default=0.0)),
                ('dispute_probability', models.FloatField(default=0.0)),
                ('commercial_value', models.FloatField(default=0.0)),
                ('visits', models.IntegerField(default=0)),
                ('is_optimal', models.BooleanField(default=False)),
                ('action_taken', models.CharField(max_length=255, null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'negotiation_states',
                'indexes': [
                    models.Index(fields=['contract_id', 'level'], name='neg_state_contract_level_idx'),
                    models.Index(fields=['parent_state_id'], name='neg_state_parent_idx'),
                ],
            },
        ),

        # Agent Decisions table
        migrations.CreateModel(
            name='AgentDecision',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('simulation_id', models.IntegerField(db_index=True)),
                ('agent_type', models.CharField(max_length=50, choices=[
                    ('buyer', 'Buyer Agent'),
                    ('supplier', 'Supplier Agent'),
                    ('regulator', 'Regulator Agent'),
                    ('risk', 'Risk Agent'),
                    ('finance', 'Finance Agent'),
                ])),
                ('action', models.CharField(max_length=255)),
                ('clause_affected', models.CharField(max_length=100)),
                ('value_change', models.JSONField(help_text='Before/after values')),
                ('rationale', models.TextField(null=True, blank=True)),
                ('approved', models.BooleanField(default=True)),
                ('impact', models.JSONField(null=True, blank=True, help_text='Impact metrics: dispute_change, cost_change')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'agent_decisions',
                'indexes': [
                    models.Index(fields=['simulation_id', 'agent_type'], name='agent_dec_sim_type_idx'),
                ],
            },
        ),

        # Contract Events table (for Digital Twin)
        migrations.CreateModel(
            name='ContractEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('contract_id', models.IntegerField(db_index=True)),
                ('event_type', models.CharField(max_length=100, choices=[
                    ('signed', 'Contract Signed'),
                    ('supplier_delay', 'Supplier Delay'),
                    ('cost_escalation', 'Cost Escalation'),
                    ('scope_change', 'Scope Change'),
                    ('renegotiation', 'Renegotiation'),
                    ('dispute_triggered', 'Dispute Triggered'),
                    ('arbitration', 'Arbitration Initiated'),
                    ('settlement', 'Settlement Reached'),
                ])),
                ('event_time', models.DateTimeField()),
                ('impact_data', models.JSONField(null=True, blank=True)),
                ('risk_change', models.FloatField(default=0.0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'contract_events',
                'ordering': ['event_time'],
                'indexes': [
                    models.Index(fields=['contract_id', 'event_time'], name='contract_event_time_idx'),
                ],
            },
        ),

        # Legal Precedents table
        migrations.CreateModel(
            name='LegalPrecedent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('case_id', models.CharField(max_length=100, unique=True)),
                ('case_name', models.CharField(max_length=255)),
                ('jurisdiction', models.CharField(max_length=100)),
                ('arbitration_seat', models.CharField(max_length=100, null=True, blank=True)),
                ('tribunal_composition', models.CharField(max_length=255, null=True, blank=True)),
                ('dispute_type', models.CharField(max_length=100)),
                ('contract_type', models.CharField(max_length=100)),
                ('contract_value', models.FloatField(null=True, blank=True)),
                ('claim_amount', models.FloatField(null=True, blank=True)),
                ('award_amount', models.FloatField(null=True, blank=True)),
                ('outcome', models.CharField(max_length=50, choices=[
                    ('claimant_win', 'Claimant Win'),
                    ('respondent_win', 'Respondent Win'),
                    ('partial_award', 'Partial Award'),
                    ('settlement', 'Settlement'),
                    ('dismissed', 'Dismissed'),
                ])),
                ('decision_date', models.DateField()),
                ('duration_days', models.IntegerField(null=True, blank=True)),
                ('legal_costs', models.FloatField(null=True, blank=True)),
                ('key_issues', models.JSONField(null=True, blank=True)),
                ('clause_embeddings', models.JSONField(null=True, blank=True, help_text='768-dim LegalBERT embeddings')),
                ('summary', models.TextField(null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'legal_precedents',
                'indexes': [
                    models.Index(fields=['jurisdiction', 'dispute_type'], name='legal_prec_juris_type_idx'),
                    models.Index(fields=['contract_type', 'outcome'], name='legal_prec_ctype_outcome_idx'),
                ],
            },
        ),

        # RL Training Logs table
        migrations.CreateModel(
            name='RLTrainingLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('episode', models.IntegerField()),
                ('state', models.JSONField()),
                ('action', models.JSONField()),
                ('reward', models.FloatField()),
                ('next_state', models.JSONField()),
                ('done', models.BooleanField(default=False)),
                ('loss', models.FloatField(null=True, blank=True)),
                ('epsilon', models.FloatField(null=True, blank=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'rl_training_logs',
                'indexes': [
                    models.Index(fields=['episode'], name='rl_log_episode_idx'),
                ],
            },
        ),
    ]
