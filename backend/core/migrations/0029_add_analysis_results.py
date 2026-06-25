# Generated migration for Agentic AI Analysis Results
# Fixed to match exact column types and collations from contracts table

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0028_add_pricing_plans'),
    ]

    operations = [
        # Create analysis_results table with raw SQL to ensure exact type matching
        migrations.RunSQL(
            sql="""
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INT AUTO_INCREMENT PRIMARY KEY,

                    -- Foreign key to contracts - must match contracts.id exactly
                    contractId char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,

                    -- Feature 1: Executive Summary
                    executiveSummary TEXT,

                    -- Feature 2: Risk Scoring
                    riskScore INT,
                    riskLevel VARCHAR(20),
                    riskFlags JSON,

                    -- Feature 3: Clause Extraction
                    extractedClauses JSON,

                    -- Feature 4: Intent Mining & Classification
                    agentMetadata JSON,
                    primaryIntent VARCHAR(200),
                    intentConfidence FLOAT,

                    -- Feature 5: Compliance Check
                    isCompliant BOOLEAN DEFAULT TRUE,
                    complianceIssues JSON,

                    -- Agent Execution Metadata
                    agentVersion VARCHAR(50) DEFAULT '1.0',
                    toolsUsed JSON,
                    executionTimeSeconds FLOAT,

                    -- Timestamps
                    analyzedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updatedAt DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

                    -- Foreign key constraint
                    CONSTRAINT analysis_results_contractId_fk
                        FOREIGN KEY (contractId)
                        REFERENCES contracts(id)
                        ON DELETE CASCADE,

                    -- Indexes for fast querying
                    INDEX analysis_risk_idx (riskScore),
                    INDEX analysis_risk_level_idx (riskLevel),
                    INDEX analysis_intent_idx (primaryIntent),
                    INDEX analysis_date_idx (analyzedAt DESC),
                    INDEX analysis_contract_idx (contractId)

                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
            """,
            reverse_sql="DROP TABLE IF EXISTS analysis_results;"
        ),
    ]
