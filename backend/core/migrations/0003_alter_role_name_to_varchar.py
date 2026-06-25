# Migration to change role name from ENUM to VARCHAR

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_alter_role_name'),
    ]

    operations = [
        migrations.RunSQL(
            sql='ALTER TABLE roles CHANGE COLUMN name name VARCHAR(50) NOT NULL UNIQUE',
            reverse_sql='ALTER TABLE roles CHANGE COLUMN name name ENUM("Admin", "Legal Reviewer", "Proc Reviewer", "Viewer") NOT NULL'
        ),
    ]
