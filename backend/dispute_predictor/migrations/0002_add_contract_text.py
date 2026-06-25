from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dispute_predictor', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='disputeprediction',
            name='contract_text',
            field=models.TextField(blank=True, db_column='contractText', default=''),
            preserve_default=False,
        ),
    ]
