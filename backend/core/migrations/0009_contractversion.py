# Custom migration for ContractVersion with proper collation handling

import core.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_contract_contract_duration_contract_contract_value_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            # Create table with proper collation for foreign keys
            sql="""
            CREATE TABLE `contract_versions` (
                `id` char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL PRIMARY KEY,
                `contractId` char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
                `createdBy` char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL,
                `versionNumber` int NOT NULL,
                `changeDescription` longtext NULL,
                `filename` varchar(255) NOT NULL,
                `originalFilename` varchar(255) NOT NULL,
                `fileType` varchar(50) NOT NULL,
                `filePath` longtext NOT NULL,
                `fullText` longtext NULL,
                `contractType` varchar(100) NULL,
                `contractValue` varchar(100) NULL,
                `partyName` varchar(255) NULL,
                `contractDuration` varchar(100) NULL,
                `createdAt` datetime(6) NOT NULL,
                UNIQUE KEY `contract_versions_contractId_versionNumber_unique` (`contractId`, `versionNumber`),
                KEY `contract_versions_contractId_idx` (`contractId`, `versionNumber`),
                KEY `contract_versions_createdBy_idx` (`createdBy`),
                CONSTRAINT `contract_versions_contractId_fk`
                    FOREIGN KEY (`contractId`) REFERENCES `contracts` (`id`)
                    ON DELETE CASCADE,
                CONSTRAINT `contract_versions_createdBy_fk`
                    FOREIGN KEY (`createdBy`) REFERENCES `users` (`id`)
                    ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
            """,
            reverse_sql="DROP TABLE IF EXISTS `contract_versions`"
        ),
    ]
