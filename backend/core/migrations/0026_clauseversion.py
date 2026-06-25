# Generated manually to fix collation issues

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0025_contractintelligence_vectorembedding_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            # Create table with explicit collation for foreign key columns
            sql="""
            CREATE TABLE `clause_versions` (
                `id` char(36) COLLATE utf8mb4_bin NOT NULL PRIMARY KEY,
                `versionNumber` int NOT NULL,
                `originalText` longtext NOT NULL,
                `modifiedText` longtext NOT NULL,
                `changeDescription` longtext,
                `newRiskScore` double,
                `newRiskLevel` varchar(20),
                `newLikelihoodScore` double,
                `newImpactScore` double,
                `modifiedAt` datetime(6) NOT NULL,
                `approvedBy` char(36),
                `approvedAt` datetime(6),
                `clauseId` char(36) COLLATE utf8mb4_bin NOT NULL,
                `modifiedBy` char(36) COLLATE utf8mb4_bin NOT NULL,

                KEY `clause_vers_clauseI_f7de73_idx` (`clauseId`, `versionNumber` DESC),
                KEY `clause_vers_modifie_a374f8_idx` (`modifiedBy`, `modifiedAt` DESC),
                UNIQUE KEY `clause_versions_unique` (`clauseId`, `versionNumber`),

                CONSTRAINT `clause_versions_clauseId_fk`
                    FOREIGN KEY (`clauseId`) REFERENCES `clauses` (`id`) ON DELETE CASCADE,
                CONSTRAINT `clause_versions_modifiedBy_fk`
                    FOREIGN KEY (`modifiedBy`) REFERENCES `users` (`id`) ON DELETE RESTRICT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
            """,
            reverse_sql="DROP TABLE IF EXISTS `clause_versions`"
        ),
    ]
