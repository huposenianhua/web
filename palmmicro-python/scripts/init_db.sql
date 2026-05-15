-- Palmmicro 数据库初始化脚本
-- MySQL 8.0+ 或 MariaDB 10.6+

-- 创建数据库
CREATE DATABASE IF NOT EXISTS `palmmicro` 
DEFAULT CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE `palmmicro`;

-- ============================================
-- 股票基础表
-- ============================================

CREATE TABLE IF NOT EXISTS `stock` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `symbol` VARCHAR(64) NOT NULL UNIQUE,
    `name` VARCHAR(256),
    `market` VARCHAR(32),
    `type` VARCHAR(32),
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_symbol (`symbol`),
    INDEX idx_market (`market`)
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- ============================================
-- 市场数据表
-- ============================================

CREATE TABLE IF NOT EXISTS `dailystock` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `stock_id` INT UNSIGNED NOT NULL,
    `date` DATE NOT NULL,
    `open` DECIMAL(13, 6),
    `high` DECIMAL(13, 6),
    `low` DECIMAL(13, 6),
    `close` DECIMAL(13, 6),
    `volume` BIGINT UNSIGNED,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_date (`stock_id`, `date`),
    INDEX idx_date (`date`),
    FOREIGN KEY (`stock_id`) REFERENCES `stock`(`id`) ON DELETE CASCADE
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `stockhistory` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `stock_id` INT UNSIGNED NOT NULL,
    `date` DATE NOT NULL,
    `close` FLOAT NOT NULL,
    `volume` BIGINT UNSIGNED NOT NULL DEFAULT 0,
    `adjclose` FLOAT NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_date (`stock_id`, `date`),
    INDEX idx_stock_date (`stock_id`, `date`),
    FOREIGN KEY (`stock_id`) REFERENCES `stock`(`id`) ON DELETE CASCADE
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `stockema50` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `stock_id` INT UNSIGNED NOT NULL,
    `date` DATE NOT NULL,
    `close` FLOAT NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_date (`stock_id`, `date`),
    FOREIGN KEY (`stock_id`) REFERENCES `stock`(`id`) ON DELETE CASCADE
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `stockema200` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `stock_id` INT UNSIGNED NOT NULL,
    `date` DATE NOT NULL,
    `close` FLOAT NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_date (`stock_id`, `date`),
    FOREIGN KEY (`stock_id`) REFERENCES `stock`(`id`) ON DELETE CASCADE
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `netvaluehistory` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `stock_id` INT UNSIGNED NOT NULL,
    `date` DATE NOT NULL,
    `close` FLOAT NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_date (`stock_id`, `date`),
    FOREIGN KEY (`stock_id`) REFERENCES `stock`(`id`) ON DELETE CASCADE
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `calibrationhistory` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `stock_id` INT UNSIGNED NOT NULL,
    `date` DATE NOT NULL,
    `close` FLOAT NOT NULL,
    `time` TIME NOT NULL,
    `num` INT UNSIGNED NOT NULL DEFAULT 1,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_date (`stock_id`, `date`),
    INDEX idx_date_time (`date`, `time`),
    FOREIGN KEY (`stock_id`) REFERENCES `stock`(`id`) ON DELETE CASCADE
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `fundposition` (
    `id` INT UNSIGNED NOT NULL PRIMARY KEY COMMENT '直接对应 stock.id',
    `close` FLOAT NOT NULL DEFAULT 1.0 COMMENT '仓位比例（0.0~1.0）',
    FOREIGN KEY (`id`) REFERENCES `stock`(`id`) ON DELETE CASCADE
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `lastcalibration` (
    `id` INT UNSIGNED NOT NULL PRIMARY KEY COMMENT '直接对应 stock.id',
    `close` FLOAT NOT NULL COMMENT '最新校准值',
    FOREIGN KEY (`id`) REFERENCES `stock`(`id`) ON DELETE CASCADE
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `futurepremium` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `stock_id` INT UNSIGNED NOT NULL,
    `date` DATE NOT NULL,
    `close` FLOAT NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_date (`stock_id`, `date`),
    FOREIGN KEY (`stock_id`) REFERENCES `stock`(`id`) ON DELETE CASCADE
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `stocksplit` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `stock_id` INT UNSIGNED NOT NULL,
    `date` DATE NOT NULL,
    `close` FLOAT NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_date (`stock_id`, `date`),
    FOREIGN KEY (`stock_id`) REFERENCES `stock`(`id`) ON DELETE CASCADE
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `stockdividend` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `stock_id` INT UNSIGNED NOT NULL,
    `date` DATE NOT NULL,
    `close` FLOAT NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_date (`stock_id`, `date`),
    FOREIGN KEY (`stock_id`) REFERENCES `stock`(`id`) ON DELETE CASCADE
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `quarterreport` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `stock_id` INT UNSIGNED NOT NULL,
    `date` DATE NOT NULL,
    `close` VARCHAR(8192) NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_date (`stock_id`, `date`),
    FOREIGN KEY (`stock_id`) REFERENCES `stock`(`id`) ON DELETE CASCADE
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `shareshistory` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `stock_id` INT UNSIGNED NOT NULL,
    `date` DATE NOT NULL,
    `close` FLOAT NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_date (`stock_id`, `date`),
    FOREIGN KEY (`stock_id`) REFERENCES `stock`(`id`) ON DELETE CASCADE
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `sharesdiff` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `stock_id` INT UNSIGNED NOT NULL,
    `date` DATE NOT NULL,
    `close` FLOAT NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_date (`stock_id`, `date`),
    FOREIGN KEY (`stock_id`) REFERENCES `stock`(`id`) ON DELETE CASCADE
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `stocktick` (
    `id` INT UNSIGNED NOT NULL PRIMARY KEY COMMENT 'IP地址的整数形式',
    `tick` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '访问计数'
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `stockhistorydate` (
    `id` INT UNSIGNED NOT NULL PRIMARY KEY COMMENT '直接对应 stock.id',
    `date` DATE NOT NULL COMMENT '历史数据最早日期',
    FOREIGN KEY (`id`) REFERENCES `stock`(`id`) ON DELETE CASCADE
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `holdingsdate` (
    `id` INT UNSIGNED NOT NULL PRIMARY KEY COMMENT '直接对应 stock.id',
    `date` DATE NOT NULL COMMENT '持仓数据最后更新日期',
    FOREIGN KEY (`id`) REFERENCES `stock`(`id`) ON DELETE CASCADE
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `dailystring` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `stock_id` INT UNSIGNED NOT NULL,
    `date` DATE NOT NULL,
    `open` VARCHAR(64),
    `high` VARCHAR(64),
    `low` VARCHAR(64),
    `close` VARCHAR(64),
    `volume` VARCHAR(64),
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_date (`stock_id`, `date`),
    FOREIGN KEY (`stock_id`) REFERENCES `stock`(`id`) ON DELETE CASCADE
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `dailytime` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `stock_id` INT UNSIGNED NOT NULL,
    `date` DATE NOT NULL,
    `time` TIME NOT NULL,
    `price` DECIMAL(13, 6),
    `volume` BIGINT UNSIGNED,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_stock_date (`stock_id`, `date`),
    FOREIGN KEY (`stock_id`) REFERENCES `stock`(`id`) ON DELETE CASCADE
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `ema5` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `stock_id` INT UNSIGNED NOT NULL,
    `date` DATE NOT NULL,
    `close` DECIMAL(13, 6),
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_date (`stock_id`, `date`),
    FOREIGN KEY (`stock_id`) REFERENCES `stock`(`id`) ON DELETE CASCADE
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `ema10` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `stock_id` INT UNSIGNED NOT NULL,
    `date` DATE NOT NULL,
    `close` DECIMAL(13, 6),
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_date (`stock_id`, `date`),
    FOREIGN KEY (`stock_id`) REFERENCES `stock`(`id`) ON DELETE CASCADE
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `ema20` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `stock_id` INT UNSIGNED NOT NULL,
    `date` DATE NOT NULL,
    `close` DECIMAL(13, 6),
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_date (`stock_id`, `date`),
    FOREIGN KEY (`stock_id`) REFERENCES `stock`(`id`) ON DELETE CASCADE
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `ema50` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `stock_id` INT UNSIGNED NOT NULL,
    `date` DATE NOT NULL,
    `close` DECIMAL(13, 6),
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_date (`stock_id`, `date`),
    FOREIGN KEY (`stock_id`) REFERENCES `stock`(`id`) ON DELETE CASCADE
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `ema200` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `stock_id` INT UNSIGNED NOT NULL,
    `date` DATE NOT NULL,
    `close` DECIMAL(13, 6),
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_date (`stock_id`, `date`),
    FOREIGN KEY (`stock_id`) REFERENCES `stock`(`id`) ON DELETE CASCADE
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `calibration` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `stock_id` INT UNSIGNED NOT NULL,
    `date` DATE NOT NULL,
    `close` DECIMAL(13, 6),
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_date (`stock_id`, `date`),
    FOREIGN KEY (`stock_id`) REFERENCES `stock`(`id`) ON DELETE CASCADE
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `netvalue` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `stock_id` INT UNSIGNED NOT NULL,
    `date` DATE NOT NULL,
    `close` DECIMAL(13, 6),
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_date (`stock_id`, `date`),
    FOREIGN KEY (`stock_id`) REFERENCES `stock`(`id`) ON DELETE CASCADE
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `fundest` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `stock_id` INT UNSIGNED NOT NULL,
    `date` DATE NOT NULL,
    `close` DECIMAL(13, 6),
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_date (`stock_id`, `date`),
    FOREIGN KEY (`stock_id`) REFERENCES `stock`(`id`) ON DELETE CASCADE
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- ============================================
-- 配对交易表
-- ============================================

CREATE TABLE IF NOT EXISTS `abpair` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `a_stock_id` INT UNSIGNED NOT NULL,
    `b_stock_id` INT UNSIGNED NOT NULL,
    `ratio` DECIMAL(13, 6),
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_a_b (`a_stock_id`, `b_stock_id`),
    FOREIGN KEY (`a_stock_id`) REFERENCES `stock`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`b_stock_id`) REFERENCES `stock`(`id`) ON DELETE CASCADE
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `ahpair` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `a_stock_id` INT UNSIGNED NOT NULL,
    `h_stock_id` INT UNSIGNED NOT NULL,
    `ratio` DECIMAL(13, 6),
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_a_h (`a_stock_id`, `h_stock_id`),
    FOREIGN KEY (`a_stock_id`) REFERENCES `stock`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`h_stock_id`) REFERENCES `stock`(`id`) ON DELETE CASCADE
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `adrpair` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `adr_stock_id` INT UNSIGNED NOT NULL,
    `h_stock_id` INT UNSIGNED NOT NULL,
    `ratio` DECIMAL(13, 6),
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_adr_h (`adr_stock_id`, `h_stock_id`),
    FOREIGN KEY (`adr_stock_id`) REFERENCES `stock`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`h_stock_id`) REFERENCES `stock`(`id`) ON DELETE CASCADE
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `fundpair` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `fund_id` INT UNSIGNED NOT NULL,
    `ref_id` INT UNSIGNED NOT NULL,
    `ratio` DECIMAL(13, 6),
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_fund_ref (`fund_id`, `ref_id`),
    FOREIGN KEY (`fund_id`) REFERENCES `stock`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`ref_id`) REFERENCES `stock`(`id`) ON DELETE CASCADE
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- ============================================
-- 交易记录表
-- ============================================

CREATE TABLE IF NOT EXISTS `member` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(64) NOT NULL UNIQUE,
    `email` VARCHAR(128),
    `password_hash` VARCHAR(256),
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_username (`username`)
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `stockgroup` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(128) NOT NULL,
    `member_id` INT UNSIGNED,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_member (`member_id`),
    FOREIGN KEY (`member_id`) REFERENCES `member`(`id`) ON DELETE SET NULL
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `stockgroupitem` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `group_id` INT UNSIGNED NOT NULL,
    `stock_id` INT UNSIGNED NOT NULL,
    `shares` INT NOT NULL DEFAULT 0,
    `cost` DECIMAL(13, 6) NOT NULL DEFAULT 0,
    `record` INT NOT NULL DEFAULT 0,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_group_stock (`group_id`, `stock_id`),
    FOREIGN KEY (`group_id`) REFERENCES `stockgroup`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`stock_id`) REFERENCES `stock`(`id`) ON DELETE CASCADE
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `stocktransaction` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `group_item_id` INT UNSIGNED NOT NULL,
    `date` DATE NOT NULL,
    `shares` INT NOT NULL,
    `price` DECIMAL(13, 6) NOT NULL,
    `fees` DECIMAL(13, 6) DEFAULT 0,
    `note` TEXT,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_group_item (`group_item_id`),
    INDEX idx_date (`date`),
    FOREIGN KEY (`group_item_id`) REFERENCES `stockgroupitem`(`id`) ON DELETE CASCADE
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- ============================================
-- 持仓数据表
-- ============================================

