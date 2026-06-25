# Manual migration to add counterparty FK to Contract

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('negotiation', '0001_initial'),
        ('core', '0039_merge_20260127_1448'),
    ]

    operations = [
        migrations.AddField(
            model_name='contract',
            name='counterparty',
            field=models.ForeignKey(
                blank=True,
                db_column='counterpartyId',
                help_text='Linked counterparty for portfolio-level risk analysis',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='contracts',
                to='negotiation.counterparty'
            ),
        ),
    ]
