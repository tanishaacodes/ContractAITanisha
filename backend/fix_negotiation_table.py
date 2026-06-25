import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    # Drop the existing table
    cursor.execute('DROP TABLE IF EXISTS clause_rewrite_suggestions')
    print('[OK] Dropped existing table')

    # Create the table with ALL columns
    cursor.execute("""
        CREATE TABLE clause_rewrite_suggestions (
            id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL PRIMARY KEY,
            clauseId CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
            contractId CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
            originalText LONGTEXT NOT NULL,
            suggestedText LONGTEXT NOT NULL,
            rationale LONGTEXT NOT NULL,
            category VARCHAR(30) NOT NULL,
            priority VARCHAR(10) NOT NULL DEFAULT 'MEDIUM',
            status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
            impactAnalysis LONGTEXT NULL,
            negotiationTips LONGTEXT NULL,
            confidenceScore DOUBLE NOT NULL DEFAULT 0.5,
            createdBy CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL,
            reviewedBy CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL,
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

    print('[OK] Created clause_rewrite_suggestions table with ALL columns')

    # Verify
    cursor.execute('DESCRIBE clause_rewrite_suggestions')
    columns = cursor.fetchall()
    print(f'\nTable now has {len(columns)} columns:')
    for col in columns:
        print(f'  - {col[0]}')

print('\n[OK] Negotiation Agent table fixed!')
