-- ============================================================================
-- DevDiary Database Schema (schema.sql)
-- Import this SQL file into your cloud MySQL database (e.g. phpMyAdmin, TiDB, etc.)
-- ============================================================================

CREATE DATABASE IF NOT EXISTS `devdiary_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `devdiary_db`;

-- ----------------------------------------------------------------------------
-- 1. Table: posts
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `posts` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `title` VARCHAR(255) NOT NULL,
  `category` VARCHAR(100) NOT NULL,
  `content` LONGTEXT NOT NULL,
  `image` VARCHAR(255) DEFAULT 'blog1.jpg',
  `likes` INT DEFAULT 0,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- 2. Table: comments
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `comments` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `post_id` INT NOT NULL,
  `name` VARCHAR(100) NOT NULL,
  `email` VARCHAR(150) NOT NULL,
  `comment` TEXT NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `post_id_idx` (`post_id`),
  CONSTRAINT `fk_comments_posts` FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- 3. Table: messages (Contact Form)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `messages` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL,
  `email` VARCHAR(150) NOT NULL,
  `subject` VARCHAR(200) NOT NULL,
  `message` TEXT NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- 4. Table: subscribers (Newsletter)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `subscribers` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `email` VARCHAR(150) NOT NULL UNIQUE,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- 5. Table: admin (Admin Authentication)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `admin` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(100) NOT NULL UNIQUE,
  `password` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- Sample Initial Admin Account (Change password after first login)
-- Username: admin
-- Password: adminpassword123
-- ----------------------------------------------------------------------------
INSERT INTO `admin` (`username`, `password`) 
SELECT 'admin', 'adminpassword123'
WHERE NOT EXISTS (SELECT 1 FROM `admin` WHERE `username` = 'admin');

-- ----------------------------------------------------------------------------
-- Sample Initial Post (To get started immediately)
-- ----------------------------------------------------------------------------
INSERT INTO `posts` (`title`, `category`, `content`, `image`, `likes`) 
SELECT 'Welcome to DevDiary! Your First Article', 'Web Development', '<p>Welcome to <strong>DevDiary</strong>! This is your first published article. You can edit or remove this post anytime from the admin dashboard.</p><p>Explore categories, read comments, and share your tech insights with the developer community.</p>', 'blog1.jpg', 1
WHERE NOT EXISTS (SELECT 1 FROM `posts` WHERE `id` = 1);

