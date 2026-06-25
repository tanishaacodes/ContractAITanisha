# Generated manually to handle VARCHAR(36) foreign keys

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_contract_status'),
    ]

    operations = [
        # Update Contract status choices
        migrations.AlterField(
            model_name='contract',
            name='status',
            field=models.CharField(
                choices=[
                    ('DRAFT', 'Draft'),
                    ('LEGAL_REVIEW', 'Legal Review'),
                    ('BUSINESS_REVIEW', 'Business Review'),
                    ('COMPLIANCE_REVIEW', 'Compliance Review'),
                    ('FINAL_APPROVAL', 'Final Approval'),
                    ('APPROVED', 'Approved'),
                    ('REJECTED', 'Rejected')
                ],
                default='DRAFT',
                help_text='Contract workflow status',
                max_length=20
            ),
        ),

        # Create ApprovalTask table with raw SQL
        migrations.RunSQL(
            sql="""
                CREATE TABLE IF NOT EXISTS approval_tasks (
                    id VARCHAR(36) NOT NULL PRIMARY KEY,
                    contractId VARCHAR(36) NOT NULL,
                    roleRequired VARCHAR(50) NOT NULL,
                    assignedTo VARCHAR(36) NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
                    comments TEXT NULL,
                    createdAt DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    approvedAt DATETIME(6) NULL,
                    workflowStage VARCHAR(30) NOT NULL,
                    CONSTRAINT approval_tasks_contract_fk
                        FOREIGN KEY (contractId) REFERENCES contracts(id) ON DELETE CASCADE,
                    CONSTRAINT approval_tasks_assignedTo_fk
                        FOREIGN KEY (assignedTo) REFERENCES users(id) ON DELETE SET NULL,
                    INDEX approval_ta_contrac_6bbf1f_idx (contractId, status),
                    INDEX approval_ta_roleReq_f42efd_idx (roleRequired, status),
                    INDEX approval_ta_assigne_8b3fa0_idx (assignedTo, status)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            reverse_sql="DROP TABLE IF EXISTS approval_tasks;"
        ),

        # Create ApprovalAudit table with raw SQL
        migrations.RunSQL(
            sql="""
                CREATE TABLE IF NOT EXISTS approval_audits (
                    id VARCHAR(36) NOT NULL PRIMARY KEY,
                    contractId VARCHAR(36) NOT NULL,
                    approvalTaskId VARCHAR(36) NOT NULL,
                    userId VARCHAR(36) NULL,
                    userRole VARCHAR(50) NOT NULL,
                    action VARCHAR(20) NOT NULL,
                    comments TEXT NOT NULL,
                    timestamp DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    ipAddress VARCHAR(39) NULL,
                    userAgent VARCHAR(500) NULL,
                    CONSTRAINT approval_audits_contract_fk
                        FOREIGN KEY (contractId) REFERENCES contracts(id) ON DELETE CASCADE,
                    CONSTRAINT approval_audits_task_fk
                        FOREIGN KEY (approvalTaskId) REFERENCES approval_tasks(id) ON DELETE CASCADE,
                    CONSTRAINT approval_audits_user_fk
                        FOREIGN KEY (userId) REFERENCES users(id) ON DELETE SET NULL,
                    INDEX approval_au_contrac_09158a_idx (contractId, timestamp DESC),
                    INDEX approval_au_userId_1d4faa_idx (userId, timestamp DESC),
                    INDEX approval_au_approva_99c048_idx (approvalTaskId)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            reverse_sql="DROP TABLE IF EXISTS approval_audits;"
        ),
    ]
