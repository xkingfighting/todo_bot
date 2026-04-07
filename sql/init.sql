CREATE DATABASE IF NOT EXISTS `todo_bot` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE `todo_bot`;

CREATE TABLE IF NOT EXISTS `todos` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `user_id` INT NOT NULL COMMENT 'TalkOnly user id',
    `chat_id` INT NOT NULL COMMENT 'Chat id (user_id for private, group_id for group)',
    `chat_type` VARCHAR(10) NOT NULL DEFAULT 'private',
    `title` VARCHAR(500) NOT NULL,
    `description` TEXT DEFAULT NULL,
    `priority` TINYINT NOT NULL DEFAULT 2 COMMENT '1=high, 2=medium, 3=low',
    `due_date` DATE DEFAULT NULL,
    `status` TINYINT NOT NULL DEFAULT 0 COMMENT '0=pending, 1=completed',
    `completed_at` INT DEFAULT NULL,
    `created_at` INT NOT NULL DEFAULT 0,
    `updated_at` INT NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    KEY `idx_user_status` (`user_id`, `status`),
    KEY `idx_chat` (`chat_id`, `chat_type`),
    KEY `idx_due_date` (`due_date`),
    KEY `idx_user_chat` (`user_id`, `chat_id`, `chat_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
