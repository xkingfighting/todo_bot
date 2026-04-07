CREATE DATABASE IF NOT EXISTS `todo_bot` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE `todo_bot`;

CREATE TABLE IF NOT EXISTS `todos` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `user_id` INT NOT NULL COMMENT 'Creator user id',
    `chat_id` INT NOT NULL COMMENT 'Chat id',
    `chat_type` VARCHAR(10) NOT NULL DEFAULT 'private',
    `title` VARCHAR(500) NOT NULL,
    `description` TEXT DEFAULT NULL,
    `priority` TINYINT NOT NULL DEFAULT 2 COMMENT '1=high, 2=medium, 3=low',
    `due_date` DATE DEFAULT NULL,
    `tags` VARCHAR(500) NOT NULL DEFAULT '' COMMENT 'Comma-separated tags',
    `repeat_rule` VARCHAR(20) NOT NULL DEFAULT '' COMMENT 'daily|weekly|monthly or empty',
    `assignee_id` INT NOT NULL DEFAULT 0 COMMENT 'Assigned user id (group)',
    `assignee_name` VARCHAR(100) NOT NULL DEFAULT '',
    `reminder_sent` TINYINT NOT NULL DEFAULT 0 COMMENT '0=not sent, 1=sent',
    `status` TINYINT NOT NULL DEFAULT 0 COMMENT '0=pending, 1=completed',
    `completed_at` INT DEFAULT NULL,
    `created_at` INT NOT NULL DEFAULT 0,
    `updated_at` INT NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    KEY `idx_user_status` (`user_id`, `status`),
    KEY `idx_chat` (`chat_id`, `chat_type`),
    KEY `idx_due_date` (`due_date`),
    KEY `idx_user_chat` (`user_id`, `chat_id`, `chat_type`),
    KEY `idx_assignee` (`assignee_id`),
    KEY `idx_tags` (`tags`(100)),
    FULLTEXT KEY `ft_title` (`title`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `user_prefs` (
    `user_id` INT NOT NULL,
    `language` VARCHAR(5) NOT NULL DEFAULT 'auto',
    `daily_summary` TINYINT NOT NULL DEFAULT 1 COMMENT '1=enabled',
    `reminder_minutes` INT NOT NULL DEFAULT 60 COMMENT 'Minutes before due to remind',
    `first_use` TINYINT NOT NULL DEFAULT 1 COMMENT '1=first time user',
    `created_at` INT NOT NULL DEFAULT 0,
    PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
