"""
Fix risk analysis tables structure
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from django.db import connection

def fix_risk_tables():
    """Drop and recreate risk analysis tables"""
    print("="*70)
    print("Fixing Risk Analysis Tables")
    print("="*70)

    with connection.cursor() as cursor:
        # Drop existing tables
        print("\n1. Dropping existing tables...")
        cursor.execute("DROP TABLE IF EXISTS clause_deviations")
        print("   [OK] Dropped clause_deviations")

        cursor.execute("DROP TABLE IF EXISTS contract_risk_analysis")
        print("   [OK] Dropped contract_risk_analysis")

        cursor.execute("DROP TABLE IF EXISTS template_clauses")
        print("   [OK] Dropped template_clauses")

        # Create template_clauses table
        print("\n2. Creating template_clauses table...")
        cursor.execute("""
            CREATE TABLE template_clauses (
                id CHAR(36) PRIMARY KEY,
                contractType VARCHAR(100) NOT NULL,
                clauseName VARCHAR(150) NOT NULL,
                importance VARCHAR(20) NOT NULL DEFAULT 'IMPORTANT',
                description TEXT,
                standardLanguage TEXT,
                riskKeywords JSON,
                createdAt DATETIME(6) NOT NULL,
                updatedAt DATETIME(6) NOT NULL,
                UNIQUE KEY unique_contract_clause (contractType, clauseName)
            )
        """)
        print("   [OK] Created template_clauses")

        # Create contract_risk_analysis table
        print("\n3. Creating contract_risk_analysis table...")
        cursor.execute("""
            CREATE TABLE contract_risk_analysis (
                id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin PRIMARY KEY,
                contractId CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
                riskLevel VARCHAR(20) NOT NULL,
                riskScore INT NOT NULL DEFAULT 0,
                totalDeviations INT NOT NULL DEFAULT 0,
                criticalIssues INT NOT NULL DEFAULT 0,
                mediumIssues INT NOT NULL DEFAULT 0,
                lowIssues INT NOT NULL DEFAULT 0,
                analysisSummary TEXT,
                createdAt DATETIME(6) NOT NULL,
                updatedAt DATETIME(6) NOT NULL,
                UNIQUE KEY contract_risk_unique (contractId),
                FOREIGN KEY (contractId) REFERENCES contracts(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """)
        print("   [OK] Created contract_risk_analysis")

        # Create clause_deviations table
        print("\n4. Creating clause_deviations table...")
        cursor.execute("""
            CREATE TABLE clause_deviations (
                id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin PRIMARY KEY,
                riskAnalysisId CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
                clauseName VARCHAR(150) NOT NULL,
                deviationType VARCHAR(20) NOT NULL,
                severity VARCHAR(20) NOT NULL,
                description TEXT NOT NULL,
                recommendation TEXT,
                createdAt DATETIME(6) NOT NULL,
                updatedAt DATETIME(6) NOT NULL,
                FOREIGN KEY (riskAnalysisId) REFERENCES contract_risk_analysis(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """)
        print("   [OK] Created clause_deviations")

    print("\n" + "="*70)
    print("Tables recreated successfully!")
    print("="*70 + "\n")

if __name__ == '__main__':
    fix_risk_tables()
