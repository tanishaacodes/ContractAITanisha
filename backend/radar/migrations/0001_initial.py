from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name='ContractExposure',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contract_id', models.CharField(db_index=True, max_length=36)),
                ('exposure_type', models.CharField(max_length=50)),
                ('signal_name', models.CharField(max_length=255)),
                ('sensitivity_factor', models.FloatField(default=0.0)),
                ('estimated_impact', models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ('is_protected', models.BooleanField(default=False)),
                ('computed_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['-computed_at']},
        ),
        migrations.CreateModel(
            name='StrategicAlert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contract_id', models.CharField(db_index=True, max_length=36)),
                ('alert_type', models.CharField(choices=[('strategic_opportunity', 'Strategic Opportunity'), ('cost_risk', 'Cost Risk'), ('renegotiation_opportunity', 'Renegotiation Opportunity'), ('hedging_required', 'Hedging Required')], max_length=50)),
                ('exposure_type', models.CharField(blank=True, max_length=50)),
                ('message', models.TextField()),
                ('estimated_value', models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ('is_actioned', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.AddIndex(
            model_name='contractexposure',
            index=models.Index(fields=['contract_id', 'exposure_type'], name='radar_contr_exp_idx'),
        ),
        migrations.AddIndex(
            model_name='strategicalert',
            index=models.Index(fields=['contract_id', 'alert_type'], name='radar_alert_idx'),
        ),
    ]
