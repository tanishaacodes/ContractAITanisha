"""
Manually create clause_rewrite_suggestions table bypassing Django migration issues
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    # Create clause_rewrite_suggestions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clause_rewrite_suggestions (
            id CHAR(36) NOT NULL PRIMARY KEY,
            clauseId CHAR(36) NOT NULL,
            contractId CHAR(36) NOT NULL,
            originalText TEXT NOT NULL,
            suggestedText TEXT NOT NULL,
            rationale TEXT NOT NULL,
            category VARCHAR(30) NOT NULL,
            priority VARCHAR(10) NOT NULL DEFAULT 'MEDIUM',
            status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
            impactAnalysis TEXT NULL,
            negotiationTips TEXT NULL,
            confidenceScore FLOAT NOT NULL DEFAULT 0.5,
            createdBy CHAR(36) NULL,
            reviewedBy CHAR(36) NULL,
            reviewedAt DATETIME NULL,
            createdAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

            CONSTRAINT fk_clause_rewrite_clause
                FOREIGN KEY (clauseId) REFERENCES clauses(id)
                ON DELETE CASCADE,
            CONSTRAINT fk_clause_rewrite_contract
                FOREIGN KEY (contractId) REFERENCES contracts(id)
                ON DELETE CASCADE,
            CONSTRAINT fk_clause_rewrite_created_by
                FOREIGN KEY (createdBy) REFERENCES users(id)
                ON DELETE SET NULL,
            CONSTRAINT fk_clause_rewrite_reviewed_by
                FOREIGN KEY (reviewedBy) REFERENCES users(id)
                ON DELETE SET NULL,

            INDEX idx_contract_status (contractId, status),
            INDEX idx_clause (clauseId),
            INDEX idx_status (status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
    """)

    print("[OK] Created clause_rewrite_suggestions table")

print("\n[OK] Negotiation Agent table setup complete!")
