CREATE DATABASE `brightspace_lite` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

CREATE USER 'lite'@'172.%.0.%' IDENTIFIED BY 'brightspace_lite_password';
CREATE USER 'lite'@'192.168.%.%' IDENTIFIED BY 'brightspace_lite_password';
GRANT ALL PRIVILEGES ON `brightspace_lite`.* TO 'lite'@'172.%.0.%';
GRANT ALL PRIVILEGES ON `brightspace_lite`.* TO 'lite'@'192.168.%.%';
FLUSH PRIVILEGES;

CREATE TABLE `auth_token` (
  `client_id` varchar(255) NOT NULL,
  `token` text NOT NULL,
  `refresh_token` text NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `expires` int NOT NULL DEFAULT '0',
  `expires_at` timestamp NULL DEFAULT NULL,
  `scope` text,
  PRIMARY KEY (`client_id`)
) ENGINE=InnoDB;

CREATE TABLE `call_log` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `request` text,
  `result` longtext,
  `status` int NOT NULL DEFAULT '200',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB;

CREATE TABLE `system_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(255) NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  `password` varchar(255) DEFAULT NULL,
  `is_admin` smallint NOT NULL DEFAULT '0',
  `created_on` datetime DEFAULT CURRENT_TIMESTAMP,
  `last_login` datetime DEFAULT NULL,
  `login_count` int DEFAULT '0',
  `is_active` smallint DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_username` (`username`) /*!80000 INVISIBLE */,
  KEY `idx_active` (`is_active`) /*!80000 INVISIBLE */,
  KEY `idx_is_admin` (`is_admin`),
  KEY `idx_name` (`name`)
) ENGINE=InnoDB;
