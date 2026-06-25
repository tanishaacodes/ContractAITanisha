from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0050_add_clause_library_enhancements'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClauseCategory',
            fields=[
                ('id', models.CharField(max_length=36, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('parent_id', models.CharField(max_length=36, null=True, blank=True, db_column='parentId')),
                ('clause_count', models.IntegerField(default=0, db_column='clauseCount')),
                ('is_standard', models.BooleanField(default=False, db_column='isStandard')),
                ('embedding_vector', models.JSONField(default=list, blank=True, db_column='embeddingVector')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='createdAt')),
                ('updated_at', models.DateTimeField(auto_now=True, db_column='updatedAt')),
            ],
            options={
                'db_table': 'clause_categories',
                'ordering': ['name'],
            },
        ),
    ]
