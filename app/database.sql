CREATE DATABASE `brightspace_lite`;

CREATE USER 'lite'@'172.%.0.%' IDENTIFIED BY 'brightspace_lite_password';
CREATE USER 'lite'@'192.168.%.%' IDENTIFIED BY 'brightspace_lite_password';
GRANT ALL PRIVILEGES ON `brightspace_lite`.* TO 'lite'@'172.%.0.%';
GRANT ALL PRIVILEGES ON `brightspace_lite`.* TO 'lite'@'192.168.%.%';
FLUSH PRIVILEGES;

CREATE TABLE `brightspace_lite`.`system_user` (
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
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB;