CREATE TABLE IF NOT EXISTS `holdings` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `fund_id` INT UNSIGNED NOT NULL,
    `stock_id` INT UNSIGNED NOT NULL,
    `ratio` DECIMAL(13, 6),
    `shares` DECIMAL(20, 6),
    `date` DATE,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_fund_stock (`fund_id`, `stock_id`),
    FOREIGN KEY (`fund_id`) REFERENCES `stock`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`stock_id`) REFERENCES `stock`(`id`) ON DELETE CASCADE
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- ============================================
-- 访问日志表
-- ============================================

CREATE TABLE IF NOT EXISTS `visitor` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `ip` VARCHAR(64) NOT NULL,
    `user_agent` VARCHAR(512),
    `path` VARCHAR(256),
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ip (`ip`),
    INDEX idx_created_at (`created_at`)
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `ipaddress` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `ip` VARCHAR(64) NOT NULL UNIQUE,
    `location` VARCHAR(256),
    `visited_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `visit_count` INT UNSIGNED DEFAULT 1,
    INDEX idx_ip (`ip`)
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `telegrambot` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `message_id` VARCHAR(64),
    `chat_id` VARCHAR(64),
    `message` TEXT,
    `response` TEXT,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_chat_id (`chat_id`),
    INDEX idx_created_at (`created_at`)
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `wechatbot` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `from_user` VARCHAR(128),
    `message` TEXT,
    `response` TEXT,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_from_user (`from_user`),
    INDEX idx_created_at (`created_at`)
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `page` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `title` VARCHAR(256) NOT NULL,
    `content` TEXT,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `pagecomment` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `page_id` INT UNSIGNED NOT NULL,
    `author` VARCHAR(128),
    `content` TEXT,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_page_id (`page_id`),
    FOREIGN KEY (`page_id`) REFERENCES `page`(`id`) ON DELETE CASCADE
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- ============================================
-- 其他辅助表
-- ============================================

CREATE TABLE IF NOT EXISTS `date` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `date` DATE NOT NULL UNIQUE,
    `year` SMALLINT,
    `month` TINYINT,
    `day` TINYINT,
    `weekday` TINYINT,
    `is_trading_day` BOOLEAN DEFAULT TRUE,
    INDEX idx_date (`date`),
    INDEX idx_year_month (`year`, `month`)
) ENGINE = INNODB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 完成
SELECT '数据库初始化完成！' AS message;
