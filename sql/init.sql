CREATE DATABASE IF NOT EXISTS `todo_bot` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `todo_bot`;

CREATE TABLE IF NOT EXISTS `todos` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `user_id` INT NOT NULL,
    `chat_id` INT NOT NULL,
    `chat_type` VARCHAR(10) NOT NULL DEFAULT 'private',
    `title` VARCHAR(500) NOT NULL,
    `description` TEXT DEFAULT NULL,
    `priority` TINYINT NOT NULL DEFAULT 2,
    `due_date` DATE DEFAULT NULL,
    `tags` VARCHAR(500) NOT NULL DEFAULT '',
    `repeat_rule` VARCHAR(20) NOT NULL DEFAULT '',
    `assignee_id` INT NOT NULL DEFAULT 0,
    `assignee_name` VARCHAR(100) NOT NULL DEFAULT '',
    `reminder_sent` TINYINT NOT NULL DEFAULT 0,
    `parent_id` INT UNSIGNED NOT NULL DEFAULT 0,
    `project_id` INT UNSIGNED NOT NULL DEFAULT 0,
    `starred` TINYINT NOT NULL DEFAULT 0,
    `due_time` VARCHAR(5) NOT NULL DEFAULT '',
    `snooze_until` INT NOT NULL DEFAULT 0,
    `status` TINYINT NOT NULL DEFAULT 0,
    `completed_at` INT DEFAULT NULL,
    `created_at` INT NOT NULL DEFAULT 0,
    `updated_at` INT NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    KEY `idx_user_status` (`user_id`, `status`),
    KEY `idx_chat` (`chat_id`, `chat_type`),
    KEY `idx_due_date` (`due_date`),
    KEY `idx_user_chat` (`user_id`, `chat_id`, `chat_type`),
    KEY `idx_assignee` (`assignee_id`),
    KEY `idx_parent` (`parent_id`),
    KEY `idx_project` (`project_id`),
    KEY `idx_starred` (`user_id`, `starred`),
    KEY `idx_tags` (`tags`(100)),
    FULLTEXT KEY `ft_title` (`title`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `user_prefs` (
    `user_id` INT NOT NULL,
    `language` VARCHAR(5) NOT NULL DEFAULT 'auto',
    `daily_summary` TINYINT NOT NULL DEFAULT 1,
    `reminder_minutes` INT NOT NULL DEFAULT 60,
    `first_use` TINYINT NOT NULL DEFAULT 1,
    `created_at` INT NOT NULL DEFAULT 0,
    PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `projects` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `user_id` INT NOT NULL,
    `chat_id` INT NOT NULL DEFAULT 0,
    `chat_type` VARCHAR(10) NOT NULL DEFAULT 'private',
    `name` VARCHAR(200) NOT NULL,
    `emoji` VARCHAR(10) NOT NULL DEFAULT '',
    `created_at` INT NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    KEY `idx_user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `activity_log` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `chat_id` INT NOT NULL,
    `chat_type` VARCHAR(10) NOT NULL DEFAULT 'group',
    `user_id` INT NOT NULL,
    `user_name` VARCHAR(100) NOT NULL DEFAULT '',
    `action` VARCHAR(30) NOT NULL,
    `todo_id` INT UNSIGNED NOT NULL DEFAULT 0,
    `detail` VARCHAR(500) NOT NULL DEFAULT '',
    `created_at` INT NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    KEY `idx_chat` (`chat_id`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
