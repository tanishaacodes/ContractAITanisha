# Custom migration for payment and subscription models only
# Generated manually to avoid AnalysisResult table conflict

import core.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0030_add_total_contracts_uploaded'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentTransaction',
            fields=[
                ('id', models.CharField(default=core.models.generate_uuid, editable=False, max_length=36, primary_key=True, serialize=False)),
                ('payment_method', models.CharField(choices=[('STRIPE', 'Stripe'), ('PAYPAL', 'PayPal')], db_column='paymentMethod', max_length=20)),
                ('amount', models.DecimalField(decimal_places=2, help_text='Payment amount in USD', max_digits=10)),
                ('currency', models.CharField(default='USD', help_text='Currency code (USD, EUR, etc.)', max_length=3)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('PROCESSING', 'Processing'), ('COMPLETED', 'Completed'), ('FAILED', 'Failed'), ('REFUNDED', 'Refunded'), ('CANCELLED', 'Cancelled')], default='PENDING', max_length=20)),
                ('stripe_payment_intent_id', models.CharField(blank=True, db_column='stripePaymentIntentId', help_text='Stripe Payment Intent ID', max_length=255, null=True)),
                ('paypal_order_id', models.CharField(blank=True, db_column='paypalOrderId', help_text='PayPal Order ID', max_length=255, null=True)),
                ('gateway_response', models.JSONField(blank=True, db_column='gatewayResponse', default=dict, help_text='Full response from payment gateway')),
                ('description', models.TextField(blank=True, help_text='Payment description', null=True)),
                ('failure_reason', models.TextField(blank=True, db_column='failureReason', help_text='Reason for payment failure', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
                ('completed_at', models.DateTimeField(blank=True, db_column='completedAt', null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, db_column='updatedAt')),
                ('plan', models.ForeignKey(db_column='planId', on_delete=django.db.models.deletion.PROTECT, related_name='payments', to='core.pricingplan')),
                ('user', models.ForeignKey(db_column='userId', on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='core.user')),
            ],
            options={
                'db_table': 'payment_transactions',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.CharField(default=core.models.generate_uuid, editable=False, max_length=36, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('ACTIVE', 'Active'), ('PAST_DUE', 'Past Due'), ('CANCELLED', 'Cancelled'), ('EXPIRED', 'Expired'), ('TRIALING', 'Trialing')], default='ACTIVE', max_length=20)),
                ('billing_cycle', models.CharField(choices=[('MONTHLY', 'Monthly'), ('YEARLY', 'Yearly')], db_column='billingCycle', default='MONTHLY', max_length=20)),
                ('stripe_subscription_id', models.CharField(blank=True, db_column='stripeSubscriptionId', help_text='Stripe Subscription ID', max_length=255, null=True)),
                ('paypal_subscription_id', models.CharField(blank=True, db_column='paypalSubscriptionId', help_text='PayPal Subscription ID', max_length=255, null=True)),
                ('start_date', models.DateTimeField(db_column='startDate', help_text='When subscription started')),
                ('current_period_start', models.DateTimeField(db_column='currentPeriodStart', help_text='Current billing period start')),
                ('current_period_end', models.DateTimeField(db_column='currentPeriodEnd', help_text='Current billing period end')),
                ('cancelled_at', models.DateTimeField(blank=True, db_column='cancelledAt', help_text='When subscription was cancelled', null=True)),
                ('ended_at', models.DateTimeField(blank=True, db_column='endedAt', help_text='When subscription ended', null=True)),
                ('trial_start', models.DateTimeField(blank=True, db_column='trialStart', null=True)),
                ('trial_end', models.DateTimeField(blank=True, db_column='trialEnd', null=True)),
                ('auto_renew', models.BooleanField(db_column='autoRenew', default=True, help_text='Whether subscription auto-renews')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
                ('updated_at', models.DateTimeField(auto_now=True, db_column='updatedAt')),
                ('plan', models.ForeignKey(db_column='planId', on_delete=django.db.models.deletion.PROTECT, related_name='subscriptions', to='core.pricingplan')),
                ('user', models.ForeignKey(db_column='userId', on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions', to='core.user')),
            ],
            options={
                'db_table': 'subscriptions',
                'ordering': ['-created_at'],
            },
        ),
        # Add indexes
        migrations.AddIndex(
            model_name='paymenttransaction',
            index=models.Index(fields=['user', '-created_at'], name='payment_tra_userId_99c153_idx'),
        ),
        migrations.AddIndex(
            model_name='paymenttransaction',
            index=models.Index(fields=['status'], name='payment_tra_status_137fde_idx'),
        ),
        migrations.AddIndex(
            model_name='paymenttransaction',
            index=models.Index(fields=['payment_method'], name='payment_tra_payment_63d9b3_idx'),
        ),
        migrations.AddIndex(
            model_name='paymenttransaction',
            index=models.Index(fields=['stripe_payment_intent_id'], name='payment_tra_stripeP_c7dd40_idx'),
        ),
        migrations.AddIndex(
            model_name='paymenttransaction',
            index=models.Index(fields=['paypal_order_id'], name='payment_tra_paypalO_8d0954_idx'),
        ),
        migrations.AddIndex(
            model_name='subscription',
            index=models.Index(fields=['user', 'status'], name='subscriptio_userId_ebe32d_idx'),
        ),
        migrations.AddIndex(
            model_name='subscription',
            index=models.Index(fields=['plan'], name='subscriptio_planId_9a6e09_idx'),
        ),
        migrations.AddIndex(
            model_name='subscription',
            index=models.Index(fields=['status', 'current_period_end'], name='subscriptio_status_e19ff4_idx'),
        ),
        migrations.AddIndex(
            model_name='subscription',
            index=models.Index(fields=['stripe_subscription_id'], name='subscriptio_stripeS_572145_idx'),
        ),
        migrations.AddIndex(
            model_name='subscription',
            index=models.Index(fields=['paypal_subscription_id'], name='subscriptio_paypalS_f089aa_idx'),
        ),
    ]
