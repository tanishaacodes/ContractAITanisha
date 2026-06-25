"""
Manual table creation script for ContractGraphMeta
Run this if makemigrations fails: python create_graph_meta_table.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from django.db import connection

def create_contract_graph_meta_table():
    """Create contract_graph_meta table if it doesn't exist"""

    with connection.cursor() as cursor:
        # Check if table exists
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
            AND table_name = 'contract_graph_meta'
        """)

        exists = cursor.fetchone()[0]

        if exists:
            print("[OK] Table 'contract_graph_meta' already exists")
            return

        # Create table
        print("Creating 'contract_graph_meta' table...")

        cursor.execute("""
            CREATE TABLE contract_graph_meta (
                id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL PRIMARY KEY,
                contractId CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL UNIQUE,
                graphSummary JSON NOT NULL,
                riskTimeline JSON NOT NULL,
                negotiationAdvice JSON NOT NULL,
                neo4jSynced BOOLEAN DEFAULT FALSE,
                createdAt DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                updatedAt DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),

                CONSTRAINT fk_contract_graph_meta_contract
                    FOREIGN KEY (contractId)
                    REFERENCES contracts(id)
                    ON DELETE CASCADE,

                INDEX idx_contract_graph_meta_contract (contractId)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        print("[OK] Table 'contract_graph_meta' created successfully!")

if __name__ == '__main__':
    try:
        create_contract_graph_meta_table()
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
