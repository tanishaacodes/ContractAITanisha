# Generated migration for Contract Redlining feature

from django.db import migrations, models
import django.db.models.deletion


def generate_uuid():
    import uuid
    return str(uuid.uuid4())


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0033_add_connector_permissions'),
    ]

    operations = [
        # Create RedlineSession table with raw SQL to ensure charset/collation compatibility
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS `redline_sessions` (
                `id` VARCHAR(36) NOT NULL PRIMARY KEY,
                `contractId` VARCHAR(36) NOT NULL,
                `userId` VARCHAR(36) NOT NULL,
                `status` VARCHAR(20) NOT NULL DEFAULT 'IN_PROGRESS',
                `jurisdiction` VARCHAR(100) NOT NULL DEFAULT 'Common Law',
                `totalClausesAnalyzed` INT NOT NULL DEFAULT 0,
                `highRiskCount` INT NOT NULL DEFAULT 0,
                `mediumRiskCount` INT NOT NULL DEFAULT 0,
                `lowRiskCount` INT NOT NULL DEFAULT 0,
                `changesAccepted` INT NOT NULL DEFAULT 0,
                `changesRejected` INT NOT NULL DEFAULT 0,
                `docxExportedAt` DATETIME NULL,
                `pdfExportedAt` DATETIME NULL,
                `exportedFilePath` TEXT NULL,
                `createdAt` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                `updatedAt` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                `completedAt` DATETIME NULL,
                CONSTRAINT `fk_redline_session_contract` FOREIGN KEY (`contractId`) REFERENCES `contracts`(`id`) ON DELETE CASCADE,
                CONSTRAINT `fk_redline_session_user` FOREIGN KEY (`userId`) REFERENCES `users`(`id`) ON DELETE CASCADE,
                INDEX `idx_redline_session_contract` (`contractId`, `createdAt` DESC),
                INDEX `idx_redline_session_user_status` (`userId`, `status`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """,
            reverse_sql="DROP TABLE IF EXISTS `redline_sessions`;"
        ),

        # Create RedlineChange table with raw SQL
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS `redline_changes` (
                `id` VARCHAR(36) NOT NULL PRIMARY KEY,
                `sessionId` VARCHAR(36) NOT NULL,
                `clauseId` VARCHAR(36) NULL,
                `clauseName` VARCHAR(255) NOT NULL,
                `clauseIndex` INT NOT NULL DEFAULT 0,
                `originalText` TEXT NOT NULL,
                `suggestedText` TEXT NOT NULL,
                `acceptedText` TEXT NULL,
                `redlineDiff` TEXT NULL,
                `riskType` VARCHAR(30) NOT NULL,
                `riskScore` INT NOT NULL DEFAULT 0,
                `riskExplanation` TEXT NOT NULL,
                `legalDoctrine` VARCHAR(255) NULL,
                `courtReasoning` TEXT NULL,
                `litigationRisk` VARCHAR(100) NULL,
                `judicialTreatment` TEXT NULL,
                `status` VARCHAR(20) NOT NULL DEFAULT 'PENDING',
                `reviewedAt` DATETIME NULL,
                `reviewedBy` VARCHAR(36) NULL,
                `createdAt` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                `updatedAt` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                CONSTRAINT `fk_redline_change_session` FOREIGN KEY (`sessionId`) REFERENCES `redline_sessions`(`id`) ON DELETE CASCADE,
                CONSTRAINT `fk_redline_change_clause` FOREIGN KEY (`clauseId`) REFERENCES `clauses`(`id`) ON DELETE SET NULL,
                CONSTRAINT `fk_redline_change_reviewer` FOREIGN KEY (`reviewedBy`) REFERENCES `users`(`id`) ON DELETE SET NULL,
                INDEX `idx_redline_change_session_status` (`sessionId`, `status`),
                INDEX `idx_redline_change_risk` (`riskType`, `riskScore` DESC),
                INDEX `idx_redline_change_session_index` (`sessionId`, `clauseIndex`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """,
            reverse_sql="DROP TABLE IF EXISTS `redline_changes`;"
        ),
    ]
