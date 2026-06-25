from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0048_add_temporal_clause_tracking'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS contract_links (
                id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                sourceContractId VARCHAR(36) NOT NULL,
                targetContractId VARCHAR(36) NOT NULL,
                linkType VARCHAR(50) NOT NULL DEFAULT 'reference',
                description LONGTEXT NULL,
                strength DOUBLE NOT NULL DEFAULT 1.0,
                createdAt DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                createdBy VARCHAR(36) NULL,
                CONSTRAINT fk_cl_source FOREIGN KEY (sourceContractId) REFERENCES contracts(id) ON DELETE CASCADE,
                CONSTRAINT fk_cl_target FOREIGN KEY (targetContractId) REFERENCES contracts(id) ON DELETE CASCADE,
                UNIQUE KEY uq_contract_links (sourceContractId, targetContractId, linkType),
                INDEX idx_contractlinks_source (sourceContractId),
                INDEX idx_contractlinks_target (targetContractId),
                INDEX idx_contractlinks_type (linkType)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            reverse_sql="DROP TABLE IF EXISTS contract_links;",
        ),
    ]
