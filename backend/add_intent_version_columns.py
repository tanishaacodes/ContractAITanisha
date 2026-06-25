"""
Manually add contract_version FK columns with correct collation to intent models.
This bypasses Django migrations to handle MySQL's strict collation checking.
"""

import MySQLdb
import os
from dotenv import load_dotenv

# Load database credentials
load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'contract_ai'),
    'charset': 'utf8mb4'
}

def add_version_columns():
    """Add contractVersionId columns with correct collation"""

    connection = MySQLdb.connect(**DB_CONFIG)
    cursor = connection.cursor()

    try:
        print("[INFO] Disabling foreign key checks...")
        cursor.execute("SET FOREIGN_KEY_CHECKS=0")

        # 1. Add contractVersionId to clause_intents
        print("[INFO] Adding contractVersionId to clause_intents...")
        cursor.execute("""
            ALTER TABLE clause_intents
            ADD COLUMN contractVersionId CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL,
            ADD CONSTRAINT clause_intents_contractVersionId_fk
                FOREIGN KEY (contractVersionId)
                REFERENCES contract_versions(id)
                ON DELETE CASCADE
        """)

        # 2. Add contractVersionId to intent_obligations
        print("[INFO] Adding contractVersionId to intent_obligations...")
        cursor.execute("""
            ALTER TABLE intent_obligations
            ADD COLUMN contractVersionId CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL,
            ADD CONSTRAINT intent_obligations_contractVersionId_fk
                FOREIGN KEY (contractVersionId)
                REFERENCES contract_versions(id)
                ON DELETE CASCADE
        """)

        # 3. Add contractVersionId to intent_rights
        print("[INFO] Adding contractVersionId to intent_rights...")
        cursor.execute("""
            ALTER TABLE intent_rights
            ADD COLUMN contractVersionId CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL,
            ADD CONSTRAINT intent_rights_contractVersionId_fk
                FOREIGN KEY (contractVersionId)
                REFERENCES contract_versions(id)
                ON DELETE CASCADE
        """)

        # 4. Add indexes
        print("[INFO] Creating indexes...")
        cursor.execute("""
            CREATE INDEX clauseintent_version_conf_idx
            ON clause_intents(contractVersionId, confidence DESC)
        """)

        cursor.execute("""
            CREATE INDEX intentobl_version_risk_idx
            ON intent_obligations(contractVersionId, riskScore DESC)
        """)

        cursor.execute("""
            CREATE INDEX intentright_version_risk_idx
            ON intent_rights(contractVersionId, riskScore DESC)
        """)

        print("[INFO] Re-enabling foreign key checks...")
        cursor.execute("SET FOREIGN_KEY_CHECKS=1")

        connection.commit()
        print("\n[SUCCESS] All version tracking columns added successfully!")
        print("[NEXT] Run: python manage.py migrate core 0017 --fake")

    except MySQLdb.Error as e:
        connection.rollback()
        print(f"\n[ERROR] {e}")
        print("[INFO] Rolling back changes...")
        return False

    finally:
        cursor.close()
        connection.close()

    return True

if __name__ == '__main__':
    print("=" * 60)
    print("Adding Version Tracking Columns to Intent Models")
    print("=" * 60)

    success = add_version_columns()

    if success:
        print("\n" + "=" * 60)
        print("All done! You can now fake the migration:")
        print("python manage.py migrate core 0017 --fake")
        print("=" * 60)
