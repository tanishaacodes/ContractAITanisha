import uuid
from django.db import models


def generate_uuid():
    return str(uuid.uuid4())


class ContractRedlineAI(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid)
    contractId = models.CharField(max_length=36, db_column='contractId')
    originalClause = models.TextField(db_column='originalClause')
    suggestedClause = models.TextField(db_column='suggestedClause', null=True)
    riskScore = models.FloatField(db_column='riskScore', default=0.0)
    changeType = models.CharField(max_length=50, db_column='changeType', default='minor')
    explanation = models.TextField(null=True)
    status = models.CharField(max_length=20, default='pending')  # pending/accepted/rejected
    createdAt = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'ai_studio_redlines'


class NegotiationAgentSession(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid)
    contractId = models.CharField(max_length=36, db_column='contractId')
    clauseText = models.TextField(db_column='clauseText')
    rounds = models.IntegerField(default=3)
    status = models.CharField(max_length=20, default='completed')
    createdAt = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'ai_studio_negotiation_sessions'


class NegotiationAgentMessage(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid)
    sessionId = models.CharField(max_length=36, db_column='sessionId')
    agentName = models.CharField(max_length=50, db_column='agentName')
    message = models.TextField()
    round = models.IntegerField()
    createdAt = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'ai_studio_negotiation_messages'


class ContractAlert(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid)
    contractId = models.CharField(max_length=36, db_column='contractId', null=True)
    alertType = models.CharField(max_length=50, db_column='alertType')
    severity = models.CharField(max_length=20, default='medium')
    message = models.TextField()
    headline = models.TextField(null=True)
    createdAt = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'contract_suite_alerts'


class ContractOutcomeRL(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=generate_uuid)
    contractId = models.CharField(max_length=36, db_column='contractId')
    action = models.CharField(max_length=100)
    profit = models.FloatField(default=0.0)
    dispute = models.BooleanField(default=False)
    delayDays = models.IntegerField(db_column='delayDays', default=0)
    reward = models.FloatField(default=0.0)
    createdAt = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'contract_suite_rl_outcomes'
