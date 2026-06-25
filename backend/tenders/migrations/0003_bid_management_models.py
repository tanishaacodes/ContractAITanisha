"""
Migration 0003 — Bid Management Models
Creates: BidDepartment, BidActionItem, BidActionDependency,
         BidDepartmentRiskPropagation, BidReadinessSnapshot
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tenders', '0002_tenderamendment'),
    ]

    operations = [

        # ── BidDepartment ──────────────────────────────────────────────────
        migrations.CreateModel(
            name='BidDepartment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, choices=[
                    ('Civil',       'Civil'),
                    ('Mechanical',  'Mechanical'),
                    ('Electrical',  'Electrical'),
                    ('MEP',         'MEP'),
                    ('Signaling',   'Signaling'),
                    ('Planning',    'Planning'),
                    ('Procurement', 'Procurement'),
                    ('Finance',     'Finance'),
                    ('Legal',       'Legal'),
                    ('HSE',         'HSE'),
                    ('QA/QC',       'QA/QC'),
                ])),
                ('workload_weight', models.FloatField(default=1.0)),
                ('description', models.TextField(blank=True, null=True)),
            ],
            options={'db_table': 'bid_department', 'ordering': ['name']},
        ),

        # ── BidActionItem ──────────────────────────────────────────────────
        migrations.CreateModel(
            name='BidActionItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID')),
                ('tender', models.ForeignKey(
                    db_constraint=False,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='action_items',
                    to='tenders.tender',
                )),
                ('department', models.ForeignKey(
                    db_constraint=False,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='action_items',
                    to='tenders.biddepartment',
                )),
                ('source_type', models.CharField(max_length=50, default='Static', choices=[
                    ('BOQ',         'BOQ'),
                    ('Risk',        'Risk'),
                    ('Clause',      'Clause'),
                    ('Negotiation', 'Negotiation'),
                    ('Eligibility', 'Eligibility'),
                    ('Static',      'Static'),
                ])),
                ('source_ref', models.CharField(max_length=255, blank=True, null=True)),
                ('title', models.CharField(max_length=500)),
                ('description', models.TextField(blank=True, null=True)),
                ('priority', models.CharField(max_length=20, default='Medium', choices=[
                    ('Low', 'Low'), ('Medium', 'Medium'),
                    ('High', 'High'), ('Critical', 'Critical'),
                ])),
                ('complexity_score',   models.FloatField(default=0.0)),
                ('risk_score',         models.FloatField(default=0.0)),
                ('financial_exposure', models.DecimalField(max_digits=20, decimal_places=2, default=0)),
                ('status', models.CharField(max_length=20, default='Pending', choices=[
                    ('Pending',     'Pending'),
                    ('In Progress', 'In Progress'),
                    ('Review',      'Review'),
                    ('Completed',   'Completed'),
                    ('Blocked',     'Blocked'),
                ])),
                ('due_date',     models.DateTimeField(null=True, blank=True)),
                ('ai_generated', models.BooleanField(default=False)),
                ('created_at',   models.DateTimeField(auto_now_add=True)),
                ('updated_at',   models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'bid_action_item',
                'ordering': ['-risk_score', 'priority', 'department'],
            },
        ),

        # ── BidActionDependency ────────────────────────────────────────────
        migrations.CreateModel(
            name='BidActionDependency',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID')),
                ('source', models.ForeignKey(
                    db_constraint=False,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='dependencies_as_source',
                    to='tenders.bidactionitem',
                )),
                ('target', models.ForeignKey(
                    db_constraint=False,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='dependencies_as_target',
                    to='tenders.bidactionitem',
                )),
                ('dependency_weight', models.FloatField(default=0.5)),
            ],
            options={
                'db_table': 'bid_action_dependency',
                'unique_together': {('source', 'target')},
            },
        ),

        # ── BidDepartmentRiskPropagation ───────────────────────────────────
        migrations.CreateModel(
            name='BidDepartmentRiskPropagation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID')),
                ('tender', models.ForeignKey(
                    db_constraint=False,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='risk_propagations',
                    to='tenders.tender',
                )),
                ('department_name',      models.CharField(max_length=100)),
                ('base_risk',            models.FloatField(default=0.0)),
                ('propagated_risk',      models.FloatField(default=0.0)),
                ('amplification',        models.FloatField(default=0.0)),
                ('predicted_delay_days', models.IntegerField(default=0)),
                ('task_count',           models.IntegerField(default=0)),
                ('computed_at',          models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'bid_dept_risk_propagation',
                'ordering': ['-propagated_risk'],
                'unique_together': {('tender', 'department_name')},
            },
        ),

        # ── BidReadinessSnapshot ───────────────────────────────────────────
        migrations.CreateModel(
            name='BidReadinessSnapshot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID')),
                ('tender', models.ForeignKey(
                    db_constraint=False,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='readiness_snapshots',
                    to='tenders.tender',
                )),
                ('readiness_index',   models.FloatField(default=0.0)),
                ('data_readiness',    models.FloatField(default=0.0)),
                ('task_completion',   models.FloatField(default=0.0)),
                ('total_actions',     models.IntegerField(default=0)),
                ('completed_actions', models.IntegerField(default=0)),
                ('critical_pending',  models.IntegerField(default=0)),
                ('total_exposure',    models.DecimalField(max_digits=20, decimal_places=2, default=0)),
                ('created_at',        models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'bid_readiness_snapshot',
                'ordering': ['-created_at'],
            },
        ),

        # ── Indexes (added after all CreateModels) ─────────────────────────
        migrations.AddIndex(
            model_name='bidactionitem',
            index=models.Index(fields=['tender', 'status'], name='bid_action_tender_status'),
        ),
        migrations.AddIndex(
            model_name='bidactionitem',
            index=models.Index(fields=['tender', 'department'], name='bid_action_tender_dept'),
        ),
        migrations.AddIndex(
            model_name='bidactionitem',
            index=models.Index(fields=['tender', 'priority'], name='bid_action_tender_prio'),
        ),
        migrations.AddIndex(
            model_name='bidreadinesssnapshot',
            index=models.Index(
                fields=['tender', '-created_at'],
                name='bid_ready_tender_date',
            ),
        ),
    ]
