from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tenders', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TenderAmendment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version_number', models.IntegerField()),
                ('amendment_note', models.TextField(blank=True, null=True)),
                ('snapshot', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('tender', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='amendments',
                    to='tenders.tender',
                )),
                ('uploaded_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='tender_amendments',
                    to=settings.AUTH_USER_MODEL,
                    db_constraint=False,
                )),
            ],
            options={
                'ordering': ['-version_number'],
                'indexes': [
                    models.Index(fields=['tender', '-version_number'], name='tenders_ten_tender__idx'),
                ],
            },
        ),
    ]
