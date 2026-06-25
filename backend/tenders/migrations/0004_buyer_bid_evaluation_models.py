"""
Migration 0004 — Buyer Bid Evaluation Models
Creates: Vendor, VendorBid, VendorClause, TenderLegalMetadata
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tenders', '0003_bid_management_models'),
    ]

    operations = [

        # ── Vendor ─────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='Vendor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('registration_number', models.CharField(
                    max_length=100, null=True, blank=True)),
                ('financial_rating', models.FloatField(default=0.5)),
                ('past_performance_score', models.FloatField(default=0.5)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'db_table': 'buyer_vendor', 'ordering': ['name']},
        ),

        # ── VendorBid ──────────────────────────────────────────────────────
        migrations.CreateModel(
            name='VendorBid',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID')),
                ('tender', models.ForeignKey(
                    'tenders.Tender',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='vendor_bids',
                    db_constraint=False,
                )),
                ('vendor', models.ForeignKey(
                    'tenders.Vendor',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='bids',
                    db_constraint=False,
                )),
                ('round_number', models.IntegerField(default=1, choices=[
                    (1, 'Round 1 (Initial Bid)'),
                    (2, 'Round 2'),
                    (3, 'Round 3'),
                    (4, 'BAFO (Best and Final Offer)'),
                ])),
                ('total_price', models.FloatField()),
                ('technical_score', models.FloatField(default=0.0)),
                ('commercial_score', models.FloatField(default=0.0)),
                ('legal_risk_score', models.FloatField(default=0.0)),
                ('delay_probability', models.FloatField(default=0.0)),
                ('deviation_score', models.FloatField(default=0.0)),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('notes', models.TextField(null=True, blank=True)),
            ],
            options={'db_table': 'buyer_vendor_bid', 'ordering': ['vendor', 'round_number']},
        ),
        migrations.AddConstraint(
            model_name='vendorbid',
            constraint=models.UniqueConstraint(
                fields=['tender', 'vendor', 'round_number'],
                name='unique_vendor_round_per_tender'
            ),
        ),

        # ── VendorClause ───────────────────────────────────────────────────
        migrations.CreateModel(
            name='VendorClause',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID')),
                ('vendor_bid', models.ForeignKey(
                    'tenders.VendorBid',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='clauses',
                    db_constraint=False,
                )),
                ('clause_type', models.CharField(max_length=60, choices=[
                    ('PAYMENT_TERMS', 'Payment Terms'),
                    ('LIQUIDATED_DAMAGES', 'Liquidated Damages'),
                    ('INDEMNITY', 'Indemnity'),
                    ('LIABILITY', 'Liability Cap'),
                    ('ARBITRATION', 'Arbitration'),
                    ('TERMINATION', 'Termination'),
                    ('FORCE_MAJEURE', 'Force Majeure'),
                    ('WARRANTY', 'Warranty'),
                    ('GOVERNING_LAW', 'Governing Law'),
                    ('PERFORMANCE_BOND', 'Performance Bond'),
                    ('OTHER', 'Other'),
                ])),
                ('clause_text', models.TextField()),
                ('deviation_score', models.FloatField(default=0.0)),
                ('risk_score', models.FloatField(default=0.0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'db_table': 'buyer_vendor_clause', 'ordering': ['-deviation_score']},
        ),

        # ── TenderLegalMetadata ────────────────────────────────────────────
        migrations.CreateModel(
            name='TenderLegalMetadata',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID')),
                ('tender', models.ForeignKey(
                    'tenders.Tender',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='legal_metadata',
                    db_constraint=False,
                )),
                ('clause_type', models.CharField(max_length=60)),
                ('clause_title', models.CharField(max_length=255)),
                ('clause_text', models.TextField()),
                ('risk_weight', models.FloatField(default=0.5)),
                ('financial_impact', models.FloatField(default=0.0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'db_table': 'buyer_tender_legal_metadata', 'ordering': ['-risk_weight']},
        ),
    ]
