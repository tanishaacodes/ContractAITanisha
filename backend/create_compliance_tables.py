"""
Create compliance tables with correct collation to match contracts table.
"""
import MySQLdb
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from django.conf import settings

db_config = settings.DATABASES['default']

conn = MySQLdb.connect(
    host=db_config['HOST'],
    user=db_config['USER'],
    password=db_config['PASSWORD'],
    database=db_config['NAME']
)

cursor = conn.cursor()

print('Creating compliance tables with correct collation...')

# Disable FK checks
cursor.execute('SET FOREIGN_KEY_CHECKS=0;')

# 1. ComplianceFramework
print('Creating compliance_frameworks table...')
cursor.execute("""
CREATE TABLE IF NOT EXISTS compliance_frameworks (
    id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    jurisdiction VARCHAR(100),
    effectiveDate DATE,
    version VARCHAR(50),
    isActive TINYINT(1) NOT NULL DEFAULT 1,
    priority INT NOT NULL DEFAULT 1,
    createdAt DATETIME NOT NULL,
    updatedAt DATETIME NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
""")

# 2. ComplianceRequirement
print('Creating compliance_requirements table...')
cursor.execute("""
CREATE TABLE IF NOT EXISTS compliance_requirements (
    id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL PRIMARY KEY,
    frameworkId CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
    requirementCode VARCHAR(100) NOT NULL,
    requirementName VARCHAR(300) NOT NULL,
    description TEXT,
    requirementType VARCHAR(50) NOT NULL,
    criticality VARCHAR(20) NOT NULL,
    detectionKeywords JSON,
    riskWeight FLOAT NOT NULL DEFAULT 1.0,
    complianceScoreWeight FLOAT NOT NULL DEFAULT 1.0,
    legalReference TEXT,
    isActive TINYINT(1) NOT NULL DEFAULT 1,
    createdAt DATETIME NOT NULL,
    updatedAt DATETIME NOT NULL,
    FOREIGN KEY (frameworkId) REFERENCES compliance_frameworks(id) ON DELETE CASCADE,
    UNIQUE KEY unique_framework_code (frameworkId, requirementCode),
    INDEX idx_framework_active (frameworkId, isActive),
    INDEX idx_requirement_type (requirementType)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
""")

# 3. IntentComplianceMapping
print('Creating intent_compliance_mappings table...')
cursor.execute("""
CREATE TABLE IF NOT EXISTS intent_compliance_mappings (
    id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL PRIMARY KEY,
    intentId CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
    requirementId CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
    contractId CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
    relevanceScore FLOAT NOT NULL,
    complianceStatus VARCHAR(20) NOT NULL,
    analysisSummary TEXT NOT NULL,
    gapDescription TEXT,
    recommendation TEXT,
    riskScore FLOAT NOT NULL DEFAULT 0.0,
    createdAt DATETIME NOT NULL,
    updatedAt DATETIME NOT NULL,
    FOREIGN KEY (intentId) REFERENCES intents(id) ON DELETE CASCADE,
    FOREIGN KEY (requirementId) REFERENCES compliance_requirements(id) ON DELETE CASCADE,
    FOREIGN KEY (contractId) REFERENCES contracts(id) ON DELETE CASCADE,
    UNIQUE KEY unique_intent_req_contract (intentId, requirementId, contractId),
    INDEX idx_contract_status (contractId, complianceStatus),
    INDEX idx_intent_relevance (intentId, relevanceScore),
    INDEX idx_requirement (requirementId),
    INDEX idx_risk_score (riskScore DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
""")

# 4. ContractComplianceAnalysis
print('Creating contract_compliance_analysis table...')
cursor.execute("""
CREATE TABLE IF NOT EXISTS contract_compliance_analysis (
    id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL PRIMARY KEY,
    contractId CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL UNIQUE,
    overallComplianceScore FLOAT NOT NULL DEFAULT 0.0,
    totalRequirementsChecked INT NOT NULL DEFAULT 0,
    compliantCount INT NOT NULL DEFAULT 0,
    partialCount INT NOT NULL DEFAULT 0,
    nonCompliantCount INT NOT NULL DEFAULT 0,
    frameworkScores JSON,
    complianceRiskScore FLOAT NOT NULL DEFAULT 0.0,
    criticalViolations INT NOT NULL DEFAULT 0,
    highViolations INT NOT NULL DEFAULT 0,
    mediumViolations INT NOT NULL DEFAULT 0,
    lowViolations INT NOT NULL DEFAULT 0,
    analysisCompletedAt DATETIME,
    analysisDurationSeconds FLOAT NOT NULL DEFAULT 0.0,
    createdAt DATETIME NOT NULL,
    updatedAt DATETIME NOT NULL,
    FOREIGN KEY (contractId) REFERENCES contracts(id) ON DELETE CASCADE,
    INDEX idx_compliance_score (overallComplianceScore),
    INDEX idx_risk_score (complianceRiskScore),
    INDEX idx_critical_violations (criticalViolations)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
""")

# Re-enable FK checks
cursor.execute('SET FOREIGN_KEY_CHECKS=1;')

conn.commit()
cursor.close()
conn.close()

print('\n[OK] All compliance tables created successfully!')
print('Now run: python manage.py migrate core 0016 --fake')
