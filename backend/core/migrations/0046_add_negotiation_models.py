# Generated migration for Feature 3: Live Clause Co-Pilot (Negotiation Mode)

from django.db import migrations, models
import django.db.models.deletion
import core.models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0045_add_self_healing_clause_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='NegotiationSession',
            fields=[
                ('id', models.CharField(default=core.models.generate_uuid, editable=False, max_length=36, primary_key=True, serialize=False)),
                ('session_name', models.CharField(db_column='sessionName', help_text='Descriptive name for this negotiation', max_length=255)),
                ('status', models.CharField(choices=[('ACTIVE', 'Active'), ('PAUSED', 'Paused'), ('COMPLETED', 'Completed'), ('CANCELLED', 'Cancelled')], default='ACTIVE', help_text='Current session status', max_length=20)),
                ('our_party_role', models.CharField(choices=[('BUYER', 'Buyer'), ('SELLER', 'Seller'), ('SERVICE_PROVIDER', 'Service Provider'), ('CLIENT', 'Client'), ('OTHER', 'Other')], db_column='ourPartyRole', help_text='Our role in this negotiation (buyer, seller, etc.)', max_length=50)),
                ('counterparty_name', models.CharField(blank=True, db_column='counterpartyName', help_text='Name of the other party', max_length=255, null=True)),
                ('enable_suggestions', models.BooleanField(db_column='enableSuggestions', default=True, help_text='Enable AI clause suggestions')),
                ('risk_tolerance', models.CharField(choices=[('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High')], db_column='riskTolerance', default='MEDIUM', help_text='Risk tolerance for suggestions', max_length=20)),
                ('objectives', models.JSONField(default=list, help_text='List of negotiation objectives (e.g., ["Reduce liability cap", "Add termination rights"])')),
                ('must_have_clauses', models.JSONField(db_column='mustHaveClauses', default=list, help_text='Clause IDs that are non-negotiable')),
                ('nice_to_have_clauses', models.JSONField(db_column='niceToHaveClauses', default=list, help_text='Clause IDs that are preferred but negotiable')),
                ('started_at', models.DateTimeField(auto_now_add=True, db_column='startedAt')),
                ('completed_at', models.DateTimeField(blank=True, db_column='completedAt', null=True)),
                ('last_activity_at', models.DateTimeField(auto_now=True, db_column='lastActivityAt')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
                ('updated_at', models.DateTimeField(auto_now=True, db_column='updatedAt')),
                ('contract', models.ForeignKey(db_column='contractId', db_constraint=False, help_text='Contract being negotiated', on_delete=django.db.models.deletion.CASCADE, related_name='negotiation_sessions', to='core.contract')),
                ('created_by', models.ForeignKey(db_constraint=False, db_column='createdBy', help_text='User who started the negotiation', on_delete=django.db.models.deletion.PROTECT, related_name='created_negotiations', to='core.user')),
            ],
            options={
                'db_table': 'negotiation_sessions',
                'ordering': ['-last_activity_at'],
            },
        ),
        migrations.CreateModel(
            name='NegotiationMessage',
            fields=[
                ('id', models.CharField(default=core.models.generate_uuid, editable=False, max_length=36, primary_key=True, serialize=False)),
                ('message_type', models.CharField(choices=[('USER', 'User Message'), ('AI', 'AI Co-Pilot'), ('SYSTEM', 'System Notification'), ('SUGGESTION', 'Clause Suggestion')], db_column='messageType', help_text='Type of message', max_length=20)),
                ('content', models.TextField(help_text='Message content')),
                ('ai_confidence', models.FloatField(blank=True, db_column='aiConfidence', help_text='AI confidence in suggestion (0-1)', null=True)),
                ('reasoning', models.TextField(blank=True, help_text='AI reasoning behind suggestion', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
                ('related_clause', models.ForeignKey(db_constraint=False, blank=True, db_column='relatedClauseId', help_text='Clause being discussed', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='negotiation_messages', to='core.clause')),
                ('sender', models.ForeignKey(db_constraint=False, blank=True, db_column='senderId', help_text='User who sent the message (null for AI/system)', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='negotiation_messages', to='core.user')),
                ('session', models.ForeignKey(db_constraint=False, db_column='sessionId', on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='core.negotiationsession')),
            ],
            options={
                'db_table': 'negotiation_messages',
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='NegotiationClauseSuggestion',
            fields=[
                ('id', models.CharField(default=core.models.generate_uuid, editable=False, max_length=36, primary_key=True, serialize=False)),
                ('suggestion_type', models.CharField(choices=[('ALTERNATIVE', 'Alternative Language'), ('STRENGTHEN', 'Strengthen Position'), ('COMPROMISE', 'Compromise Option'), ('FALLBACK', 'Fallback Position'), ('PRECEDENT', 'Based on Precedent')], db_column='suggestionType', max_length=20)),
                ('status', models.CharField(choices=[('PENDING', 'Pending Review'), ('ACCEPTED', 'Accepted'), ('REJECTED', 'Rejected'), ('MODIFIED', 'Modified and Accepted')], default='PENDING', max_length=20)),
                ('original_text', models.TextField(db_column='originalText')),
                ('suggested_text', models.TextField(db_column='suggestedText')),
                ('risk_impact', models.CharField(choices=[('REDUCES_RISK', 'Reduces Risk'), ('NEUTRAL', 'Neutral'), ('INCREASES_RISK', 'Increases Risk')], db_column='riskImpact', help_text='Expected risk impact', max_length=20)),
                ('risk_score_delta', models.FloatField(db_column='riskScoreDelta', help_text='Change in risk score (-1 to +1)')),
                ('rationale', models.TextField(help_text='AI explanation of the suggestion')),
                ('similar_clauses_count', models.IntegerField(db_column='similarClausesCount', default=0, help_text='Number of similar clauses in database')),
                ('avg_outcome_score', models.FloatField(blank=True, db_column='avgOutcomeScore', help_text='Average outcome score from precedents', null=True)),
                ('precedent_data', models.JSONField(db_column='precedentData', default=dict, help_text='Detailed precedent information')),
                ('reviewed_at', models.DateTimeField(blank=True, db_column='reviewedAt', null=True)),
                ('review_notes', models.TextField(blank=True, db_column='reviewNotes', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
                ('updated_at', models.DateTimeField(auto_now=True, db_column='updatedAt')),
                ('clause', models.ForeignKey(db_constraint=False, db_column='clauseId', help_text='Clause being negotiated', on_delete=django.db.models.deletion.CASCADE, related_name='negotiation_suggestions', to='core.clause')),
                ('reviewed_by', models.ForeignKey(db_constraint=False, blank=True, db_column='reviewedBy', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='reviewed_negotiation_suggestions', to='core.user')),
                ('session', models.ForeignKey(db_constraint=False, db_column='sessionId', on_delete=django.db.models.deletion.CASCADE, related_name='suggestions', to='core.negotiationsession')),
            ],
            options={
                'db_table': 'negotiation_clause_suggestions',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='NegotiationPosition',
            fields=[
                ('id', models.CharField(default=core.models.generate_uuid, editable=False, max_length=36, primary_key=True, serialize=False)),
                ('iteration', models.IntegerField(default=1, help_text='Position version number (increments with counteroffers)')),
                ('position_status', models.CharField(choices=[('PROPOSED', 'Proposed'), ('COUNTERED', 'Countered'), ('ACCEPTED', 'Accepted'), ('REJECTED', 'Rejected'), ('STALLED', 'Stalled')], db_column='positionStatus', max_length=20)),
                ('our_text', models.TextField(db_column='ourText', help_text='Our proposed clause text')),
                ('our_priority', models.CharField(choices=[('MUST_HAVE', 'Must Have'), ('IMPORTANT', 'Important'), ('NICE_TO_HAVE', 'Nice to Have')], db_column='ourPriority', max_length=20)),
                ('our_justification', models.TextField(blank=True, db_column='ourJustification', null=True)),
                ('their_text', models.TextField(blank=True, db_column='theirText', help_text='Counterparty proposed text', null=True)),
                ('their_feedback', models.TextField(blank=True, db_column='theirFeedback', help_text='Counterparty comments', null=True)),
                ('gap_analysis', models.JSONField(db_column='gapAnalysis', default=dict, help_text='AI analysis of differences between positions')),
                ('compromise_suggestions', models.JSONField(db_column='compromiseSuggestions', default=list, help_text='AI-generated compromise options')),
                ('proposed_at', models.DateTimeField(auto_now_add=True, db_column='proposedAt')),
                ('responded_at', models.DateTimeField(blank=True, db_column='respondedAt', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
                ('updated_at', models.DateTimeField(auto_now=True, db_column='updatedAt')),
                ('clause', models.ForeignKey(db_constraint=False, db_column='clauseId', on_delete=django.db.models.deletion.CASCADE, related_name='negotiation_positions', to='core.clause')),
                ('session', models.ForeignKey(db_constraint=False, db_column='sessionId', on_delete=django.db.models.deletion.CASCADE, related_name='positions', to='core.negotiationsession')),
            ],
            options={
                'db_table': 'negotiation_positions',
                'ordering': ['clause', '-iteration'],
            },
        ),
        # Add indexes
        migrations.AddIndex(
            model_name='negotiationsession',
            index=models.Index(fields=['contract', '-started_at'], name='negotiation_contract_idx'),
        ),
        migrations.AddIndex(
            model_name='negotiationsession',
            index=models.Index(fields=['status', '-last_activity_at'], name='negotiation_status_idx'),
        ),
        migrations.AddIndex(
            model_name='negotiationsession',
            index=models.Index(fields=['created_by', '-started_at'], name='negotiation_creator_idx'),
        ),
        migrations.AddIndex(
            model_name='negotiationmessage',
            index=models.Index(fields=['session', 'created_at'], name='negotiation_msg_session_idx'),
        ),
        migrations.AddIndex(
            model_name='negotiationmessage',
            index=models.Index(fields=['message_type', '-created_at'], name='negotiation_msg_type_idx'),
        ),
        migrations.AddIndex(
            model_name='negotiationclausesuggestion',
            index=models.Index(fields=['session', '-created_at'], name='negotiation_sug_session_idx'),
        ),
        migrations.AddIndex(
            model_name='negotiationclausesuggestion',
            index=models.Index(fields=['clause', 'status'], name='negotiation_sug_clause_idx'),
        ),
        migrations.AddIndex(
            model_name='negotiationclausesuggestion',
            index=models.Index(fields=['status', 'suggestion_type'], name='negotiation_sug_status_idx'),
        ),
        migrations.AddIndex(
            model_name='negotiationposition',
            index=models.Index(fields=['session', 'clause', '-iteration'], name='negotiation_pos_session_idx'),
        ),
        migrations.AddIndex(
            model_name='negotiationposition',
            index=models.Index(fields=['position_status', '-proposed_at'], name='negotiation_pos_status_idx'),
        ),
    ]
