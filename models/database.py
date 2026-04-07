"""Database and Redis connection management."""

import logging

import mysql.connector
from mysql.connector import pooling
import redis

from config.settings import settings

logger = logging.getLogger(__name__)

_pool = None
_redis_client = None


def get_db_pool() -> pooling.MySQLConnectionPool:
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="todo_bot_pool",
            pool_size=5,
            host=settings.MYSQL_HOST,
            port=settings.MYSQL_PORT,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            database=settings.MYSQL_DATABASE,
            charset="utf8mb4",
            collation="utf8mb4_unicode_ci",
            autocommit=True,
        )
        logger.info("MySQL connection pool created.")
    return _pool


def get_db():
    """Get a connection from the pool."""
    return get_db_pool().get_connection()


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            decode_responses=True,
        )
        _redis_client.ping()
        logger.info("Redis connected.")
    return _redis_client


def init_database():
    """Create database and tables if not exist."""
    conn = mysql.connector.connect(
        host=settings.MYSQL_HOST,
        port=settings.MYSQL_PORT,
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD,
        charset="utf8mb4",
    )
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{settings.MYSQL_DATABASE}` "
                   "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    cursor.execute(f"USE `{settings.MYSQL_DATABASE}`")

    # Main todos table
    cursor.execute("""
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
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # User preferences table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `user_prefs` (
            `user_id` INT NOT NULL,
            `language` VARCHAR(5) NOT NULL DEFAULT 'auto',
            `daily_summary` TINYINT NOT NULL DEFAULT 1 COMMENT '1=enabled',
            `reminder_minutes` INT NOT NULL DEFAULT 60 COMMENT 'Minutes before due to remind',
            `first_use` TINYINT NOT NULL DEFAULT 1 COMMENT '1=first time user',
            `created_at` INT NOT NULL DEFAULT 0,
            PRIMARY KEY (`user_id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # Migrate existing todos table if needed
    try:
        cursor.execute("ALTER TABLE `todos` ADD COLUMN `tags` VARCHAR(500) NOT NULL DEFAULT '' COMMENT 'Comma-separated tags'")
    except mysql.connector.Error:
        pass
    try:
        cursor.execute("ALTER TABLE `todos` ADD COLUMN `repeat_rule` VARCHAR(20) NOT NULL DEFAULT ''")
    except mysql.connector.Error:
        pass
    try:
        cursor.execute("ALTER TABLE `todos` ADD COLUMN `assignee_id` INT NOT NULL DEFAULT 0")
    except mysql.connector.Error:
        pass
    try:
        cursor.execute("ALTER TABLE `todos` ADD COLUMN `assignee_name` VARCHAR(100) NOT NULL DEFAULT ''")
    except mysql.connector.Error:
        pass
    try:
        cursor.execute("ALTER TABLE `todos` ADD COLUMN `reminder_sent` TINYINT NOT NULL DEFAULT 0")
    except mysql.connector.Error:
        pass
    try:
        cursor.execute("ALTER TABLE `todos` ADD FULLTEXT KEY `ft_title` (`title`)")
    except mysql.connector.Error:
        pass

    cursor.close()
    conn.close()
    logger.info("Database initialized.")
