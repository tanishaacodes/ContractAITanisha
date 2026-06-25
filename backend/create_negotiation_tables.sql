-- Create negotiation tables manually
CREATE TABLE IF NOT EXISTS `counterparties` (
    `id` varchar(36) NOT NULL PRIMARY KEY,
    `name` varchar(255) NOT NULL UNIQUE,
    `industry` varchar(100) NULL,
    `risk_profile` double NOT NULL DEFAULT 0.5,
    `aggressiveness_score` double NOT NULL DEFAULT 0.5,
    `createdAt` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updatedAt` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `negotiation_history` (
    `id` varchar(36) NOT NULL PRIMARY KEY,
    `counterpartyId` varchar(36) NOT NULL,
    `clauseType` varchar(100) NOT NULL,
    `clauseText` longtext NOT NULL,
    `deviationScore` double NOT NULL DEFAULT 0.0,
    `accepted` tinyint(1) NOT NULL DEFAULT 0,
    `redlineRounds` int NOT NULL DEFAULT 0,
    `stalled` tinyint(1) NOT NULL DEFAULT 0,
    `createdAt` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    FOREIGN KEY (`counterpartyId`) REFERENCES `counterparties` (`id`) ON DELETE CASCADE,
    INDEX `negot_hist_counterparty_idx` (`counterpartyId`, `clauseType`),
    INDEX `negot_hist_accepted_idx` (`accepted`),
    INDEX `negot_hist_stalled_idx` (`stalled`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `counterparty_behavior_snapshots` (
    `id` varchar(36) NOT NULL PRIMARY KEY,
    `counterpartyId` varchar(36) NOT NULL,
    `avgAcceptanceRate` double NOT NULL,
    `avgRedlineRounds` double NOT NULL,
    `stallRate` double NOT NULL,
    `aggressivenessScore` double NOT NULL,
    `elasticityScore` double NOT NULL,
    `snapshotDate` date NOT NULL DEFAULT (CURRENT_DATE),
    FOREIGN KEY (`counterpartyId`) REFERENCES `counterparties` (`id`) ON DELETE CASCADE,
    INDEX `behavior_snapshot_cp_date_idx` (`counterpartyId`, `snapshotDate`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `contract_negotiations` (
    `id` varchar(36) NOT NULL PRIMARY KEY,
    `contractId` varchar(36) NULL,
    `counterpartyId` varchar(36) NOT NULL,
    `contractName` varchar(255) NOT NULL,
    `status` varchar(50) NOT NULL DEFAULT 'SIMULATED',
    `totalRounds` int NOT NULL DEFAULT 0,
    `stallProbability` double NOT NULL DEFAULT 0.0,
    `createdAt` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updatedAt` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    FOREIGN KEY (`counterpartyId`) REFERENCES `counterparties` (`id`) ON DELETE CASCADE,
    INDEX `contract_negot_cp_status_idx` (`counterpartyId`, `status`),
    INDEX `contract_negot_status_idx` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `negotiation_clause_states` (
    `id` varchar(36) NOT NULL PRIMARY KEY,
    `negotiationId` varchar(36) NOT NULL,
    `clauseType` varchar(100) NOT NULL,
    `proposedText` longtext NOT NULL,
    `accepted` tinyint(1) NOT NULL DEFAULT 0,
    `roundNumber` int NOT NULL DEFAULT 0,
    `acceptanceProbability` double NOT NULL DEFAULT 0.0,
    `stallRisk` double NOT NULL DEFAULT 0.0,
    `expectedRedlines` int NOT NULL DEFAULT 0,
    `createdAt` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    FOREIGN KEY (`negotiationId`) REFERENCES `contract_negotiations` (`id`) ON DELETE CASCADE,
    INDEX `clause_state_negot_round_idx` (`negotiationId`, `roundNumber`),
    INDEX `clause_state_accepted_idx` (`accepted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `silent_risks` (
    `id` varchar(36) NOT NULL PRIMARY KEY,
    `contractId` varchar(36) NOT NULL,
    `riskType` varchar(100) NOT NULL,
    `description` longtext NOT NULL,
    `clausePair` json NOT NULL,
    `financialExposure` double NOT NULL,
    `confidence` double NOT NULL DEFAULT 0.0,
    `severity` varchar(20) NOT NULL DEFAULT 'MEDIUM',
    `detectedAt` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    INDEX `silent_risk_contract_type_idx` (`contractId`, `riskType`),
    INDEX `silent_risk_severity_idx` (`severity`),
    INDEX `silent_risk_confidence_idx` (`confidence`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `clause_interaction_patterns` (
    `id` varchar(36) NOT NULL PRIMARY KEY,
    `clauseTypes` json NOT NULL,
    `riskType` varchar(100) NOT NULL,
    `patternDescription` longtext NOT NULL,
    `impactMultiplier` double NOT NULL DEFAULT 0.3,
    `vectorEmbedding` json NULL,
    `isActive` tinyint(1) NOT NULL DEFAULT 1,
    `createdAt` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `negotiation_predictions` (
    `id` varchar(36) NOT NULL PRIMARY KEY,
    `contractId` varchar(36) NULL,
    `counterpartyId` varchar(36) NOT NULL,
    `clauseType` varchar(100) NOT NULL,
    `clauseText` longtext NOT NULL,
    `acceptanceProbability` double NOT NULL,
    `expectedRedlines` int NOT NULL,
    `stallRisk` double NOT NULL,
    `actualAccepted` tinyint(1) NULL,
    `actualRedlines` int NULL,
    `predictionDate` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    FOREIGN KEY (`counterpartyId`) REFERENCES `counterparties` (`id`) ON DELETE CASCADE,
    INDEX `negot_pred_cp_clause_idx` (`counterpartyId`, `clauseType`),
    INDEX `negot_pred_date_idx` (`predictionDate`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
