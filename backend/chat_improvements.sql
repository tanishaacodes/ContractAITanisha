-- ============================================
-- AI Chat Improvements - Database Schema
-- Features: Conversation History, Caching, Analytics
-- ============================================

-- 1. Chat Conversations Table
CREATE TABLE IF NOT EXISTS `chat_conversations` (
  `id` CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL PRIMARY KEY,
  `userId` CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `title` VARCHAR(500) DEFAULT 'New Conversation',
  `lastMessageAt` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `createdAt` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updatedAt` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_user_conversations` (`userId`, `lastMessageAt` DESC),
  FOREIGN KEY (`userId`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Chat Messages Table
CREATE TABLE IF NOT EXISTS `chat_messages` (
  `id` CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL PRIMARY KEY,
  `conversationId` CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `role` ENUM('user', 'assistant') NOT NULL,
  `content` LONGTEXT NOT NULL,
  `sources` JSON DEFAULT NULL,
  `metadata` JSON DEFAULT NULL,
  `pageNumbers` JSON DEFAULT NULL,
  `contractIds` JSON DEFAULT NULL,
  `createdAt` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_conversation_messages` (`conversationId`, `createdAt` ASC),
  FOREIGN KEY (`conversationId`) REFERENCES `chat_conversations`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Chat Cache Table (for faster responses)
CREATE TABLE IF NOT EXISTS `chat_cache` (
  `id` CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL PRIMARY KEY,
  `queryHash` VARCHAR(64) NOT NULL UNIQUE,
  `query` TEXT NOT NULL,
  `response` LONGTEXT NOT NULL,
  `sources` JSON DEFAULT NULL,
  `pageNumbers` JSON DEFAULT NULL,
  `contractIds` JSON DEFAULT NULL,
  `hitCount` INT DEFAULT 1,
  `createdAt` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `expiresAt` DATETIME DEFAULT NULL,
  `lastAccessedAt` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_query_hash` (`queryHash`),
  INDEX `idx_expires` (`expiresAt`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Chat Analytics Table
CREATE TABLE IF NOT EXISTS `chat_analytics` (
  `id` CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL PRIMARY KEY,
  `userId` CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `query` TEXT NOT NULL,
  `contractId` CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `responseTime` INT DEFAULT NULL COMMENT 'Response time in milliseconds',
  `wasCached` TINYINT(1) DEFAULT 0,
  `timestamp` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_user_analytics` (`userId`, `timestamp` DESC),
  INDEX `idx_contract_analytics` (`contractId`, `timestamp` DESC),
  FOREIGN KEY (`userId`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`contractId`) REFERENCES `contracts`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Suggested Questions Table
CREATE TABLE IF NOT EXISTS `suggested_questions` (
  `id` CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL PRIMARY KEY,
  `contractType` VARCHAR(100) DEFAULT 'General',
  `question` VARCHAR(500) NOT NULL,
  `category` VARCHAR(50) DEFAULT NULL COMMENT 'e.g., payment, termination, risk',
  `priority` INT DEFAULT 0,
  `isActive` TINYINT(1) DEFAULT 1,
  `createdAt` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_contract_type` (`contractType`, `priority` DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Insert default suggested questions
INSERT INTO `suggested_questions` (`id`, `contractType`, `question`, `category`, `priority`) VALUES
(UUID(), 'General', 'What are the key termination clauses?', 'termination', 100),
(UUID(), 'General', 'What are the payment terms?', 'payment', 90),
(UUID(), 'General', 'Who are the parties involved?', 'parties', 80),
(UUID(), 'General', 'What is the contract duration?', 'duration', 70),
(UUID(), 'General', 'What are the renewal conditions?', 'renewal', 60),
(UUID(), 'General', 'What are the liability limitations?', 'liability', 50),
(UUID(), 'General', 'What are my obligations?', 'obligations', 40),
(UUID(), 'General', 'What are the confidentiality requirements?', 'confidentiality', 30),
(UUID(), 'General', 'What are the penalties for breach?', 'penalties', 20),
(UUID(), 'General', 'What are the dispute resolution mechanisms?', 'dispute', 10);

-- Indexes for performance (already created in table definitions above)
-- Additional indexes if needed can be added here
