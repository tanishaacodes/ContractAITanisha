from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='ContractRedlineAI',
            fields=[
                ('id', models.CharField(default=None, max_length=36, primary_key=True, serialize=False)),
                ('contractId', models.CharField(db_column='contractId', max_length=36)),
                ('originalClause', models.TextField(db_column='originalClause')),
                ('suggestedClause', models.TextField(db_column='suggestedClause', null=True)),
                ('riskScore', models.FloatField(db_column='riskScore', default=0.0)),
                ('changeType', models.CharField(db_column='changeType', default='minor', max_length=50)),
                ('explanation', models.TextField(null=True)),
                ('status', models.CharField(default='pending', max_length=20)),
                ('createdAt', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
            ],
            options={
                'db_table': 'ai_studio_redlines',
            },
        ),
        migrations.CreateModel(
            name='NegotiationAgentSession',
            fields=[
                ('id', models.CharField(default=None, max_length=36, primary_key=True, serialize=False)),
                ('contractId', models.CharField(db_column='contractId', max_length=36)),
                ('clauseText', models.TextField(db_column='clauseText')),
                ('rounds', models.IntegerField(default=3)),
                ('status', models.CharField(default='completed', max_length=20)),
                ('createdAt', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
            ],
            options={
                'db_table': 'ai_studio_negotiation_sessions',
            },
        ),
        migrations.CreateModel(
            name='NegotiationAgentMessage',
            fields=[
                ('id', models.CharField(default=None, max_length=36, primary_key=True, serialize=False)),
                ('sessionId', models.CharField(db_column='sessionId', max_length=36)),
                ('agentName', models.CharField(db_column='agentName', max_length=50)),
                ('message', models.TextField()),
                ('round', models.IntegerField()),
                ('createdAt', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
            ],
            options={
                'db_table': 'ai_studio_negotiation_messages',
            },
        ),
        migrations.CreateModel(
            name='ContractAlert',
            fields=[
                ('id', models.CharField(default=None, max_length=36, primary_key=True, serialize=False)),
                ('contractId', models.CharField(db_column='contractId', max_length=36, null=True)),
                ('alertType', models.CharField(db_column='alertType', max_length=50)),
                ('severity', models.CharField(default='medium', max_length=20)),
                ('message', models.TextField()),
                ('headline', models.TextField(null=True)),
                ('createdAt', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
            ],
            options={
                'db_table': 'contract_suite_alerts',
            },
        ),
        migrations.CreateModel(
            name='ContractOutcomeRL',
            fields=[
                ('id', models.CharField(default=None, max_length=36, primary_key=True, serialize=False)),
                ('contractId', models.CharField(db_column='contractId', max_length=36)),
                ('action', models.CharField(max_length=100)),
                ('profit', models.FloatField(default=0.0)),
                ('dispute', models.BooleanField(default=False)),
                ('delayDays', models.IntegerField(db_column='delayDays', default=0)),
                ('reward', models.FloatField(default=0.0)),
                ('createdAt', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
            ],
            options={
                'db_table': 'contract_suite_rl_outcomes',
            },
        ),
    ]
