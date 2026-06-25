from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name='MarketSignal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('signal_type', models.CharField(choices=[('commodity', 'Commodity'), ('interest_rate', 'Interest Rate'), ('fx', 'Foreign Exchange'), ('equity', 'Equity Index')], max_length=50)),
                ('signal_name', models.CharField(max_length=255)),
                ('ticker', models.CharField(blank=True, max_length=50, null=True)),
                ('current_value', models.FloatField(blank=True, null=True)),
                ('previous_value', models.FloatField(blank=True, null=True)),
                ('percent_change', models.FloatField(default=0.0)),
                ('status', models.CharField(default='live', max_length=20)),
                ('fetched_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['-fetched_at']},
        ),
        migrations.AddIndex(
            model_name='marketsignal',
            index=models.Index(fields=['signal_type', 'fetched_at'], name='market_mark_signal__idx'),
        ),
    ]
