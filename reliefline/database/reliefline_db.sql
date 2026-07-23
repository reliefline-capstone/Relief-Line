/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19-11.8.6-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: 127.0.0.1    Database: reliefline_db
-- ------------------------------------------------------
-- Server version	11.8.6-MariaDB-0+deb13u1 from Debian

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*M!100616 SET @OLD_NOTE_VERBOSITY=@@NOTE_VERBOSITY, NOTE_VERBOSITY=0 */;

--
-- Table structure for table `activity_logs`
--

DROP TABLE IF EXISTS `activity_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `activity_logs` (
  `log_id` int(11) NOT NULL AUTO_INCREMENT,
  `actor_id` int(11) DEFAULT NULL,
  `action_type` varchar(50) NOT NULL,
  `description` varchar(255) NOT NULL,
  `is_read` tinyint(1) NOT NULL DEFAULT 0,
  `office_id` int(11) DEFAULT NULL,
  `barangay_id` int(11) DEFAULT NULL,
  `allocation_id` int(11) DEFAULT NULL,
  `distribution_id` int(11) DEFAULT NULL,
  `batch_id` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `ip_address` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`log_id`),
  KEY `actor_id` (`actor_id`),
  KEY `office_id` (`office_id`),
  KEY `barangay_id` (`barangay_id`),
  KEY `fk_activity_allocation` (`allocation_id`),
  KEY `fk_activity_distribution` (`distribution_id`),
  KEY `fk_activity_batch` (`batch_id`),
  CONSTRAINT `activity_logs_ibfk_1` FOREIGN KEY (`actor_id`) REFERENCES `users` (`user_id`),
  CONSTRAINT `activity_logs_ibfk_2` FOREIGN KEY (`office_id`) REFERENCES `offices` (`office_id`),
  CONSTRAINT `activity_logs_ibfk_3` FOREIGN KEY (`barangay_id`) REFERENCES `barangays` (`barangay_id`),
  CONSTRAINT `fk_activity_allocation` FOREIGN KEY (`allocation_id`) REFERENCES `allocation_records` (`allocation_id`),
  CONSTRAINT `fk_activity_batch` FOREIGN KEY (`batch_id`) REFERENCES `relief_request_batches` (`batch_id`),
  CONSTRAINT `fk_activity_distribution` FOREIGN KEY (`distribution_id`) REFERENCES `distribution_records` (`distribution_id`)
) ENGINE=InnoDB AUTO_INCREMENT=124 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `activity_logs`
--

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `activity_logs` WRITE;
/*!40000 ALTER TABLE `activity_logs` DISABLE KEYS */;
INSERT INTO `activity_logs` VALUES
(3,2,'allocation_approved','Approved 2,300 food packs for Urdaneta City from Warehouse A',1,5,1,8,NULL,NULL,'2026-07-19 21:35:28',NULL),
(4,2,'distribution_delivered','D-2026-005 delivered to Urdaneta City, received by Aivan Flores',1,5,1,NULL,5,NULL,'2026-07-19 21:35:28',NULL),
(5,2,'allocation_approved','Approved 900 food packs for Santa Barbara from Warehouse A',1,5,15,10,NULL,NULL,'2026-07-19 21:35:28',NULL),
(6,2,'distribution_status','Distribution marked In Transit for Bactad East, Urdaneta City',1,5,2,NULL,6,NULL,'2026-07-19 21:35:28',NULL),
(7,2,'allocation_rejected','Rejected relief request from Urdaneta City: adequate stock on hand',1,5,5,18,NULL,NULL,'2026-07-19 21:35:28',NULL),
(8,2,'distribution_status','D-2026-009 marked Loaded',1,5,30,NULL,9,NULL,'2026-07-19 21:45:02',NULL),
(9,2,'distribution_status','D-2026-009 marked Dispatched',1,5,30,NULL,9,NULL,'2026-07-19 21:45:02',NULL),
(10,2,'distribution_status','D-2026-009 marked In Transit',1,5,30,NULL,9,NULL,'2026-07-19 21:45:02',NULL),
(11,2,'distribution_delivered','D-2026-009 delivered to Calasiao, received by Test Recipient',1,5,30,NULL,9,NULL,'2026-07-19 21:45:02',NULL),
(12,2,'allocation_approved','Approved 1,000 food packs for Urdaneta City from Urdaneta City Social Welfare and Development Office',1,2,3,15,NULL,NULL,'2026-07-20 02:52:05',NULL),
(13,4,'relief_request_submitted','Santa Barbara Municipal Social Welfare and Development Office submitted RR-2026-008 to PSWDO — 400 food packs across 1 barangays',1,3,NULL,NULL,NULL,8,'2026-07-20 07:02:35',NULL),
(14,2,'allocation_approved','Approved 400 food packs for Santa Barbara from Warehouse A',1,5,16,29,NULL,NULL,'2026-07-20 07:03:37',NULL),
(15,2,'distribution_status','New distribution scheduled for Bayaoas, Urdaneta City — 1,000 food packs',1,2,3,NULL,19,NULL,'2026-07-21 04:51:01',NULL),
(22,2,'distribution_status','D-2026-019 marked Loaded',1,2,3,NULL,19,NULL,'2026-07-21 05:12:58',NULL),
(28,1,'settings_updated','System Administrator updated warehouse stock thresholds',1,NULL,NULL,NULL,NULL,NULL,'2026-07-20 22:23:26',NULL),
(29,1,'login','System Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-22 04:23:58','127.0.0.1'),
(30,1,'login','System Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-22 04:24:51','127.0.0.1'),
(33,1,'user_created','System Administrator created CSWDO/MSWDO Administrator account for Test User',1,2,NULL,NULL,NULL,NULL,'2026-07-22 04:26:39','127.0.0.1'),
(34,1,'user_deactivated','System Administrator deactivated the account for Test User',1,NULL,NULL,NULL,NULL,NULL,'2026-07-22 04:28:24','127.0.0.1'),
(35,1,'user_password_reset','System Administrator reset the password for Test User',1,NULL,NULL,NULL,NULL,NULL,'2026-07-22 04:28:24','127.0.0.1'),
(40,1,'user_password_reset','System Administrator reset the password for PSWDO Administrator',1,NULL,NULL,NULL,NULL,NULL,'2026-07-22 04:29:20','127.0.0.1'),
(41,2,'login','PSWDO Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-22 04:29:41','127.0.0.1'),
(42,1,'login','System Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-22 04:29:42','127.0.0.1'),
(43,1,'user_password_reset','System Administrator reset the password for Urdaneta CSWDO Admin',1,NULL,NULL,NULL,NULL,NULL,'2026-07-22 04:29:42','127.0.0.1'),
(44,3,'login','Urdaneta CSWDO Admin logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-22 04:30:27','127.0.0.1'),
(45,4,'login','Santa Barbara MSWDO Admin logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-22 04:42:44','127.0.0.1'),
(46,2,'login','PSWDO Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-22 04:44:11','127.0.0.1'),
(47,5,'login','Calasiao MSWDO Admin logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-22 04:44:33','127.0.0.1'),
(48,1,'login','System Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-22 04:44:47','127.0.0.1'),
(49,1,'login','System Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-22 05:25:49','127.0.0.1'),
(50,1,'login','System Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-22 05:30:44','127.0.0.1'),
(51,1,'login','System Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-22 05:39:00','127.0.0.1'),
(52,1,'login','System Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-22 05:39:13','127.0.0.1'),
(53,1,'login','System Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-22 05:39:33','127.0.0.1'),
(54,1,'login','System Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-22 05:50:18','127.0.0.1'),
(55,1,'login','System Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-22 05:50:37','127.0.0.1'),
(56,1,'login','System Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-22 05:51:13','127.0.0.1'),
(57,1,'login','System Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-22 05:51:26','127.0.0.1'),
(58,1,'login','System Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-22 06:34:04','127.0.0.1'),
(59,1,'login','System Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-22 06:34:28','127.0.0.1'),
(60,1,'login','System Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-22 06:37:00','127.0.0.1'),
(61,1,'login','System Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-22 06:37:36','127.0.0.1'),
(62,1,'login','System Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-22 06:38:05','127.0.0.1'),
(63,2,'login','PSWDO Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-22 06:40:38','127.0.0.1'),
(64,4,'login','Santa Barbara MSWDO Admin logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-22 06:41:32','127.0.0.1'),
(65,1,'login','System Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-22 06:41:43','127.0.0.1'),
(66,1,'login','System Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-22 06:44:26','127.0.0.1'),
(67,1,'login','System Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-22 06:45:55','127.0.0.1'),
(68,1,'login','System Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-22 06:46:24','127.0.0.1'),
(69,1,'login','System Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-22 06:51:49','127.0.0.1'),
(70,1,'login','System Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-22 06:53:21','127.0.0.1'),
(71,2,'login','PSWDO Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 03:11:04','127.0.0.1'),
(72,1,'login','System Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 03:11:59','127.0.0.1'),
(73,33,'login','Jose Reyes logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 05:10:02','127.0.0.1'),
(75,12,'login','Cecilia Manalo logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 05:13:36','127.0.0.1'),
(78,27,'login','Wilfredo Salazar logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 05:22:11','127.0.0.1'),
(79,33,'login','Jose Reyes logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 05:23:02','127.0.0.1'),
(80,11,'login','Ramon Bautista logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 05:25:46','127.0.0.1'),
(81,33,'login','Jose Reyes logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 05:25:58','127.0.0.1'),
(82,33,'login','Jose Reyes logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 06:05:46','127.0.0.1'),
(83,33,'damage_report_submitted','DR-2026-028 submitted by Brgy. Banaoang — 30 affected families',1,4,23,NULL,NULL,NULL,'2026-07-23 06:07:34',NULL),
(84,33,'damage_report_submitted','DR-2026-028 resubmitted by Brgy. Banaoang — 30 affected families',1,4,23,NULL,NULL,NULL,'2026-07-23 06:09:36',NULL),
(85,33,'login','Jose Reyes logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 06:10:28','127.0.0.1'),
(86,11,'login','Ramon Bautista logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 06:26:29','127.0.0.1'),
(87,12,'login','Cecilia Manalo logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 06:27:18','127.0.0.1'),
(88,16,'login','Rosalinda Aquino logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 06:27:18','127.0.0.1'),
(89,11,'login','Ramon Bautista logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 06:34:12','127.0.0.1'),
(90,2,'login','PSWDO Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 06:35:12','127.0.0.1'),
(91,11,'login','Ramon Bautista logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 06:35:45','127.0.0.1'),
(92,1,'login','System Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 06:37:37','127.0.0.1'),
(93,11,'login','Ramon Bautista logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 06:38:30','127.0.0.1'),
(94,2,'login','PSWDO Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 06:39:18','127.0.0.1'),
(95,11,'login','Ramon Bautista logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 06:39:39','127.0.0.1'),
(96,2,'login','PSWDO Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 06:43:41','127.0.0.1'),
(97,11,'login','Ramon Bautista logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 06:44:08','127.0.0.1'),
(98,11,'login','Ramon Bautista logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 06:58:14','127.0.0.1'),
(99,11,'login','Ramon Bautista logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 06:59:16','127.0.0.1'),
(100,2,'login','PSWDO Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 06:59:23','127.0.0.1'),
(101,11,'login','Ramon Bautista logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 07:00:36','127.0.0.1'),
(102,1,'login','System Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 07:01:23','127.0.0.1'),
(103,11,'login','Ramon Bautista logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 07:01:39','127.0.0.1'),
(104,11,'login','Ramon Bautista logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 07:13:31','127.0.0.1'),
(105,11,'login','Ramon Bautista logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 07:13:50','127.0.0.1'),
(106,2,'login','PSWDO Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 07:18:00','127.0.0.1'),
(107,11,'login','Ramon Bautista logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 07:18:11','127.0.0.1'),
(108,2,'login','PSWDO Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 07:21:07','127.0.0.1'),
(109,11,'login','Ramon Bautista logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 07:22:24','127.0.0.1'),
(110,11,'login','Ramon Bautista logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 07:26:13','127.0.0.1'),
(111,11,'login','Ramon Bautista logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 07:26:27','127.0.0.1'),
(112,11,'login','Ramon Bautista logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 07:26:51','127.0.0.1'),
(113,11,'login','Ramon Bautista logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 07:27:21','127.0.0.1'),
(114,11,'login','Ramon Bautista logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 07:36:36','127.0.0.1'),
(115,2,'login','PSWDO Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 07:39:14','127.0.0.1'),
(116,1,'login','System Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 07:41:27','127.0.0.1'),
(117,3,'login','Urdaneta CSWDO Admin logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 07:42:32','127.0.0.1'),
(118,2,'login','PSWDO Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 07:45:13','127.0.0.1'),
(119,3,'login','Urdaneta CSWDO Admin logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 07:46:23','127.0.0.1'),
(120,1,'login','System Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 07:46:34','127.0.0.1'),
(121,11,'login','Ramon Bautista logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 07:47:03','127.0.0.1'),
(122,11,'login','Ramon Bautista logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 07:47:09','127.0.0.1'),
(123,2,'login','PSWDO Administrator logged in',1,NULL,NULL,NULL,NULL,NULL,'2026-07-23 07:47:21','127.0.0.1');
/*!40000 ALTER TABLE `activity_logs` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;

--
-- Table structure for table `allocation_records`
--

DROP TABLE IF EXISTS `allocation_records`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `allocation_records` (
  `allocation_id` int(11) NOT NULL AUTO_INCREMENT,
  `barangay_id` int(11) NOT NULL,
  `office_id` int(11) NOT NULL,
  `predicted_quantity` int(11) NOT NULL DEFAULT 0,
  `allocated_quantity` int(11) NOT NULL DEFAULT 0,
  `historical_allocation` int(11) NOT NULL DEFAULT 0,
  `allocation_date` date NOT NULL,
  `disaster_event` varchar(150) DEFAULT NULL,
  `event_id` int(11) DEFAULT NULL,
  `status` enum('pending','approved','released') NOT NULL DEFAULT 'pending',
  `created_by` int(11) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `rejection_reason` text DEFAULT NULL,
  `fulfilling_office_id` int(11) DEFAULT NULL,
  `expected_delivery_date` date DEFAULT NULL,
  `remarks` text DEFAULT NULL,
  `decided_by` int(11) DEFAULT NULL,
  `batch_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`allocation_id`),
  KEY `barangay_id` (`barangay_id`),
  KEY `office_id` (`office_id`),
  KEY `created_by` (`created_by`),
  KEY `fk_alloc_event` (`event_id`),
  KEY `fk_alloc_fulfilling_office` (`fulfilling_office_id`),
  KEY `fk_alloc_decided_by` (`decided_by`),
  KEY `fk_alloc_batch` (`batch_id`),
  CONSTRAINT `allocation_records_ibfk_1` FOREIGN KEY (`barangay_id`) REFERENCES `barangays` (`barangay_id`) ON DELETE CASCADE,
  CONSTRAINT `allocation_records_ibfk_2` FOREIGN KEY (`office_id`) REFERENCES `offices` (`office_id`) ON DELETE CASCADE,
  CONSTRAINT `allocation_records_ibfk_3` FOREIGN KEY (`created_by`) REFERENCES `users` (`user_id`) ON DELETE SET NULL,
  CONSTRAINT `fk_alloc_batch` FOREIGN KEY (`batch_id`) REFERENCES `relief_request_batches` (`batch_id`) ON DELETE SET NULL,
  CONSTRAINT `fk_alloc_decided_by` FOREIGN KEY (`decided_by`) REFERENCES `users` (`user_id`),
  CONSTRAINT `fk_alloc_event` FOREIGN KEY (`event_id`) REFERENCES `disaster_events` (`event_id`),
  CONSTRAINT `fk_alloc_fulfilling_office` FOREIGN KEY (`fulfilling_office_id`) REFERENCES `offices` (`office_id`)
) ENGINE=InnoDB AUTO_INCREMENT=30 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `allocation_records`
--

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `allocation_records` WRITE;
/*!40000 ALTER TABLE `allocation_records` DISABLE KEYS */;
INSERT INTO `allocation_records` VALUES
(8,1,2,2300,2300,0,'2026-07-19',NULL,1,'approved',2,'2026-07-17 13:35:28',NULL,5,'2026-07-22',NULL,2,9),
(9,2,2,1500,1500,0,'2026-07-19',NULL,1,'approved',2,'2026-07-17 13:35:28',NULL,5,'2026-07-22',NULL,2,9),
(10,15,3,900,900,0,'2026-07-19',NULL,1,'approved',2,'2026-07-17 13:35:28',NULL,5,'2026-07-22',NULL,2,10),
(11,18,3,600,600,0,'2026-07-19',NULL,1,'approved',2,'2026-07-17 13:35:28',NULL,5,'2026-07-22',NULL,2,10),
(12,30,4,1800,1800,0,'2026-07-19',NULL,1,'approved',2,'2026-07-17 13:35:28',NULL,5,'2026-07-22',NULL,2,11),
(13,26,4,1200,1200,0,'2026-07-19',NULL,1,'approved',2,'2026-07-17 13:35:28',NULL,5,'2026-07-22',NULL,2,11),
(14,28,4,1100,1100,0,'2026-07-19',NULL,1,'approved',2,'2026-07-17 13:35:28',NULL,5,'2026-07-22',NULL,2,11),
(15,3,2,1000,1000,0,'2026-07-19',NULL,1,'approved',NULL,'2026-07-17 13:35:28',NULL,2,NULL,NULL,2,9),
(16,12,3,700,0,0,'2026-07-19',NULL,1,'pending',NULL,'2026-07-17 13:35:28',NULL,NULL,NULL,NULL,NULL,10),
(17,23,4,500,300,0,'2026-07-19',NULL,1,'approved',2,'2026-07-17 13:35:28',NULL,5,'2026-07-21',NULL,2,11),
(18,5,2,800,0,0,'2026-07-19',NULL,1,'pending',NULL,'2026-07-17 13:35:28','Municipal warehouse already has adequate stock for this barangay; redirected to Bayaoas instead.',NULL,NULL,NULL,2,9),
(19,19,3,1500,0,0,'2026-07-19',NULL,1,'pending',4,'2026-07-20 06:52:00',NULL,NULL,NULL,NULL,NULL,2),
(20,20,3,450,450,0,'2026-07-17',NULL,1,'approved',4,'2026-07-20 06:52:00',NULL,5,'2026-07-19',NULL,2,3),
(21,11,3,450,450,0,'2026-07-17',NULL,1,'approved',4,'2026-07-20 06:52:00',NULL,5,'2026-07-19',NULL,2,3),
(22,14,3,361,0,0,'2026-07-16',NULL,1,'pending',4,'2026-07-20 06:52:00','Insufficient damage report documentation. Please resubmit with complete barangay verification.',NULL,NULL,NULL,2,4),
(23,17,3,339,0,0,'2026-07-16',NULL,1,'pending',4,'2026-07-20 06:52:00','Insufficient damage report documentation. Please resubmit with complete barangay verification.',NULL,NULL,NULL,2,4),
(24,13,3,383,383,0,'2025-06-25',NULL,2,'approved',4,'2026-07-20 06:52:00',NULL,5,'2025-06-27',NULL,2,5),
(25,16,3,517,517,0,'2025-06-25',NULL,2,'approved',4,'2026-07-20 06:52:00',NULL,5,'2025-06-27',NULL,2,5),
(26,12,3,360,360,0,'2025-05-16',NULL,3,'approved',4,'2026-07-20 06:52:00',NULL,5,'2025-05-18',NULL,2,6),
(27,18,3,377,377,0,'2025-05-16',NULL,3,'approved',4,'2026-07-20 06:52:00',NULL,5,'2025-05-18',NULL,2,6),
(28,15,3,463,463,0,'2025-05-16',NULL,3,'approved',4,'2026-07-20 06:52:00',NULL,5,'2025-05-18',NULL,2,6),
(29,16,3,400,400,0,'2026-07-20',NULL,1,'approved',4,'2026-07-20 07:02:35',NULL,5,NULL,'Approved via test',2,8);
/*!40000 ALTER TABLE `allocation_records` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;

--
-- Table structure for table `barangay_disaster_status`
--

DROP TABLE IF EXISTS `barangay_disaster_status`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `barangay_disaster_status` (
  `status_id` int(11) NOT NULL AUTO_INCREMENT,
  `event_id` int(11) NOT NULL,
  `barangay_id` int(11) NOT NULL,
  `status` enum('normal','monitoring','needs_assistance','high_priority') DEFAULT 'normal',
  `affected_families` int(11) NOT NULL DEFAULT 0,
  `updated_by` int(11) DEFAULT NULL,
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`status_id`),
  UNIQUE KEY `unique_event_barangay` (`event_id`,`barangay_id`),
  KEY `barangay_id` (`barangay_id`),
  KEY `updated_by` (`updated_by`),
  CONSTRAINT `barangay_disaster_status_ibfk_1` FOREIGN KEY (`event_id`) REFERENCES `disaster_events` (`event_id`) ON DELETE CASCADE,
  CONSTRAINT `barangay_disaster_status_ibfk_2` FOREIGN KEY (`barangay_id`) REFERENCES `barangays` (`barangay_id`) ON DELETE CASCADE,
  CONSTRAINT `barangay_disaster_status_ibfk_3` FOREIGN KEY (`updated_by`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `barangay_disaster_status`
--

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `barangay_disaster_status` WRITE;
/*!40000 ALTER TABLE `barangay_disaster_status` DISABLE KEYS */;
INSERT INTO `barangay_disaster_status` VALUES
(1,1,1,'high_priority',1200,2,'2026-07-17 05:35:28'),
(2,1,2,'needs_assistance',800,2,'2026-07-17 05:35:28'),
(3,1,3,'monitoring',400,2,'2026-07-17 05:35:28'),
(4,1,5,'needs_assistance',600,2,'2026-07-17 05:35:28'),
(5,1,15,'high_priority',900,2,'2026-07-17 05:35:28'),
(6,1,18,'needs_assistance',600,2,'2026-07-17 05:35:28'),
(7,1,12,'monitoring',300,2,'2026-07-17 05:35:28'),
(8,1,30,'high_priority',700,2,'2026-07-17 05:35:28'),
(9,1,26,'needs_assistance',500,2,'2026-07-17 05:35:28'),
(10,1,28,'monitoring',350,2,'2026-07-17 05:35:28'),
(11,1,23,'monitoring',250,2,'2026-07-17 05:35:28'),
(12,1,20,'normal',40,4,'2026-07-20 06:22:18'),
(13,1,11,'monitoring',150,4,'2026-07-20 06:30:25'),
(14,1,19,'high_priority',340,4,'2026-07-20 06:52:00'),
(15,1,14,'needs_assistance',210,4,'2026-07-20 06:52:00'),
(16,1,17,'needs_assistance',175,4,'2026-07-20 06:52:00'),
(17,1,16,'normal',80,4,'2026-07-20 07:02:16');
/*!40000 ALTER TABLE `barangay_disaster_status` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;

--
-- Table structure for table `barangay_reports`
--

DROP TABLE IF EXISTS `barangay_reports`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `barangay_reports` (
  `report_id` int(11) NOT NULL AUTO_INCREMENT,
  `barangay_id` int(11) NOT NULL,
  `event_id` int(11) NOT NULL,
  `disaster_type` varchar(50) DEFAULT NULL,
  `incident_date` date DEFAULT NULL,
  `incident_time` time DEFAULT NULL,
  `submitted_by_name` varchar(150) NOT NULL,
  `submitted_by_designation` varchar(100) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `submitted_at` datetime DEFAULT NULL,
  `affected_families` int(11) DEFAULT NULL,
  `affected_individuals` int(11) DEFAULT NULL,
  `totally_damaged_houses` int(11) DEFAULT NULL,
  `partially_damaged_houses` int(11) DEFAULT NULL,
  `missing_persons` int(11) DEFAULT 0,
  `casualties_deaths` int(11) DEFAULT 0,
  `drinking_water_cases` int(11) DEFAULT 0,
  `hygiene_kits_est` int(11) DEFAULT 0,
  `blankets_est` int(11) DEFAULT 0,
  `flood_level` enum('normal','monitoring','needs_assistance','high_priority') DEFAULT NULL,
  `flood_depth_m` decimal(4,2) DEFAULT NULL,
  `remarks` text DEFAULT NULL,
  `photo_paths` varchar(500) DEFAULT NULL,
  `status` enum('draft','pending','verified','returned') DEFAULT 'draft',
  `review_remarks` text DEFAULT NULL,
  `reviewed_by` int(11) DEFAULT NULL,
  `reviewed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`report_id`),
  KEY `barangay_id` (`barangay_id`),
  KEY `event_id` (`event_id`),
  KEY `reviewed_by` (`reviewed_by`),
  CONSTRAINT `barangay_reports_ibfk_1` FOREIGN KEY (`barangay_id`) REFERENCES `barangays` (`barangay_id`),
  CONSTRAINT `barangay_reports_ibfk_2` FOREIGN KEY (`event_id`) REFERENCES `disaster_events` (`event_id`),
  CONSTRAINT `barangay_reports_ibfk_3` FOREIGN KEY (`reviewed_by`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=32 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `barangay_reports`
--

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `barangay_reports` WRITE;
/*!40000 ALTER TABLE `barangay_reports` DISABLE KEYS */;
INSERT INTO `barangay_reports` VALUES
(1,11,1,NULL,NULL,NULL,'Ricardo Manalo','Barangay Captain','2026-07-23 05:53:01','2026-07-20 03:22:18',150,600,2,5,0,0,0,0,0,'monitoring',0.30,'Light flooding along the creek. Monitoring water level.','photo_abot_1.jpg','verified','Verified via automated test.',4,'2026-07-20 06:30:25'),
(2,12,1,NULL,NULL,NULL,'Corazon Dizon','Barangay Secretary','2026-07-23 05:53:01','2026-07-20 00:22:18',300,1200,4,9,0,0,0,0,0,'monitoring',0.40,'Flooding receding. Residents advised to stay alert.','photo_ban-ao_1.jpg','verified','Consistent with barangay visit.',4,'2026-07-20 01:22:18'),
(3,13,1,NULL,NULL,NULL,'Ernesto Villar','Barangay Kagawad','2026-07-23 05:53:01','2026-07-20 04:22:18',220,880,9,14,0,0,0,0,0,'needs_assistance',0.60,'Several households still without power.','photo_batayang_1.jpg','returned','Please double-check the family count.',4,'2026-07-20 06:30:47'),
(4,15,1,NULL,NULL,NULL,'Marissa Ocampo','Barangay Captain','2026-07-23 05:53:01','2026-07-19 22:22:18',900,3600,22,31,0,0,0,0,0,'high_priority',1.10,'Critical flooding, main road impassable.','photo_calepaan_1.jpg','verified','Verified on-site. Matches CDRRMO advisory.',4,'2026-07-19 23:22:18'),
(5,16,1,NULL,NULL,NULL,'Danilo Ferrer','Barangay Secretary','2026-07-23 05:53:01','2026-07-20 01:22:18',80,320,0,3,0,0,0,0,0,'normal',0.10,'Minor debris on roadside only.','photo_carosucan_norte_1.jpg','verified','Re-verified for relief request test.',4,'2026-07-20 07:02:16'),
(6,18,1,NULL,NULL,NULL,'Teresita Bautista','Barangay Captain','2026-07-23 05:53:01','2026-07-19 23:22:18',600,2400,11,19,0,0,0,0,0,'needs_assistance',0.70,'Several families relocated to higher ground.','photo_coliling_1.jpg','verified','Verified. Data consistent with field visit.',4,'2026-07-20 00:22:18'),
(7,19,1,NULL,NULL,NULL,'Romeo Castillo','Barangay Kagawad','2026-07-23 05:53:01','2026-07-20 05:22:18',340,1360,15,20,0,0,0,0,0,'high_priority',0.90,'Rising water level near the irrigation canal.','photo_hacienda_1.jpg','verified','Verified for relief request demo.',4,'2026-07-20 06:52:00'),
(8,20,1,NULL,NULL,NULL,'Luz Aquino','Barangay Secretary','2026-07-23 05:53:01','2026-07-19 21:22:18',40,160,0,1,0,0,0,0,0,'normal',0.00,'No significant impact observed.','photo_mapolopolo_1.jpg','verified','Verified.',4,'2026-07-19 22:22:18'),
(9,1,1,NULL,NULL,NULL,'Julieta Reyes','Barangay Captain','2026-07-23 05:53:01','2026-07-19 20:22:18',1200,4800,28,40,0,0,0,0,0,'high_priority',1.30,'Critical flooding, evacuation ongoing.','photo_anonas_1.jpg','verified','Verified on-site — matches CDRRMO report.',3,'2026-07-19 21:22:18'),
(10,2,1,NULL,NULL,NULL,'Mario Corpuz','Barangay Secretary','2026-07-23 05:53:01','2026-07-19 21:22:18',800,3200,14,22,0,0,0,0,0,'needs_assistance',0.80,'Flood waters entering low-lying homes.','photo_bactad_east_1.jpg','verified','Consistent with field visit.',3,'2026-07-19 22:22:18'),
(11,3,1,NULL,NULL,NULL,'Angelita Ramos','Barangay Kagawad','2026-07-23 05:53:01','2026-07-20 04:22:18',180,720,3,6,0,0,0,0,0,'monitoring',0.30,'Water level rising slowly, monitoring situation.','photo_bayaoas_1.jpg','pending',NULL,NULL,NULL),
(12,4,1,NULL,NULL,NULL,'Feliciano Domingo','Barangay Captain','2026-07-23 05:53:01','2026-07-20 02:22:18',60,240,0,2,0,0,0,0,0,'normal',0.00,'No flooding reported, strong winds only.','photo_bolaoen_1.jpg','pending',NULL,NULL,NULL),
(13,5,1,NULL,NULL,NULL,'Yolanda Santiago','Barangay Secretary','2026-07-23 05:53:01','2026-07-19 19:22:18',600,2400,10,18,0,0,0,0,0,'needs_assistance',0.60,'Several roads temporarily flooded.','photo_cabaruan_1.jpg','verified','Verified. Redirect relief coordination noted.',3,'2026-07-19 20:22:18'),
(14,7,1,NULL,NULL,NULL,'Arnel Pascual','Barangay Kagawad','2026-07-23 05:53:01','2026-07-20 03:22:18',95,380,1,3,0,0,0,0,0,'monitoring',0.20,'Minor flooding near the barangay hall.','photo_camantiles_1.jpg','returned','Photo evidence unclear — please resubmit with a clearer shot.',3,'2026-07-20 04:22:18'),
(15,8,1,NULL,NULL,NULL,'Remedios Torres','Barangay Captain','2026-07-23 05:53:01','2026-07-20 05:22:18',260,1040,8,13,0,0,0,0,0,'needs_assistance',0.70,'Creek overflowed near residential area.','photo_casantaan_1.jpg','pending',NULL,NULL,NULL),
(16,10,1,NULL,NULL,NULL,'Benjamin Aguilar','Barangay Secretary','2026-07-23 05:53:01','2026-07-20 01:22:18',130,520,2,5,0,0,0,0,0,'monitoring',0.30,'Light flooding, situation stable.','photo_cayambanan_1.jpg','pending',NULL,NULL,NULL),
(17,21,1,NULL,NULL,NULL,'Perlita Navarro','Barangay Captain','2026-07-23 05:53:01','2026-07-20 04:22:18',140,560,2,4,0,0,0,0,0,'monitoring',0.30,'Light flooding along the main road.','photo_ambonao_1.jpg','pending',NULL,NULL,NULL),
(18,22,1,NULL,NULL,NULL,'Josefina Mendoza','Barangay Secretary','2026-07-23 05:53:01','2026-07-20 02:22:18',50,200,0,1,0,0,0,0,0,'normal',0.00,'No significant damage observed.','photo_ambuetel_1.jpg','returned','Report is missing barangay captain\'s signature — please resubmit.',5,'2026-07-20 03:22:18'),
(19,23,1,NULL,NULL,NULL,'Ramon Salvador','Barangay Kagawad','2026-07-23 05:53:01','2026-07-19 22:22:18',250,1000,3,7,0,0,0,0,0,'monitoring',0.30,'Flooding receding along riverside homes.','photo_banaoang_1.jpg','verified','Verified. Matches previous advisory.',5,'2026-07-19 23:22:18'),
(20,24,1,NULL,NULL,NULL,'Cristina Lopez','Barangay Captain','2026-07-23 05:53:01','2026-07-20 05:22:18',210,840,7,12,0,0,0,0,0,'needs_assistance',0.60,'Rising water level near the river bank.','photo_bued_1.jpg','pending',NULL,NULL,NULL),
(21,25,1,NULL,NULL,NULL,'Fernando Garcia','Barangay Secretary','2026-07-23 05:53:01','2026-07-20 00:22:18',70,280,0,2,0,0,0,0,0,'normal',0.00,'Strong winds, no flooding reported.','photo_buenlag_1.jpg','pending',NULL,NULL,NULL),
(22,26,1,NULL,NULL,NULL,'Aurora Ramirez','Barangay Kagawad','2026-07-23 05:53:01','2026-07-19 21:22:18',500,2000,9,16,0,0,0,0,0,'needs_assistance',0.60,'Several families temporarily relocated.','photo_cabilocaan_1.jpg','verified','Verified on-site.',5,'2026-07-19 22:22:18'),
(23,28,1,NULL,NULL,NULL,'Salvador Cruz','Barangay Captain','2026-07-23 05:53:01','2026-07-19 20:22:18',350,1400,4,8,0,0,0,0,0,'monitoring',0.40,'Water receding, roads passable.','photo_doyong_1.jpg','verified','Verified.',5,'2026-07-19 21:22:18'),
(24,30,1,NULL,NULL,NULL,'Herminia Flores','Barangay Secretary','2026-07-23 05:53:01','2026-07-19 18:22:18',700,2800,18,25,0,0,0,0,0,'high_priority',1.00,'Critical flooding, several households isolated.','photo_lasip_1.jpg','verified','Verified — matches CDRRMO advisory.',5,'2026-07-19 19:22:18'),
(25,14,1,NULL,NULL,NULL,'Barangay Office','Barangay Secretary','2026-07-23 05:53:01','2026-07-20 06:52:00',210,840,10,17,0,0,0,0,0,'needs_assistance',0.50,'Seeded for Relief Requests demo.','photo_bungallon_1.jpg','verified','Verified for relief request demo.',4,'2026-07-20 06:52:00'),
(26,17,1,NULL,NULL,NULL,'Barangay Office','Barangay Secretary','2026-07-23 05:53:01','2026-07-20 06:52:00',175,700,8,14,0,0,0,0,0,'needs_assistance',0.50,'Seeded for Relief Requests demo.','photo_carosucan_sur_1.jpg','verified','Verified for relief request demo.',4,'2026-07-20 06:52:00'),
(29,1,1,'Typhoon/Flood','2026-07-20','06:00:00','Ramon Bautista','Barangay Captain','2026-07-23 06:24:07','2026-07-23 06:24:07',45,180,5,10,0,0,10,15,10,'normal',1.10,'Initial report — data still being collected. Situation rapidly changing.',NULL,'draft','Please update the number of affected families with a more accurate count and attach photos of damaged areas.',NULL,'2026-07-23 06:24:07'),
(30,2,1,'Flash Flood','2026-07-21','14:30:00','Cecilia Manalo','Barangay Captain','2026-07-23 06:24:07','2026-07-23 06:24:07',28,112,1,6,0,0,6,8,5,'monitoring',0.80,'Water level rising slowly along the creek. Monitoring the situation.',NULL,'pending',NULL,NULL,NULL),
(31,6,1,'Typhoon/Flood','2026-07-21',NULL,'Rosalinda Aquino','Barangay Captain','2026-07-23 06:25:48',NULL,12,48,0,2,0,0,0,0,0,'normal',0.40,'Still gathering exact numbers from purok leaders.',NULL,'draft',NULL,NULL,NULL);
/*!40000 ALTER TABLE `barangay_reports` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;

--
-- Table structure for table `barangays`
--

DROP TABLE IF EXISTS `barangays`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `barangays` (
  `barangay_id` int(11) NOT NULL AUTO_INCREMENT,
  `barangay_name` varchar(100) NOT NULL,
  `city_municipality` varchar(100) NOT NULL,
  `population` int(11) NOT NULL DEFAULT 0,
  `num_households` int(11) NOT NULL DEFAULT 0,
  `poverty_incidence` decimal(5,2) NOT NULL DEFAULT 0.00,
  `disaster_risk_index` decimal(4,2) NOT NULL DEFAULT 0.00,
  `past_calamity_freq` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`barangay_id`)
) ENGINE=InnoDB AUTO_INCREMENT=32 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `barangays`
--

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `barangays` WRITE;
/*!40000 ALTER TABLE `barangays` DISABLE KEYS */;
INSERT INTO `barangays` VALUES
(1,'Anonas','Urdaneta City',3200,640,32.50,6.50,5),
(2,'Bactad East','Urdaneta City',4100,820,28.00,5.80,4),
(3,'Bayaoas','Urdaneta City',2800,560,40.00,7.20,7),
(4,'Bolaoen','Urdaneta City',1900,380,35.00,6.00,4),
(5,'Cabaruan','Urdaneta City',2500,500,38.50,7.80,6),
(6,'Cabuloan','Urdaneta City',3600,720,30.00,5.50,5),
(7,'Camantiles','Urdaneta City',1500,300,45.00,8.00,8),
(8,'Casantaan','Urdaneta City',2100,420,33.00,6.30,5),
(9,'Catablan','Urdaneta City',2700,540,29.50,5.90,4),
(10,'Cayambanan','Urdaneta City',1800,360,42.00,7.50,6),
(11,'Abot','Santa Barbara',1600,320,38.00,6.80,5),
(12,'Ban-ao','Santa Barbara',2200,440,31.50,5.70,4),
(13,'Batayang','Santa Barbara',1900,380,36.00,7.00,6),
(14,'Bungallon','Santa Barbara',2800,560,27.00,5.20,3),
(15,'Calepaan','Santa Barbara',1400,280,44.50,8.10,7),
(16,'Carosucan Norte','Santa Barbara',2100,420,33.50,6.40,5),
(17,'Carosucan Sur','Santa Barbara',1700,340,37.00,6.90,5),
(18,'Coliling','Santa Barbara',1300,260,46.00,8.30,8),
(19,'Hacienda','Santa Barbara',2500,500,29.00,5.60,4),
(20,'Mapolopolo','Santa Barbara',1100,220,50.00,8.80,9),
(21,'Ambonao','Calasiao',3800,760,26.00,5.10,3),
(22,'Ambuetel','Calasiao',2300,460,34.00,6.60,5),
(23,'Banaoang','Calasiao',1700,340,39.00,7.30,6),
(24,'Bued','Calasiao',4200,840,24.50,4.90,3),
(25,'Buenlag','Calasiao',2900,580,30.50,5.80,4),
(26,'Cabilocaan','Calasiao',1500,300,43.00,7.90,7),
(27,'Dinalaoan','Calasiao',2000,400,36.50,6.70,5),
(28,'Doyong','Calasiao',1800,360,41.00,7.60,6),
(29,'Gabon','Calasiao',2600,520,28.50,5.40,4),
(30,'Lasip','Calasiao',1200,240,48.00,8.50,8);
/*!40000 ALTER TABLE `barangays` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;

--
-- Table structure for table `city_demand_summary`
--

DROP TABLE IF EXISTS `city_demand_summary`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `city_demand_summary` (
  `summary_id` int(11) NOT NULL AUTO_INCREMENT,
  `city_municipality` varchar(100) NOT NULL,
  `total_barangays` int(11) NOT NULL DEFAULT 0,
  `total_projected_demand` int(11) NOT NULL DEFAULT 0,
  `total_historical_allocation` int(11) NOT NULL DEFAULT 0,
  `total_available_stock` int(11) NOT NULL DEFAULT 0,
  `demand_level` enum('low','moderate','high','critical') NOT NULL DEFAULT 'low',
  `generated_at` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`summary_id`),
  KEY `city_municipality` (`city_municipality`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `city_demand_summary`
--

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `city_demand_summary` WRITE;
/*!40000 ALTER TABLE `city_demand_summary` DISABLE KEYS */;
/*!40000 ALTER TABLE `city_demand_summary` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;

--
-- Table structure for table `daily_ops_stats`
--

DROP TABLE IF EXISTS `daily_ops_stats`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `daily_ops_stats` (
  `stat_id` int(11) NOT NULL AUTO_INCREMENT,
  `office_id` int(11) NOT NULL,
  `stat_date` date NOT NULL,
  `vehicles_active` int(11) DEFAULT 0,
  `updated_by` int(11) DEFAULT NULL,
  PRIMARY KEY (`stat_id`),
  UNIQUE KEY `unique_office_date` (`office_id`,`stat_date`),
  KEY `updated_by` (`updated_by`),
  CONSTRAINT `daily_ops_stats_ibfk_1` FOREIGN KEY (`office_id`) REFERENCES `offices` (`office_id`),
  CONSTRAINT `daily_ops_stats_ibfk_2` FOREIGN KEY (`updated_by`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `daily_ops_stats`
--

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `daily_ops_stats` WRITE;
/*!40000 ALTER TABLE `daily_ops_stats` DISABLE KEYS */;
INSERT INTO `daily_ops_stats` VALUES
(1,2,'2026-07-20',1,2),
(2,3,'2026-07-20',1,2),
(3,4,'2026-07-20',1,2);
/*!40000 ALTER TABLE `daily_ops_stats` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;

--
-- Table structure for table `disaster_events`
--

DROP TABLE IF EXISTS `disaster_events`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `disaster_events` (
  `event_id` int(11) NOT NULL AUTO_INCREMENT,
  `event_name` varchar(150) NOT NULL,
  `event_type` enum('typhoon','flood','other') DEFAULT 'typhoon',
  `status` enum('active','monitoring','ended') DEFAULT 'active',
  `weather_condition` varchar(50) DEFAULT NULL,
  `start_date` date NOT NULL,
  `end_date` date DEFAULT NULL,
  `created_by` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`event_id`),
  KEY `created_by` (`created_by`),
  CONSTRAINT `disaster_events_ibfk_1` FOREIGN KEY (`created_by`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `disaster_events`
--

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `disaster_events` WRITE;
/*!40000 ALTER TABLE `disaster_events` DISABLE KEYS */;
INSERT INTO `disaster_events` VALUES
(1,'Typhoon Crising','typhoon','active','Thunderstorm','2026-07-13',NULL,1,'2026-07-10 05:08:52'),
(2,'Typhoon Dante','typhoon','ended','Cleared','2025-06-20','2025-06-25',2,'2026-07-20 06:52:00'),
(3,'Typhoon Egay','typhoon','ended','Cleared','2025-05-11','2025-05-16',2,'2026-07-20 06:52:00');
/*!40000 ALTER TABLE `disaster_events` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;

--
-- Table structure for table `distribution_records`
--

DROP TABLE IF EXISTS `distribution_records`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `distribution_records` (
  `distribution_id` int(11) NOT NULL AUTO_INCREMENT,
  `barangay_id` int(11) NOT NULL,
  `allocation_id` int(11) NOT NULL,
  `quantity_released` int(11) NOT NULL DEFAULT 0,
  `distribution_date` date NOT NULL,
  `validation_type` enum('photo','signature') DEFAULT NULL,
  `validation_file` varchar(500) DEFAULT NULL,
  `submitted_by` int(11) DEFAULT NULL,
  `status` enum('pending','confirmed') NOT NULL DEFAULT 'pending',
  `submitted_at` datetime DEFAULT current_timestamp(),
  `vehicle_id` int(11) DEFAULT NULL,
  `driver_id` int(11) DEFAULT NULL,
  `dispatch_status` enum('preparing','loaded','dispatched','in_transit','delivered','delayed') DEFAULT 'preparing',
  `departure_time` time DEFAULT NULL,
  `expected_arrival_time` time DEFAULT NULL,
  `received_by` varchar(150) DEFAULT NULL,
  `time_received` time DEFAULT NULL,
  `condition` enum('complete','partial','damaged') DEFAULT NULL,
  `travel_time` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`distribution_id`),
  KEY `barangay_id` (`barangay_id`),
  KEY `allocation_id` (`allocation_id`),
  KEY `submitted_by` (`submitted_by`),
  KEY `fk_dist_vehicle` (`vehicle_id`),
  KEY `fk_dist_driver` (`driver_id`),
  CONSTRAINT `distribution_records_ibfk_1` FOREIGN KEY (`barangay_id`) REFERENCES `barangays` (`barangay_id`) ON DELETE CASCADE,
  CONSTRAINT `distribution_records_ibfk_2` FOREIGN KEY (`allocation_id`) REFERENCES `allocation_records` (`allocation_id`) ON DELETE CASCADE,
  CONSTRAINT `distribution_records_ibfk_3` FOREIGN KEY (`submitted_by`) REFERENCES `users` (`user_id`) ON DELETE SET NULL,
  CONSTRAINT `fk_dist_driver` FOREIGN KEY (`driver_id`) REFERENCES `drivers` (`driver_id`),
  CONSTRAINT `fk_dist_vehicle` FOREIGN KEY (`vehicle_id`) REFERENCES `vehicles` (`vehicle_id`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `distribution_records`
--

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `distribution_records` WRITE;
/*!40000 ALTER TABLE `distribution_records` DISABLE KEYS */;
INSERT INTO `distribution_records` VALUES
(5,1,8,2300,'2026-07-20',NULL,NULL,2,'confirmed','2026-07-17 13:35:28',4,4,'delivered','08:00:00','10:30:00','Aivan Flores',NULL,'complete','2 hrs 30 mins'),
(6,2,9,1500,'2026-07-20',NULL,NULL,NULL,'pending','2026-07-17 13:35:28',5,5,'in_transit','07:30:00','09:45:00',NULL,NULL,NULL,NULL),
(7,15,10,900,'2026-07-20',NULL,NULL,2,'pending','2026-07-17 13:35:28',6,6,'dispatched','09:00:00','11:15:00',NULL,NULL,NULL,NULL),
(8,18,11,600,'2026-07-20',NULL,NULL,2,'pending','2026-07-17 13:35:28',5,5,'loaded',NULL,NULL,NULL,NULL,NULL,NULL),
(9,30,12,1800,'2026-07-20','photo','delivery_receipt_test.pdf',2,'confirmed','2026-07-17 13:35:28',5,5,'delivered','13:45:02',NULL,'Test Recipient','15:15:00','complete','1 hr 45 mins'),
(10,26,13,1200,'2026-07-20',NULL,NULL,2,'pending','2026-07-17 13:35:28',NULL,NULL,'delayed',NULL,NULL,NULL,NULL,NULL,NULL),
(11,28,14,1100,'2026-07-20',NULL,NULL,2,'confirmed','2026-07-17 13:35:28',4,4,'delivered','06:45:00','09:00:00','Maria Santos',NULL,'complete','2 hrs 15 mins'),
(12,20,20,450,'2026-07-20',NULL,NULL,2,'pending','2026-07-20 06:52:00',NULL,NULL,'preparing','08:00:00','11:00:00',NULL,NULL,NULL,NULL),
(13,11,21,450,'2026-07-20',NULL,NULL,2,'pending','2026-07-20 06:52:00',NULL,NULL,'preparing','08:00:00','11:00:00',NULL,NULL,NULL,NULL),
(14,13,24,383,'2026-07-20',NULL,NULL,2,'confirmed','2026-07-20 06:52:00',NULL,NULL,'delivered','08:00:00','11:00:00','Barangay Officer',NULL,'complete',NULL),
(15,16,25,517,'2026-07-20',NULL,NULL,2,'confirmed','2026-07-20 06:52:00',NULL,NULL,'delivered','08:00:00','11:00:00','Barangay Officer',NULL,'complete',NULL),
(16,12,26,360,'2026-07-20',NULL,NULL,2,'confirmed','2026-07-20 06:52:00',NULL,NULL,'delivered','08:00:00','11:00:00','Barangay Officer',NULL,'complete',NULL),
(17,18,27,377,'2026-07-20',NULL,NULL,2,'confirmed','2026-07-20 06:52:00',NULL,NULL,'delivered','08:00:00','11:00:00','Barangay Officer',NULL,'complete',NULL),
(18,15,28,463,'2026-07-20',NULL,NULL,2,'confirmed','2026-07-20 06:52:00',NULL,NULL,'delivered','08:00:00','11:00:00','Barangay Officer',NULL,'complete',NULL),
(19,3,15,1000,'2026-07-21',NULL,NULL,2,'pending','2026-07-21 04:51:01',NULL,NULL,'loaded',NULL,NULL,NULL,NULL,NULL,NULL);
/*!40000 ALTER TABLE `distribution_records` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;

--
-- Table structure for table `drivers`
--

DROP TABLE IF EXISTS `drivers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `drivers` (
  `driver_id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `office_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`driver_id`),
  KEY `office_id` (`office_id`),
  CONSTRAINT `drivers_ibfk_1` FOREIGN KEY (`office_id`) REFERENCES `offices` (`office_id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `drivers`
--

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `drivers` WRITE;
/*!40000 ALTER TABLE `drivers` DISABLE KEYS */;
INSERT INTO `drivers` VALUES
(4,'Juan Dela Cruz',5),
(5,'Pedro Santos',5),
(6,'Mark Reyes',5);
/*!40000 ALTER TABLE `drivers` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;

--
-- Table structure for table `model_metrics`
--

DROP TABLE IF EXISTS `model_metrics`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `model_metrics` (
  `metric_id` int(11) NOT NULL AUTO_INCREMENT,
  `model_version` varchar(50) NOT NULL DEFAULT 'v1.0',
  `mae` decimal(10,4) DEFAULT NULL,
  `rmse` decimal(10,4) DEFAULT NULL,
  `mape` decimal(10,4) DEFAULT NULL,
  `r_squared` decimal(10,4) DEFAULT NULL,
  `training_samples` int(11) DEFAULT NULL,
  `trained_at` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`metric_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `model_metrics`
--

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `model_metrics` WRITE;
/*!40000 ALTER TABLE `model_metrics` DISABLE KEYS */;
INSERT INTO `model_metrics` VALUES
(1,'v3.0-linreg',699.2642,837.2097,68.3782,-1.5685,11,'2026-07-20 03:11:41'),
(2,'v4.0-linreg-6f',480.6969,587.6103,65.5822,-0.2226,22,'2026-07-21 04:06:32');
/*!40000 ALTER TABLE `model_metrics` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;

--
-- Table structure for table `offices`
--

DROP TABLE IF EXISTS `offices`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `offices` (
  `office_id` int(11) NOT NULL AUTO_INCREMENT,
  `office_name` varchar(100) NOT NULL,
  `office_type` enum('pswdo','cswdo','barangay') NOT NULL,
  `area_covered` varchar(100) NOT NULL,
  `capacity_food_pack` int(11) NOT NULL DEFAULT 20000,
  `full_address` varchar(255) DEFAULT NULL,
  `manager_name` varchar(100) DEFAULT NULL,
  `contact_number` varchar(20) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`office_id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `offices`
--

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `offices` WRITE;
/*!40000 ALTER TABLE `offices` DISABLE KEYS */;
INSERT INTO `offices` VALUES
(1,'Provincial Social Welfare and Development Office','pswdo','Province of Pangasinan',20000,NULL,NULL,NULL,NULL,1),
(2,'Urdaneta City Social Welfare and Development Office','cswdo','Urdaneta City',22000,NULL,NULL,NULL,NULL,1),
(3,'Santa Barbara Municipal Social Welfare and Development Office','cswdo','Santa Barbara',20000,NULL,NULL,NULL,NULL,1),
(4,'Calasiao Municipal Social Welfare and Development Office','cswdo','Calasiao',18000,NULL,NULL,NULL,NULL,1),
(5,'Warehouse A','pswdo','Lingayen',22000,NULL,NULL,NULL,NULL,1),
(6,'Warehouse C','pswdo','Alaminos',18000,NULL,NULL,NULL,NULL,1);
/*!40000 ALTER TABLE `offices` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;

--
-- Table structure for table `prediction_logs`
--

DROP TABLE IF EXISTS `prediction_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `prediction_logs` (
  `log_id` int(11) NOT NULL AUTO_INCREMENT,
  `barangay_id` int(11) NOT NULL,
  `predicted_quantity` int(11) NOT NULL,
  `input_snapshot` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`input_snapshot`)),
  `predicted_at` datetime DEFAULT current_timestamp(),
  `model_version` varchar(50) DEFAULT 'v1.0',
  PRIMARY KEY (`log_id`),
  KEY `barangay_id` (`barangay_id`),
  CONSTRAINT `prediction_logs_ibfk_1` FOREIGN KEY (`barangay_id`) REFERENCES `barangays` (`barangay_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1488 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `prediction_logs`
--

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `prediction_logs` WRITE;
/*!40000 ALTER TABLE `prediction_logs` DISABLE KEYS */;
INSERT INTO `prediction_logs` VALUES
(1,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-06-30 11:33:59','v1.0'),
(2,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-06-30 11:33:59','v1.0'),
(3,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-06-30 11:33:59','v1.0'),
(4,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-06-30 11:33:59','v1.0'),
(5,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-06-30 11:33:59','v1.0'),
(6,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-06-30 11:33:59','v1.0'),
(7,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-06-30 11:33:59','v1.0'),
(8,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-06-30 11:33:59','v1.0'),
(9,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-06-30 11:33:59','v1.0'),
(10,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-06-30 11:33:59','v1.0'),
(11,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-06-30 11:33:59','v1.0'),
(12,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-06-30 11:33:59','v1.0'),
(13,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-06-30 11:33:59','v1.0'),
(14,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-06-30 11:33:59','v1.0'),
(15,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-06-30 11:33:59','v1.0'),
(16,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-06-30 11:33:59','v1.0'),
(17,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-06-30 11:33:59','v1.0'),
(18,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-06-30 11:33:59','v1.0'),
(19,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-06-30 11:33:59','v1.0'),
(20,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-06-30 11:33:59','v1.0'),
(21,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-06-30 11:33:59','v1.0'),
(22,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-06-30 11:33:59','v1.0'),
(23,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-06-30 11:33:59','v1.0'),
(24,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-06-30 11:33:59','v1.0'),
(25,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-06-30 11:33:59','v1.0'),
(26,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-06-30 11:33:59','v1.0'),
(27,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-06-30 11:33:59','v1.0'),
(28,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-06-30 11:33:59','v1.0'),
(29,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-06-30 11:33:59','v1.0'),
(30,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-06-30 11:33:59','v1.0'),
(31,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-06-30 11:37:22','v1.0'),
(32,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-06-30 11:37:22','v1.0'),
(33,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-06-30 11:37:22','v1.0'),
(34,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-06-30 11:37:22','v1.0'),
(35,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-06-30 11:37:22','v1.0'),
(36,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-06-30 11:37:22','v1.0'),
(37,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-06-30 11:37:22','v1.0'),
(38,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-06-30 11:37:22','v1.0'),
(39,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-06-30 11:37:22','v1.0'),
(40,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-06-30 11:37:22','v1.0'),
(41,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-06-30 11:37:22','v1.0'),
(42,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-06-30 11:37:22','v1.0'),
(43,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-06-30 11:37:22','v1.0'),
(44,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-06-30 11:37:22','v1.0'),
(45,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-06-30 11:37:22','v1.0'),
(46,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-06-30 11:37:22','v1.0'),
(47,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-06-30 11:37:22','v1.0'),
(48,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-06-30 11:37:22','v1.0'),
(49,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-06-30 11:37:22','v1.0'),
(50,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-06-30 11:37:22','v1.0'),
(51,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-06-30 11:37:22','v1.0'),
(52,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-06-30 11:37:22','v1.0'),
(53,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-06-30 11:37:22','v1.0'),
(54,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-06-30 11:37:22','v1.0'),
(55,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-06-30 11:37:22','v1.0'),
(56,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-06-30 11:37:22','v1.0'),
(57,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-06-30 11:37:22','v1.0'),
(58,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-06-30 11:37:22','v1.0'),
(59,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-06-30 11:37:22','v1.0'),
(60,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-06-30 11:37:22','v1.0'),
(61,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 12:40:48','v1.0'),
(62,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 12:40:48','v1.0'),
(63,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 12:40:48','v1.0'),
(64,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 12:40:48','v1.0'),
(65,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 12:40:48','v1.0'),
(66,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 12:40:48','v1.0'),
(67,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 12:40:48','v1.0'),
(68,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 12:40:48','v1.0'),
(69,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 12:40:48','v1.0'),
(70,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 12:40:48','v1.0'),
(71,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 12:40:48','v1.0'),
(72,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 12:40:48','v1.0'),
(73,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 12:40:48','v1.0'),
(74,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 12:40:48','v1.0'),
(75,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 12:40:48','v1.0'),
(76,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 12:40:48','v1.0'),
(77,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 12:40:48','v1.0'),
(78,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 12:40:48','v1.0'),
(79,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 12:40:48','v1.0'),
(80,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 12:40:48','v1.0'),
(81,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 12:40:48','v1.0'),
(82,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 12:40:48','v1.0'),
(83,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 12:40:48','v1.0'),
(84,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 12:40:48','v1.0'),
(85,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 12:40:48','v1.0'),
(86,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 12:40:48','v1.0'),
(87,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 12:40:48','v1.0'),
(88,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 12:40:48','v1.0'),
(89,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 12:40:48','v1.0'),
(90,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 12:40:48','v1.0'),
(91,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 12:40:52','v1.0'),
(92,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 12:40:52','v1.0'),
(93,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 12:40:52','v1.0'),
(94,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 12:40:52','v1.0'),
(95,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 12:40:52','v1.0'),
(96,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 12:40:52','v1.0'),
(97,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 12:40:52','v1.0'),
(98,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 12:40:52','v1.0'),
(99,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 12:40:52','v1.0'),
(100,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 12:40:52','v1.0'),
(101,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 12:40:52','v1.0'),
(102,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 12:40:52','v1.0'),
(103,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 12:40:52','v1.0'),
(104,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 12:40:52','v1.0'),
(105,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 12:40:52','v1.0'),
(106,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 12:40:52','v1.0'),
(107,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 12:40:52','v1.0'),
(108,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 12:40:52','v1.0'),
(109,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 12:40:52','v1.0'),
(110,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 12:40:52','v1.0'),
(111,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 12:40:52','v1.0'),
(112,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 12:40:52','v1.0'),
(113,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 12:40:52','v1.0'),
(114,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 12:40:52','v1.0'),
(115,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 12:40:52','v1.0'),
(116,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 12:40:52','v1.0'),
(117,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 12:40:52','v1.0'),
(118,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 12:40:52','v1.0'),
(119,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 12:40:52','v1.0'),
(120,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 12:40:52','v1.0'),
(121,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 12:41:07','v1.0'),
(122,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 12:41:07','v1.0'),
(123,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 12:41:07','v1.0'),
(124,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 12:41:07','v1.0'),
(125,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 12:41:07','v1.0'),
(126,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 12:41:07','v1.0'),
(127,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 12:41:07','v1.0'),
(128,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 12:41:07','v1.0'),
(129,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 12:41:07','v1.0'),
(130,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 12:41:07','v1.0'),
(131,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 12:41:07','v1.0'),
(132,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 12:41:07','v1.0'),
(133,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 12:41:07','v1.0'),
(134,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 12:41:07','v1.0'),
(135,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 12:41:07','v1.0'),
(136,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 12:41:07','v1.0'),
(137,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 12:41:07','v1.0'),
(138,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 12:41:07','v1.0'),
(139,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 12:41:07','v1.0'),
(140,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 12:41:07','v1.0'),
(141,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 12:41:07','v1.0'),
(142,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 12:41:07','v1.0'),
(143,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 12:41:07','v1.0'),
(144,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 12:41:07','v1.0'),
(145,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 12:41:07','v1.0'),
(146,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 12:41:07','v1.0'),
(147,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 12:41:07','v1.0'),
(148,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 12:41:07','v1.0'),
(149,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 12:41:07','v1.0'),
(150,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 12:41:07','v1.0'),
(151,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 12:53:39','v1.0'),
(152,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 12:53:39','v1.0'),
(153,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 12:53:39','v1.0'),
(154,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 12:53:39','v1.0'),
(155,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 12:53:39','v1.0'),
(156,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 12:53:39','v1.0'),
(157,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 12:53:39','v1.0'),
(158,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 12:53:39','v1.0'),
(159,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 12:53:39','v1.0'),
(160,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 12:53:39','v1.0'),
(161,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 12:53:39','v1.0'),
(162,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 12:53:39','v1.0'),
(163,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 12:53:39','v1.0'),
(164,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 12:53:39','v1.0'),
(165,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 12:53:39','v1.0'),
(166,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 12:53:39','v1.0'),
(167,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 12:53:39','v1.0'),
(168,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 12:53:39','v1.0'),
(169,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 12:53:39','v1.0'),
(170,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 12:53:39','v1.0'),
(171,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 12:53:39','v1.0'),
(172,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 12:53:39','v1.0'),
(173,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 12:53:39','v1.0'),
(174,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 12:53:39','v1.0'),
(175,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 12:53:39','v1.0'),
(176,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 12:53:39','v1.0'),
(177,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 12:53:39','v1.0'),
(178,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 12:53:39','v1.0'),
(179,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 12:53:39','v1.0'),
(180,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 12:53:39','v1.0'),
(181,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:40:30','v1.0'),
(182,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:40:30','v1.0'),
(183,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:40:30','v1.0'),
(184,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:40:30','v1.0'),
(185,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:40:30','v1.0'),
(186,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:40:30','v1.0'),
(187,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:40:30','v1.0'),
(188,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:40:30','v1.0'),
(189,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:40:30','v1.0'),
(190,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:40:30','v1.0'),
(191,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:40:30','v1.0'),
(192,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:40:30','v1.0'),
(193,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:40:30','v1.0'),
(194,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:40:30','v1.0'),
(195,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:40:30','v1.0'),
(196,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:40:30','v1.0'),
(197,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:40:30','v1.0'),
(198,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:40:30','v1.0'),
(199,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:40:30','v1.0'),
(200,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 13:40:30','v1.0'),
(201,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:40:30','v1.0'),
(202,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:40:30','v1.0'),
(203,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:40:30','v1.0'),
(204,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:40:30','v1.0'),
(205,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:40:30','v1.0'),
(206,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:40:30','v1.0'),
(207,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:40:30','v1.0'),
(208,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:40:30','v1.0'),
(209,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:40:30','v1.0'),
(210,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:40:30','v1.0'),
(211,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:40:33','v1.0'),
(212,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:40:33','v1.0'),
(213,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:40:33','v1.0'),
(214,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:40:33','v1.0'),
(215,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:40:33','v1.0'),
(216,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:40:33','v1.0'),
(217,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:40:33','v1.0'),
(218,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:40:33','v1.0'),
(219,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:40:33','v1.0'),
(220,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:40:33','v1.0'),
(221,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:40:33','v1.0'),
(222,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:40:33','v1.0'),
(223,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:40:33','v1.0'),
(224,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:40:33','v1.0'),
(225,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:40:33','v1.0'),
(226,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:40:33','v1.0'),
(227,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:40:33','v1.0'),
(228,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:40:33','v1.0'),
(229,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:40:33','v1.0'),
(230,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 13:40:33','v1.0'),
(231,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:40:33','v1.0'),
(232,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:40:33','v1.0'),
(233,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:40:33','v1.0'),
(234,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:40:33','v1.0'),
(235,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:40:33','v1.0'),
(236,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:40:33','v1.0'),
(237,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:40:33','v1.0'),
(238,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:40:33','v1.0'),
(239,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:40:33','v1.0'),
(240,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:40:33','v1.0'),
(241,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:42:51','v1.0'),
(242,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:42:51','v1.0'),
(243,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:42:51','v1.0'),
(244,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:42:51','v1.0'),
(245,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:42:51','v1.0'),
(246,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:42:51','v1.0'),
(247,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:42:51','v1.0'),
(248,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:42:51','v1.0'),
(249,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:42:51','v1.0'),
(250,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:42:51','v1.0'),
(251,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:42:51','v1.0'),
(252,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:42:51','v1.0'),
(253,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:42:51','v1.0'),
(254,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:42:51','v1.0'),
(255,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:42:51','v1.0'),
(256,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:42:51','v1.0'),
(257,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:42:51','v1.0'),
(258,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:42:51','v1.0'),
(259,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:42:51','v1.0'),
(260,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 13:42:51','v1.0'),
(261,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:42:51','v1.0'),
(262,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:42:51','v1.0'),
(263,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:42:51','v1.0'),
(264,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:42:51','v1.0'),
(265,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:42:51','v1.0'),
(266,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:42:51','v1.0'),
(267,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:42:51','v1.0'),
(268,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:42:51','v1.0'),
(269,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:42:51','v1.0'),
(270,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:42:51','v1.0'),
(271,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:42:56','v1.0'),
(272,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:42:56','v1.0'),
(273,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:42:56','v1.0'),
(274,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:42:56','v1.0'),
(275,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:42:56','v1.0'),
(276,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:42:56','v1.0'),
(277,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:42:56','v1.0'),
(278,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:42:56','v1.0'),
(279,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:42:56','v1.0'),
(280,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:42:56','v1.0'),
(281,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:42:56','v1.0'),
(282,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:42:56','v1.0'),
(283,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:42:56','v1.0'),
(284,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:42:56','v1.0'),
(285,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:42:56','v1.0'),
(286,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:42:56','v1.0'),
(287,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:42:56','v1.0'),
(288,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:42:56','v1.0'),
(289,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:42:56','v1.0'),
(290,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 13:42:56','v1.0'),
(291,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:42:56','v1.0'),
(292,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:42:56','v1.0'),
(293,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:42:56','v1.0'),
(294,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:42:56','v1.0'),
(295,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:42:56','v1.0'),
(296,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:42:56','v1.0'),
(297,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:42:56','v1.0'),
(298,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:42:56','v1.0'),
(299,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:42:56','v1.0'),
(300,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:42:56','v1.0'),
(301,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:42:58','v1.0'),
(302,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:42:58','v1.0'),
(303,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:42:58','v1.0'),
(304,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:42:58','v1.0'),
(305,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:42:59','v1.0'),
(306,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:42:59','v1.0'),
(307,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:42:59','v1.0'),
(308,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:42:59','v1.0'),
(309,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:42:59','v1.0'),
(310,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:42:59','v1.0'),
(311,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:42:59','v1.0'),
(312,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:42:59','v1.0'),
(313,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:42:59','v1.0'),
(314,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:42:59','v1.0'),
(315,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:42:59','v1.0'),
(316,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:42:59','v1.0'),
(317,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:42:59','v1.0'),
(318,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:42:59','v1.0'),
(319,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:42:59','v1.0'),
(320,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 13:42:59','v1.0'),
(321,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:42:59','v1.0'),
(322,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:42:59','v1.0'),
(323,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:42:59','v1.0'),
(324,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:42:59','v1.0'),
(325,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:42:59','v1.0'),
(326,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:42:59','v1.0'),
(327,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:42:59','v1.0'),
(328,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:42:59','v1.0'),
(329,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:42:59','v1.0'),
(330,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:42:59','v1.0'),
(331,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:45:59','v1.0'),
(332,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:45:59','v1.0'),
(333,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:45:59','v1.0'),
(334,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:45:59','v1.0'),
(335,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:45:59','v1.0'),
(336,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:45:59','v1.0'),
(337,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:45:59','v1.0'),
(338,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:45:59','v1.0'),
(339,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:45:59','v1.0'),
(340,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:45:59','v1.0'),
(341,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:45:59','v1.0'),
(342,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:45:59','v1.0'),
(343,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:45:59','v1.0'),
(344,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:45:59','v1.0'),
(345,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:45:59','v1.0'),
(346,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:45:59','v1.0'),
(347,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:45:59','v1.0'),
(348,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:45:59','v1.0'),
(349,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:46:00','v1.0'),
(350,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 13:46:00','v1.0'),
(351,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:46:00','v1.0'),
(352,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:46:00','v1.0'),
(353,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:46:00','v1.0'),
(354,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:46:00','v1.0'),
(355,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:46:00','v1.0'),
(356,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:46:00','v1.0'),
(357,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:46:00','v1.0'),
(358,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:46:00','v1.0'),
(359,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:46:00','v1.0'),
(360,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:46:00','v1.0'),
(361,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:46:01','v1.0'),
(362,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:46:01','v1.0'),
(363,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:46:01','v1.0'),
(364,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:46:01','v1.0'),
(365,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:46:01','v1.0'),
(366,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:46:01','v1.0'),
(367,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:46:01','v1.0'),
(368,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:46:01','v1.0'),
(369,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:46:01','v1.0'),
(370,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:46:01','v1.0'),
(371,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:46:01','v1.0'),
(372,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:46:01','v1.0'),
(373,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:46:01','v1.0'),
(374,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:46:01','v1.0'),
(375,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:46:01','v1.0'),
(376,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:46:01','v1.0'),
(377,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:46:01','v1.0'),
(378,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:46:01','v1.0'),
(379,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:46:01','v1.0'),
(380,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 13:46:01','v1.0'),
(381,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:46:01','v1.0'),
(382,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:46:01','v1.0'),
(383,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:46:01','v1.0'),
(384,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:46:01','v1.0'),
(385,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:46:01','v1.0'),
(386,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:46:01','v1.0'),
(387,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:46:01','v1.0'),
(388,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:46:01','v1.0'),
(389,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:46:01','v1.0'),
(390,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:46:01','v1.0'),
(391,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:46:06','v1.0'),
(392,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:46:06','v1.0'),
(393,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:46:06','v1.0'),
(394,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:46:06','v1.0'),
(395,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:46:06','v1.0'),
(396,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:46:06','v1.0'),
(397,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:46:06','v1.0'),
(398,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:46:06','v1.0'),
(399,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:46:06','v1.0'),
(400,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:46:06','v1.0'),
(401,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:46:06','v1.0'),
(402,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:46:06','v1.0'),
(403,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:46:06','v1.0'),
(404,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:46:06','v1.0'),
(405,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:46:06','v1.0'),
(406,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:46:06','v1.0'),
(407,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:46:06','v1.0'),
(408,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:46:06','v1.0'),
(409,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:46:06','v1.0'),
(410,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 13:46:06','v1.0'),
(411,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:46:06','v1.0'),
(412,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:46:06','v1.0'),
(413,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:46:06','v1.0'),
(414,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:46:06','v1.0'),
(415,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:46:06','v1.0'),
(416,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:46:06','v1.0'),
(417,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:46:06','v1.0'),
(418,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:46:06','v1.0'),
(419,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:46:06','v1.0'),
(420,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:46:06','v1.0'),
(421,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:49:42','v1.0'),
(422,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:49:42','v1.0'),
(423,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:49:42','v1.0'),
(424,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:49:42','v1.0'),
(425,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:49:42','v1.0'),
(426,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:49:42','v1.0'),
(427,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:49:42','v1.0'),
(428,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:49:42','v1.0'),
(429,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:49:42','v1.0'),
(430,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:49:42','v1.0'),
(431,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:49:42','v1.0'),
(432,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:49:42','v1.0'),
(433,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:49:42','v1.0'),
(434,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:49:42','v1.0'),
(435,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:49:42','v1.0'),
(436,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:49:42','v1.0'),
(437,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:49:42','v1.0'),
(438,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:49:42','v1.0'),
(439,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:49:42','v1.0'),
(440,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 13:49:42','v1.0'),
(441,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:49:42','v1.0'),
(442,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:49:42','v1.0'),
(443,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:49:42','v1.0'),
(444,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:49:42','v1.0'),
(445,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:49:42','v1.0'),
(446,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:49:42','v1.0'),
(447,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:49:42','v1.0'),
(448,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:49:42','v1.0'),
(449,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:49:42','v1.0'),
(450,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:49:42','v1.0'),
(451,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:50:39','v1.0'),
(452,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:50:39','v1.0'),
(453,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:50:39','v1.0'),
(454,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:50:39','v1.0'),
(455,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:50:39','v1.0'),
(456,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:50:39','v1.0'),
(457,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:50:39','v1.0'),
(458,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:50:39','v1.0'),
(459,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:50:39','v1.0'),
(460,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:50:39','v1.0'),
(461,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:50:39','v1.0'),
(462,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:50:39','v1.0'),
(463,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:50:39','v1.0'),
(464,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:50:39','v1.0'),
(465,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:50:39','v1.0'),
(466,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:50:39','v1.0'),
(467,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:50:39','v1.0'),
(468,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:50:39','v1.0'),
(469,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:50:39','v1.0'),
(470,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 13:50:39','v1.0'),
(471,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:50:39','v1.0'),
(472,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:50:39','v1.0'),
(473,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:50:39','v1.0'),
(474,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:50:39','v1.0'),
(475,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:50:39','v1.0'),
(476,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:50:39','v1.0'),
(477,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:50:39','v1.0'),
(478,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:50:39','v1.0'),
(479,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:50:39','v1.0'),
(480,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:50:39','v1.0'),
(481,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:50:46','v1.0'),
(482,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:50:46','v1.0'),
(483,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:50:46','v1.0'),
(484,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:50:46','v1.0'),
(485,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:50:46','v1.0'),
(486,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:50:46','v1.0'),
(487,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:50:46','v1.0'),
(488,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:50:46','v1.0'),
(489,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:50:46','v1.0'),
(490,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:50:46','v1.0'),
(491,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:50:46','v1.0'),
(492,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:50:46','v1.0'),
(493,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:50:46','v1.0'),
(494,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:50:46','v1.0'),
(495,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:50:46','v1.0'),
(496,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:50:46','v1.0'),
(497,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:50:46','v1.0'),
(498,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:50:46','v1.0'),
(499,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:50:46','v1.0'),
(500,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 13:50:46','v1.0'),
(501,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:50:46','v1.0'),
(502,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:50:46','v1.0'),
(503,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:50:46','v1.0'),
(504,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:50:46','v1.0'),
(505,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:50:46','v1.0'),
(506,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:50:46','v1.0'),
(507,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:50:46','v1.0'),
(508,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:50:46','v1.0'),
(509,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:50:46','v1.0'),
(510,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:50:46','v1.0'),
(511,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:51:01','v1.0'),
(512,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:51:01','v1.0'),
(513,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:51:01','v1.0'),
(514,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:51:01','v1.0'),
(515,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:51:01','v1.0'),
(516,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:51:01','v1.0'),
(517,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:51:01','v1.0'),
(518,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:51:01','v1.0'),
(519,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:51:01','v1.0'),
(520,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:51:01','v1.0'),
(521,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:51:01','v1.0'),
(522,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:51:01','v1.0'),
(523,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:51:01','v1.0'),
(524,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:51:01','v1.0'),
(525,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:51:01','v1.0'),
(526,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:51:01','v1.0'),
(527,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:51:01','v1.0'),
(528,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:51:01','v1.0'),
(529,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:51:01','v1.0'),
(530,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 13:51:01','v1.0'),
(531,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:51:01','v1.0'),
(532,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:51:01','v1.0'),
(533,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:51:01','v1.0'),
(534,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:51:01','v1.0'),
(535,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:51:01','v1.0'),
(536,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:51:01','v1.0'),
(537,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:51:01','v1.0'),
(538,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:51:01','v1.0'),
(539,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:51:01','v1.0'),
(540,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:51:01','v1.0'),
(541,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:51:47','v1.0'),
(542,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:51:47','v1.0'),
(543,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:51:47','v1.0'),
(544,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:51:47','v1.0'),
(545,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:51:47','v1.0'),
(546,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:51:47','v1.0'),
(547,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:51:47','v1.0'),
(548,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:51:47','v1.0'),
(549,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:51:47','v1.0'),
(550,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:51:47','v1.0'),
(551,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:51:47','v1.0'),
(552,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:51:47','v1.0'),
(553,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:51:47','v1.0'),
(554,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:51:47','v1.0'),
(555,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:51:47','v1.0'),
(556,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:51:47','v1.0'),
(557,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:51:47','v1.0'),
(558,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:51:47','v1.0'),
(559,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:51:47','v1.0'),
(560,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 13:51:47','v1.0'),
(561,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:51:47','v1.0'),
(562,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:51:47','v1.0'),
(563,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:51:47','v1.0'),
(564,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:51:47','v1.0'),
(565,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:51:47','v1.0'),
(566,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:51:47','v1.0'),
(567,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:51:47','v1.0'),
(568,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:51:47','v1.0'),
(569,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:51:47','v1.0'),
(570,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:51:47','v1.0'),
(571,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:51:56','v1.0'),
(572,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:51:56','v1.0'),
(573,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:51:56','v1.0'),
(574,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:51:56','v1.0'),
(575,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:51:56','v1.0'),
(576,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:51:56','v1.0'),
(577,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:51:56','v1.0'),
(578,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:51:56','v1.0'),
(579,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:51:56','v1.0'),
(580,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:51:56','v1.0'),
(581,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:51:56','v1.0'),
(582,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:51:56','v1.0'),
(583,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:51:56','v1.0'),
(584,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:51:56','v1.0'),
(585,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:51:56','v1.0'),
(586,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:51:56','v1.0'),
(587,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:51:56','v1.0'),
(588,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:51:56','v1.0'),
(589,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:51:56','v1.0'),
(590,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 13:51:56','v1.0'),
(591,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:51:56','v1.0'),
(592,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:51:56','v1.0'),
(593,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:51:56','v1.0'),
(594,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:51:56','v1.0'),
(595,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:51:56','v1.0'),
(596,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:51:56','v1.0'),
(597,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:51:56','v1.0'),
(598,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:51:56','v1.0'),
(599,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:51:56','v1.0'),
(600,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:51:56','v1.0'),
(601,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:58:49','v1.0'),
(602,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:58:49','v1.0'),
(603,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:58:49','v1.0'),
(604,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:58:49','v1.0'),
(605,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:58:49','v1.0'),
(606,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:58:49','v1.0'),
(607,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:58:49','v1.0'),
(608,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:58:49','v1.0'),
(609,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:58:49','v1.0'),
(610,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:58:49','v1.0'),
(611,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:58:49','v1.0'),
(612,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:58:49','v1.0'),
(613,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:58:49','v1.0'),
(614,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:58:49','v1.0'),
(615,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:58:49','v1.0'),
(616,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:58:49','v1.0'),
(617,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:58:49','v1.0'),
(618,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:58:49','v1.0'),
(619,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:58:49','v1.0'),
(620,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 13:58:49','v1.0'),
(621,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:58:49','v1.0'),
(622,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:58:49','v1.0'),
(623,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:58:49','v1.0'),
(624,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:58:49','v1.0'),
(625,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:58:49','v1.0'),
(626,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:58:49','v1.0'),
(627,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:58:49','v1.0'),
(628,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:58:49','v1.0'),
(629,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:58:49','v1.0'),
(630,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:58:49','v1.0'),
(631,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(632,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(633,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(634,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(635,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(636,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(637,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(638,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(639,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(640,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(641,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(642,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(643,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(644,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(645,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(646,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(647,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(648,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(649,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(650,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(651,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(652,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(653,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(654,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(655,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(656,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(657,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(658,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(659,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(660,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(661,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(662,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(663,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(664,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(665,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(666,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(667,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(668,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(669,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(670,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(671,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(672,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(673,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(674,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(675,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(676,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(677,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(678,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(679,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(680,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(681,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(682,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(683,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(684,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(685,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(686,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(687,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(688,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(689,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(690,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:58:50','v1.0'),
(691,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:58:51','v1.0'),
(692,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:58:51','v1.0'),
(693,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:58:51','v1.0'),
(694,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:58:51','v1.0'),
(695,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:58:51','v1.0'),
(696,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:58:51','v1.0'),
(697,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:58:51','v1.0'),
(698,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:58:51','v1.0'),
(699,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:58:51','v1.0'),
(700,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:58:51','v1.0'),
(701,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:58:51','v1.0'),
(702,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:58:51','v1.0'),
(703,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:58:51','v1.0'),
(704,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 13:58:51','v1.0'),
(705,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:58:51','v1.0'),
(706,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:58:51','v1.0'),
(707,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:58:51','v1.0'),
(708,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:58:51','v1.0'),
(709,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:58:51','v1.0'),
(710,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 13:58:51','v1.0'),
(711,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:58:51','v1.0'),
(712,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:58:51','v1.0'),
(713,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 13:58:51','v1.0'),
(714,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:58:51','v1.0'),
(715,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:58:51','v1.0'),
(716,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:58:51','v1.0'),
(717,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 13:58:51','v1.0'),
(718,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 13:58:51','v1.0'),
(719,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 13:58:51','v1.0'),
(720,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 13:58:51','v1.0'),
(721,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:02:47','v1.0'),
(722,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:02:47','v1.0'),
(723,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:02:47','v1.0'),
(724,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:02:47','v1.0'),
(725,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:02:47','v1.0'),
(726,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:02:47','v1.0'),
(727,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:02:47','v1.0'),
(728,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:02:47','v1.0'),
(729,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:02:47','v1.0'),
(730,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:02:47','v1.0'),
(731,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:02:47','v1.0'),
(732,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:02:47','v1.0'),
(733,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:02:47','v1.0'),
(734,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:02:47','v1.0'),
(735,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:02:47','v1.0'),
(736,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:02:47','v1.0'),
(737,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:02:47','v1.0'),
(738,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:02:47','v1.0'),
(739,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:02:47','v1.0'),
(740,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 14:02:47','v1.0'),
(741,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:02:47','v1.0'),
(742,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:02:47','v1.0'),
(743,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:02:47','v1.0'),
(744,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:02:47','v1.0'),
(745,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:02:47','v1.0'),
(746,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:02:47','v1.0'),
(747,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:02:47','v1.0'),
(748,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:02:47','v1.0'),
(749,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:02:47','v1.0'),
(750,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:02:47','v1.0'),
(751,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:27:41','v1.0'),
(752,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:27:41','v1.0'),
(753,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:27:41','v1.0'),
(754,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:27:41','v1.0'),
(755,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:27:41','v1.0'),
(756,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:27:41','v1.0'),
(757,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:27:41','v1.0'),
(758,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:27:41','v1.0'),
(759,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:27:41','v1.0'),
(760,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:27:41','v1.0'),
(761,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:27:41','v1.0'),
(762,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:27:41','v1.0'),
(763,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:27:41','v1.0'),
(764,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:27:41','v1.0'),
(765,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:27:41','v1.0'),
(766,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:27:41','v1.0'),
(767,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:27:41','v1.0'),
(768,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:27:41','v1.0'),
(769,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:27:41','v1.0'),
(770,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 14:27:41','v1.0'),
(771,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:27:41','v1.0'),
(772,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:27:41','v1.0'),
(773,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:27:41','v1.0'),
(774,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:27:41','v1.0'),
(775,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:27:41','v1.0'),
(776,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:27:41','v1.0'),
(777,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:27:41','v1.0'),
(778,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:27:41','v1.0'),
(779,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:27:41','v1.0'),
(780,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:27:41','v1.0'),
(781,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:27:44','v1.0'),
(782,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:27:44','v1.0'),
(783,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:27:44','v1.0'),
(784,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:27:44','v1.0'),
(785,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:27:44','v1.0'),
(786,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:27:44','v1.0'),
(787,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:27:44','v1.0'),
(788,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:27:44','v1.0'),
(789,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:27:44','v1.0'),
(790,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:27:44','v1.0'),
(791,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:27:44','v1.0'),
(792,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:27:44','v1.0'),
(793,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:27:44','v1.0'),
(794,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:27:44','v1.0'),
(795,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:27:44','v1.0'),
(796,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:27:44','v1.0'),
(797,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:27:44','v1.0'),
(798,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:27:44','v1.0'),
(799,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:27:44','v1.0'),
(800,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 14:27:44','v1.0'),
(801,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:27:44','v1.0'),
(802,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:27:44','v1.0'),
(803,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:27:44','v1.0'),
(804,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:27:44','v1.0'),
(805,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:27:44','v1.0'),
(806,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:27:44','v1.0'),
(807,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:27:44','v1.0'),
(808,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:27:44','v1.0'),
(809,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:27:44','v1.0'),
(810,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:27:44','v1.0'),
(811,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:27:45','v1.0'),
(812,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:27:45','v1.0'),
(813,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:27:45','v1.0'),
(814,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:27:45','v1.0'),
(815,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:27:45','v1.0'),
(816,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:27:45','v1.0'),
(817,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:27:45','v1.0'),
(818,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:27:45','v1.0'),
(819,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:27:45','v1.0'),
(820,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:27:45','v1.0'),
(821,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:27:45','v1.0'),
(822,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:27:45','v1.0'),
(823,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:27:45','v1.0'),
(824,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:27:45','v1.0'),
(825,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:27:45','v1.0'),
(826,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:27:45','v1.0'),
(827,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:27:45','v1.0'),
(828,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:27:45','v1.0'),
(829,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:27:45','v1.0'),
(830,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 14:27:45','v1.0'),
(831,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:27:45','v1.0'),
(832,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:27:45','v1.0'),
(833,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:27:45','v1.0'),
(834,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:27:45','v1.0'),
(835,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:27:45','v1.0'),
(836,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:27:45','v1.0'),
(837,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:27:45','v1.0'),
(838,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:27:45','v1.0'),
(839,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:27:45','v1.0'),
(840,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:27:45','v1.0'),
(841,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:28:31','v1.0'),
(842,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:28:31','v1.0'),
(843,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:28:31','v1.0'),
(844,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:28:31','v1.0'),
(845,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:28:31','v1.0'),
(846,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:28:31','v1.0'),
(847,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:28:31','v1.0'),
(848,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:28:31','v1.0'),
(849,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:28:31','v1.0'),
(850,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:28:31','v1.0'),
(851,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:28:31','v1.0'),
(852,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:28:31','v1.0'),
(853,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:28:31','v1.0'),
(854,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:28:31','v1.0'),
(855,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:28:31','v1.0'),
(856,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:28:31','v1.0'),
(857,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:28:31','v1.0'),
(858,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:28:31','v1.0'),
(859,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:28:31','v1.0'),
(860,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 14:28:31','v1.0'),
(861,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:28:31','v1.0'),
(862,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:28:31','v1.0'),
(863,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:28:31','v1.0'),
(864,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:28:31','v1.0'),
(865,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:28:31','v1.0'),
(866,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:28:31','v1.0'),
(867,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:28:31','v1.0'),
(868,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:28:31','v1.0'),
(869,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:28:31','v1.0'),
(870,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:28:31','v1.0'),
(871,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:30:31','v1.0'),
(872,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:30:31','v1.0'),
(873,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:30:31','v1.0'),
(874,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:30:31','v1.0'),
(875,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:30:31','v1.0'),
(876,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:30:31','v1.0'),
(877,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:30:31','v1.0'),
(878,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:30:31','v1.0'),
(879,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:30:31','v1.0'),
(880,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:30:31','v1.0'),
(881,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:30:31','v1.0'),
(882,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:30:31','v1.0'),
(883,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:30:31','v1.0'),
(884,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:30:31','v1.0'),
(885,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:30:31','v1.0'),
(886,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:30:31','v1.0'),
(887,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:30:31','v1.0'),
(888,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:30:31','v1.0'),
(889,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:30:31','v1.0'),
(890,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 14:30:31','v1.0'),
(891,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:30:31','v1.0'),
(892,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:30:31','v1.0'),
(893,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:30:31','v1.0'),
(894,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:30:31','v1.0'),
(895,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:30:31','v1.0'),
(896,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:30:31','v1.0'),
(897,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:30:31','v1.0'),
(898,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:30:31','v1.0'),
(899,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:30:31','v1.0'),
(900,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:30:31','v1.0'),
(901,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:33:58','v1.0'),
(902,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:33:58','v1.0'),
(903,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:33:58','v1.0'),
(904,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:33:58','v1.0'),
(905,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:33:58','v1.0'),
(906,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:33:58','v1.0'),
(907,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:33:58','v1.0'),
(908,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:33:58','v1.0'),
(909,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:33:58','v1.0'),
(910,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:33:58','v1.0'),
(911,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:33:58','v1.0'),
(912,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:33:58','v1.0'),
(913,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:33:58','v1.0'),
(914,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:33:58','v1.0'),
(915,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:33:58','v1.0'),
(916,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:33:58','v1.0'),
(917,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:33:58','v1.0'),
(918,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:33:58','v1.0'),
(919,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:33:58','v1.0'),
(920,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 14:33:58','v1.0'),
(921,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:33:58','v1.0'),
(922,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:33:58','v1.0'),
(923,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:33:58','v1.0'),
(924,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:33:58','v1.0'),
(925,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:33:58','v1.0'),
(926,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:33:58','v1.0'),
(927,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:33:58','v1.0'),
(928,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:33:58','v1.0'),
(929,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:33:58','v1.0'),
(930,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:33:58','v1.0'),
(931,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:35:28','v1.0'),
(932,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:35:28','v1.0'),
(933,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:35:28','v1.0'),
(934,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:35:28','v1.0'),
(935,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:35:28','v1.0'),
(936,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:35:28','v1.0'),
(937,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:35:28','v1.0'),
(938,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:35:28','v1.0'),
(939,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:35:28','v1.0'),
(940,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:35:28','v1.0'),
(941,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:35:28','v1.0'),
(942,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:35:28','v1.0'),
(943,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:35:28','v1.0'),
(944,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:35:28','v1.0'),
(945,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:35:28','v1.0'),
(946,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:35:28','v1.0'),
(947,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:35:28','v1.0'),
(948,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:35:28','v1.0'),
(949,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:35:28','v1.0'),
(950,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 14:35:28','v1.0'),
(951,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:35:28','v1.0'),
(952,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:35:28','v1.0'),
(953,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:35:28','v1.0'),
(954,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:35:28','v1.0'),
(955,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:35:28','v1.0'),
(956,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:35:28','v1.0'),
(957,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:35:28','v1.0'),
(958,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:35:28','v1.0'),
(959,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:35:28','v1.0'),
(960,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:35:28','v1.0'),
(961,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:35:30','v1.0'),
(962,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:35:30','v1.0'),
(963,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:35:30','v1.0'),
(964,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:35:30','v1.0'),
(965,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:35:30','v1.0'),
(966,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:35:30','v1.0'),
(967,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:35:30','v1.0'),
(968,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:35:30','v1.0'),
(969,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:35:30','v1.0'),
(970,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:35:30','v1.0'),
(971,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:35:30','v1.0'),
(972,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:35:30','v1.0'),
(973,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:35:30','v1.0'),
(974,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:35:30','v1.0'),
(975,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:35:30','v1.0'),
(976,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:35:30','v1.0'),
(977,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:35:30','v1.0'),
(978,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:35:30','v1.0'),
(979,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:35:30','v1.0'),
(980,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 14:35:30','v1.0'),
(981,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:35:30','v1.0'),
(982,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:35:30','v1.0'),
(983,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:35:30','v1.0'),
(984,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:35:30','v1.0'),
(985,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:35:30','v1.0'),
(986,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:35:30','v1.0'),
(987,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:35:30','v1.0'),
(988,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:35:30','v1.0'),
(989,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:35:30','v1.0'),
(990,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:35:30','v1.0'),
(991,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:35:44','v1.0'),
(992,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:35:44','v1.0'),
(993,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:35:44','v1.0'),
(994,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:35:44','v1.0'),
(995,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:35:44','v1.0'),
(996,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:35:44','v1.0'),
(997,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:35:44','v1.0'),
(998,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:35:44','v1.0'),
(999,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:35:44','v1.0'),
(1000,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:35:44','v1.0'),
(1001,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:35:44','v1.0'),
(1002,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:35:44','v1.0'),
(1003,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:35:44','v1.0'),
(1004,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:35:44','v1.0'),
(1005,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:35:44','v1.0'),
(1006,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:35:44','v1.0'),
(1007,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:35:44','v1.0'),
(1008,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:35:44','v1.0'),
(1009,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:35:44','v1.0'),
(1010,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 14:35:44','v1.0'),
(1011,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:35:44','v1.0'),
(1012,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:35:44','v1.0'),
(1013,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:35:44','v1.0'),
(1014,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:35:44','v1.0'),
(1015,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:35:44','v1.0'),
(1016,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:35:44','v1.0'),
(1017,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:35:44','v1.0'),
(1018,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:35:44','v1.0'),
(1019,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:35:44','v1.0'),
(1020,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:35:44','v1.0'),
(1021,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1022,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1023,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1024,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1025,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1026,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1027,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1028,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1029,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1030,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1031,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1032,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1033,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1034,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1035,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1036,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1037,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1038,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1039,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1040,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1041,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1042,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1043,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1044,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1045,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1046,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1047,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1048,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1049,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1050,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1051,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1052,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1053,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1054,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1055,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1056,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1057,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1058,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1059,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1060,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1061,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1062,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1063,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1064,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1065,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1066,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1067,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1068,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1069,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1070,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1071,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1072,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1073,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1074,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1075,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1076,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1077,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1078,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1079,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1080,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:38:37','v1.0'),
(1081,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:38:38','v1.0'),
(1082,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:38:38','v1.0'),
(1083,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:38:38','v1.0'),
(1084,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:38:38','v1.0'),
(1085,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:38:38','v1.0'),
(1086,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:38:38','v1.0'),
(1087,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:38:38','v1.0'),
(1088,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:38:38','v1.0'),
(1089,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:38:38','v1.0'),
(1090,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:38:38','v1.0'),
(1091,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:38:38','v1.0'),
(1092,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:38:38','v1.0'),
(1093,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:38:38','v1.0'),
(1094,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:38:38','v1.0'),
(1095,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:38:38','v1.0'),
(1096,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:38:38','v1.0'),
(1097,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:38:38','v1.0'),
(1098,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:38:38','v1.0'),
(1099,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:38:38','v1.0'),
(1100,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 14:38:38','v1.0'),
(1101,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:38:38','v1.0'),
(1102,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:38:38','v1.0'),
(1103,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:38:38','v1.0'),
(1104,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:38:38','v1.0'),
(1105,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:38:38','v1.0'),
(1106,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:38:38','v1.0'),
(1107,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:38:38','v1.0'),
(1108,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:38:38','v1.0'),
(1109,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:38:38','v1.0'),
(1110,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:38:38','v1.0'),
(1111,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:39:54','v1.0'),
(1112,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:39:54','v1.0'),
(1113,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:39:54','v1.0'),
(1114,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:39:54','v1.0'),
(1115,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:39:54','v1.0'),
(1116,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:39:54','v1.0'),
(1117,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:39:54','v1.0'),
(1118,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:39:54','v1.0'),
(1119,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:39:54','v1.0'),
(1120,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:39:54','v1.0'),
(1121,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:39:54','v1.0'),
(1122,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:39:54','v1.0'),
(1123,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:39:54','v1.0'),
(1124,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:39:54','v1.0'),
(1125,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:39:54','v1.0'),
(1126,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:39:54','v1.0'),
(1127,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:39:54','v1.0'),
(1128,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:39:54','v1.0'),
(1129,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:39:54','v1.0'),
(1130,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 14:39:54','v1.0'),
(1131,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:39:54','v1.0'),
(1132,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:39:54','v1.0'),
(1133,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:39:54','v1.0'),
(1134,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:39:54','v1.0'),
(1135,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:39:54','v1.0'),
(1136,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:39:54','v1.0'),
(1137,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:39:54','v1.0'),
(1138,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:39:54','v1.0'),
(1139,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:39:54','v1.0'),
(1140,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:39:54','v1.0'),
(1141,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:41:33','v1.0'),
(1142,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:41:33','v1.0'),
(1143,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:41:33','v1.0'),
(1144,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:41:33','v1.0'),
(1145,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:41:33','v1.0'),
(1146,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:41:33','v1.0'),
(1147,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:41:33','v1.0'),
(1148,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:41:33','v1.0'),
(1149,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:41:33','v1.0'),
(1150,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:41:33','v1.0'),
(1151,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:41:33','v1.0'),
(1152,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:41:33','v1.0'),
(1153,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:41:33','v1.0'),
(1154,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:41:33','v1.0'),
(1155,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:41:33','v1.0'),
(1156,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:41:33','v1.0'),
(1157,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:41:33','v1.0'),
(1158,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:41:33','v1.0'),
(1159,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:41:33','v1.0'),
(1160,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 14:41:33','v1.0'),
(1161,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:41:33','v1.0'),
(1162,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:41:33','v1.0'),
(1163,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:41:33','v1.0'),
(1164,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:41:33','v1.0'),
(1165,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:41:33','v1.0'),
(1166,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:41:33','v1.0'),
(1167,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:41:33','v1.0'),
(1168,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:41:33','v1.0'),
(1169,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:41:33','v1.0'),
(1170,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:41:33','v1.0'),
(1171,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:42:24','v1.0'),
(1172,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:42:24','v1.0'),
(1173,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:42:24','v1.0'),
(1174,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:42:24','v1.0'),
(1175,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:42:24','v1.0'),
(1176,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:42:24','v1.0'),
(1177,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:42:24','v1.0'),
(1178,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:42:24','v1.0'),
(1179,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:42:24','v1.0'),
(1180,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:42:24','v1.0'),
(1181,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:42:24','v1.0'),
(1182,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:42:24','v1.0'),
(1183,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:42:24','v1.0'),
(1184,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:42:24','v1.0'),
(1185,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:42:24','v1.0'),
(1186,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:42:24','v1.0'),
(1187,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:42:24','v1.0'),
(1188,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:42:24','v1.0'),
(1189,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:42:24','v1.0'),
(1190,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 14:42:24','v1.0'),
(1191,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:42:24','v1.0'),
(1192,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:42:24','v1.0'),
(1193,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:42:24','v1.0'),
(1194,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:42:24','v1.0'),
(1195,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:42:24','v1.0'),
(1196,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:42:24','v1.0'),
(1197,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:42:24','v1.0'),
(1198,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:42:24','v1.0'),
(1199,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:42:24','v1.0'),
(1200,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:42:24','v1.0'),
(1201,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:42:30','v1.0'),
(1202,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:42:30','v1.0'),
(1203,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:42:30','v1.0'),
(1204,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:42:30','v1.0'),
(1205,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:42:30','v1.0'),
(1206,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:42:30','v1.0'),
(1207,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:42:30','v1.0'),
(1208,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:42:30','v1.0'),
(1209,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:42:30','v1.0'),
(1210,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:42:30','v1.0'),
(1211,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:42:30','v1.0'),
(1212,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:42:30','v1.0'),
(1213,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:42:30','v1.0'),
(1214,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:42:30','v1.0'),
(1215,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:42:30','v1.0'),
(1216,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:42:30','v1.0'),
(1217,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:42:30','v1.0'),
(1218,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:42:30','v1.0'),
(1219,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:42:30','v1.0'),
(1220,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 14:42:30','v1.0'),
(1221,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:42:30','v1.0'),
(1222,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:42:30','v1.0'),
(1223,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:42:30','v1.0'),
(1224,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:42:30','v1.0'),
(1225,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:42:30','v1.0'),
(1226,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:42:30','v1.0'),
(1227,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:42:30','v1.0'),
(1228,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:42:30','v1.0'),
(1229,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:42:30','v1.0'),
(1230,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:42:30','v1.0'),
(1231,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:44:25','v1.0'),
(1232,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:44:25','v1.0'),
(1233,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:44:25','v1.0'),
(1234,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:44:25','v1.0'),
(1235,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:44:25','v1.0'),
(1236,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:44:25','v1.0'),
(1237,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:44:25','v1.0'),
(1238,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:44:25','v1.0'),
(1239,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:44:25','v1.0'),
(1240,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:44:25','v1.0'),
(1241,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:44:25','v1.0'),
(1242,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:44:25','v1.0'),
(1243,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:44:25','v1.0'),
(1244,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:44:25','v1.0'),
(1245,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:44:25','v1.0'),
(1246,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:44:25','v1.0'),
(1247,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:44:25','v1.0'),
(1248,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:44:25','v1.0'),
(1249,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:44:25','v1.0'),
(1250,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 14:44:25','v1.0'),
(1251,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:44:25','v1.0'),
(1252,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:44:25','v1.0'),
(1253,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:44:25','v1.0'),
(1254,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:44:25','v1.0'),
(1255,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:44:25','v1.0'),
(1256,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:44:25','v1.0'),
(1257,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:44:25','v1.0'),
(1258,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:44:25','v1.0'),
(1259,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:44:25','v1.0'),
(1260,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:44:25','v1.0'),
(1261,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:44:45','v1.0'),
(1262,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:44:45','v1.0'),
(1263,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:44:45','v1.0'),
(1264,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:44:45','v1.0'),
(1265,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:44:45','v1.0'),
(1266,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:44:45','v1.0'),
(1267,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:44:45','v1.0'),
(1268,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:44:45','v1.0'),
(1269,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:44:45','v1.0'),
(1270,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:44:45','v1.0'),
(1271,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:44:45','v1.0'),
(1272,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:44:45','v1.0'),
(1273,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:44:45','v1.0'),
(1274,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:44:45','v1.0'),
(1275,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:44:45','v1.0'),
(1276,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:44:45','v1.0'),
(1277,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:44:45','v1.0'),
(1278,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:44:45','v1.0'),
(1279,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:44:45','v1.0'),
(1280,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 14:44:45','v1.0'),
(1281,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:44:45','v1.0'),
(1282,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:44:45','v1.0'),
(1283,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:44:45','v1.0'),
(1284,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:44:45','v1.0'),
(1285,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:44:45','v1.0'),
(1286,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:44:45','v1.0'),
(1287,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:44:45','v1.0'),
(1288,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:44:45','v1.0'),
(1289,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:44:45','v1.0'),
(1290,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:44:45','v1.0'),
(1291,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:44:46','v1.0'),
(1292,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:44:46','v1.0'),
(1293,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:44:46','v1.0'),
(1294,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:44:46','v1.0'),
(1295,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:44:46','v1.0'),
(1296,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:44:46','v1.0'),
(1297,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:44:46','v1.0'),
(1298,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:44:46','v1.0'),
(1299,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:44:46','v1.0'),
(1300,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:44:46','v1.0'),
(1301,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:44:46','v1.0'),
(1302,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:44:46','v1.0'),
(1303,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:44:46','v1.0'),
(1304,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:44:46','v1.0'),
(1305,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:44:46','v1.0'),
(1306,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:44:46','v1.0'),
(1307,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:44:46','v1.0'),
(1308,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:44:46','v1.0'),
(1309,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:44:46','v1.0'),
(1310,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 14:44:46','v1.0'),
(1311,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:44:46','v1.0'),
(1312,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:44:46','v1.0'),
(1313,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:44:46','v1.0'),
(1314,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:44:46','v1.0'),
(1315,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:44:46','v1.0'),
(1316,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:44:46','v1.0'),
(1317,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:44:46','v1.0'),
(1318,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:44:46','v1.0'),
(1319,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:44:46','v1.0'),
(1320,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:44:46','v1.0'),
(1321,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:46:38','v1.0'),
(1322,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:46:38','v1.0'),
(1323,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:46:38','v1.0'),
(1324,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:46:38','v1.0'),
(1325,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:46:38','v1.0'),
(1326,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:46:38','v1.0'),
(1327,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:46:38','v1.0'),
(1328,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:46:38','v1.0'),
(1329,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:46:38','v1.0'),
(1330,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:46:38','v1.0'),
(1331,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:46:38','v1.0'),
(1332,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:46:38','v1.0'),
(1333,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:46:38','v1.0'),
(1334,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:46:38','v1.0'),
(1335,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:46:38','v1.0'),
(1336,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:46:38','v1.0'),
(1337,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:46:38','v1.0'),
(1338,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:46:38','v1.0'),
(1339,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:46:38','v1.0'),
(1340,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 14:46:38','v1.0'),
(1341,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:46:38','v1.0'),
(1342,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:46:38','v1.0'),
(1343,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:46:38','v1.0'),
(1344,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:46:38','v1.0'),
(1345,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:46:38','v1.0'),
(1346,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:46:38','v1.0'),
(1347,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:46:38','v1.0'),
(1348,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:46:38','v1.0'),
(1349,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:46:38','v1.0'),
(1350,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:46:38','v1.0'),
(1351,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:47:10','v1.0'),
(1352,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:47:10','v1.0'),
(1353,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:47:10','v1.0'),
(1354,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:47:10','v1.0'),
(1355,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:47:10','v1.0'),
(1356,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:47:10','v1.0'),
(1357,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:47:10','v1.0'),
(1358,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:47:10','v1.0'),
(1359,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:47:10','v1.0'),
(1360,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:47:10','v1.0'),
(1361,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:47:10','v1.0'),
(1362,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:47:10','v1.0'),
(1363,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:47:10','v1.0'),
(1364,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:47:10','v1.0'),
(1365,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:47:10','v1.0'),
(1366,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:47:10','v1.0'),
(1367,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:47:10','v1.0'),
(1368,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:47:10','v1.0'),
(1369,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:47:10','v1.0'),
(1370,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 14:47:10','v1.0'),
(1371,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:47:10','v1.0'),
(1372,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:47:10','v1.0'),
(1373,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:47:10','v1.0'),
(1374,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:47:10','v1.0'),
(1375,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:47:10','v1.0'),
(1376,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:47:10','v1.0'),
(1377,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:47:10','v1.0'),
(1378,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:47:10','v1.0'),
(1379,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:47:10','v1.0'),
(1380,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:47:10','v1.0'),
(1381,21,0,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:49:26','v1.0'),
(1382,22,0,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:49:26','v1.0'),
(1383,23,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:49:26','v1.0'),
(1384,24,0,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:49:26','v1.0'),
(1385,25,0,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:49:26','v1.0'),
(1386,26,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:49:26','v1.0'),
(1387,27,0,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:49:26','v1.0'),
(1388,28,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:49:26','v1.0'),
(1389,29,0,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:49:26','v1.0'),
(1390,30,0,'{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:49:26','v1.0'),
(1391,11,0,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:49:26','v1.0'),
(1392,12,0,'{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:49:26','v1.0'),
(1393,13,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:49:26','v1.0'),
(1394,14,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-02 14:49:26','v1.0'),
(1395,15,0,'{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:49:26','v1.0'),
(1396,16,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:49:26','v1.0'),
(1397,17,0,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:49:26','v1.0'),
(1398,18,0,'{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:49:26','v1.0'),
(1399,19,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:49:26','v1.0'),
(1400,20,0,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}','2026-07-02 14:49:26','v1.0'),
(1401,1,0,'{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:49:26','v1.0'),
(1402,2,0,'{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:49:26','v1.0'),
(1403,3,0,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}','2026-07-02 14:49:26','v1.0'),
(1404,4,0,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:49:26','v1.0'),
(1405,5,0,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:49:26','v1.0'),
(1406,6,0,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:49:26','v1.0'),
(1407,7,0,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-02 14:49:26','v1.0'),
(1408,8,0,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-02 14:49:26','v1.0'),
(1409,9,0,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-02 14:49:26','v1.0'),
(1410,10,0,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-02 14:49:26','v1.0'),
(1411,21,1128,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3}','2026-07-20 02:55:44','v2.0-ridgecv'),
(1412,22,1128,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5}','2026-07-20 02:55:44','v2.0-ridgecv'),
(1413,24,1129,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3}','2026-07-20 02:55:44','v2.0-ridgecv'),
(1414,25,1128,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4}','2026-07-20 02:55:44','v2.0-ridgecv'),
(1415,27,1127,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5}','2026-07-20 02:55:44','v2.0-ridgecv'),
(1416,29,1128,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4}','2026-07-20 02:55:44','v2.0-ridgecv'),
(1417,11,1127,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5}','2026-07-20 02:55:44','v2.0-ridgecv'),
(1418,13,1127,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6}','2026-07-20 02:55:44','v2.0-ridgecv'),
(1419,14,1128,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3}','2026-07-20 02:55:44','v2.0-ridgecv'),
(1420,16,1128,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5}','2026-07-20 02:55:44','v2.0-ridgecv'),
(1421,17,1127,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5}','2026-07-20 02:55:44','v2.0-ridgecv'),
(1422,19,1128,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4}','2026-07-20 02:55:44','v2.0-ridgecv'),
(1423,20,1126,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9}','2026-07-20 02:55:44','v2.0-ridgecv'),
(1424,4,1128,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4}','2026-07-20 02:55:44','v2.0-ridgecv'),
(1425,6,1128,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5}','2026-07-20 02:55:44','v2.0-ridgecv'),
(1426,7,1127,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8}','2026-07-20 02:55:44','v2.0-ridgecv'),
(1427,8,1128,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5}','2026-07-20 02:55:44','v2.0-ridgecv'),
(1428,9,1128,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4}','2026-07-20 02:55:44','v2.0-ridgecv'),
(1429,10,1127,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6}','2026-07-20 02:55:44','v2.0-ridgecv'),
(1430,21,1525,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3}','2026-07-20 03:29:20','v3.0-linreg'),
(1431,22,842,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5}','2026-07-20 03:29:20','v3.0-linreg'),
(1432,24,1597,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3}','2026-07-20 03:29:20','v3.0-linreg'),
(1433,25,1167,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4}','2026-07-20 03:29:20','v3.0-linreg'),
(1434,27,1042,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5}','2026-07-20 03:29:20','v3.0-linreg'),
(1435,29,647,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4}','2026-07-20 03:29:20','v3.0-linreg'),
(1436,11,987,'{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5}','2026-07-20 03:29:20','v3.0-linreg'),
(1437,13,470,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6}','2026-07-20 03:29:20','v3.0-linreg'),
(1438,14,922,'{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3}','2026-07-20 03:29:20','v3.0-linreg'),
(1439,16,633,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5}','2026-07-20 03:29:20','v3.0-linreg'),
(1440,17,868,'{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5}','2026-07-20 03:29:20','v3.0-linreg'),
(1441,19,626,'{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4}','2026-07-20 03:29:20','v3.0-linreg'),
(1442,20,986,'{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9}','2026-07-20 03:29:20','v3.0-linreg'),
(1443,4,1172,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4}','2026-07-20 03:29:20','v3.0-linreg'),
(1444,6,1307,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5}','2026-07-20 03:29:20','v3.0-linreg'),
(1445,7,890,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8}','2026-07-20 03:29:20','v3.0-linreg'),
(1446,8,561,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5}','2026-07-20 03:29:20','v3.0-linreg'),
(1447,9,818,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4}','2026-07-20 03:29:20','v3.0-linreg'),
(1448,10,1380,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6}','2026-07-20 03:29:20','v3.0-linreg'),
(1449,21,1426,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-21 04:06:49','v4.0-linreg-6f'),
(1450,22,800,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-21 04:06:49','v4.0-linreg-6f'),
(1451,24,1597,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-21 04:06:49','v4.0-linreg-6f'),
(1452,25,1038,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-21 04:06:49','v4.0-linreg-6f'),
(1453,27,762,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-21 04:06:49','v4.0-linreg-6f'),
(1454,29,669,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-21 04:06:49','v4.0-linreg-6f'),
(1455,13,551,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 383}','2026-07-21 04:06:49','v4.0-linreg-6f'),
(1456,4,644,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-21 04:06:49','v4.0-linreg-6f'),
(1457,6,1395,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-21 04:06:49','v4.0-linreg-6f'),
(1458,7,779,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-21 04:06:49','v4.0-linreg-6f'),
(1459,8,576,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-21 04:06:49','v4.0-linreg-6f'),
(1460,9,834,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-21 04:06:49','v4.0-linreg-6f'),
(1461,10,943,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-21 04:06:49','v4.0-linreg-6f'),
(1462,21,1426,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-22 06:40:58','v4.0-linreg-6f'),
(1463,22,800,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-22 06:40:58','v4.0-linreg-6f'),
(1464,24,1597,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-22 06:40:58','v4.0-linreg-6f'),
(1465,25,1038,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-22 06:40:58','v4.0-linreg-6f'),
(1466,27,762,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-22 06:40:58','v4.0-linreg-6f'),
(1467,29,669,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-22 06:40:58','v4.0-linreg-6f'),
(1468,13,551,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 383}','2026-07-22 06:40:58','v4.0-linreg-6f'),
(1469,4,644,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-22 06:40:59','v4.0-linreg-6f'),
(1470,6,1395,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-22 06:40:59','v4.0-linreg-6f'),
(1471,7,779,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-22 06:40:59','v4.0-linreg-6f'),
(1472,8,576,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-22 06:40:59','v4.0-linreg-6f'),
(1473,9,834,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-22 06:40:59','v4.0-linreg-6f'),
(1474,10,943,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-22 06:40:59','v4.0-linreg-6f'),
(1475,21,1426,'{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-23 03:11:23','v4.0-linreg-6f'),
(1476,22,800,'{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-23 03:11:23','v4.0-linreg-6f'),
(1477,24,1597,'{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}','2026-07-23 03:11:23','v4.0-linreg-6f'),
(1478,25,1038,'{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-23 03:11:23','v4.0-linreg-6f'),
(1479,27,762,'{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-23 03:11:23','v4.0-linreg-6f'),
(1480,29,669,'{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-23 03:11:23','v4.0-linreg-6f'),
(1481,13,551,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 383}','2026-07-23 03:11:23','v4.0-linreg-6f'),
(1482,4,644,'{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-23 03:11:23','v4.0-linreg-6f'),
(1483,6,1395,'{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-23 03:11:23','v4.0-linreg-6f'),
(1484,7,779,'{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}','2026-07-23 03:11:23','v4.0-linreg-6f'),
(1485,8,576,'{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}','2026-07-23 03:11:23','v4.0-linreg-6f'),
(1486,9,834,'{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}','2026-07-23 03:11:23','v4.0-linreg-6f'),
(1487,10,943,'{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}','2026-07-23 03:11:23','v4.0-linreg-6f');
/*!40000 ALTER TABLE `prediction_logs` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;

--
-- Table structure for table `preposition_records`
--

DROP TABLE IF EXISTS `preposition_records`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `preposition_records` (
  `preposition_id` int(11) NOT NULL AUTO_INCREMENT,
  `from_office_id` int(11) NOT NULL,
  `to_barangay_id` int(11) NOT NULL,
  `item_type` enum('food_pack') NOT NULL DEFAULT 'food_pack',
  `quantity` int(11) NOT NULL DEFAULT 0,
  `status` enum('pending','approved','completed') NOT NULL DEFAULT 'pending',
  `preposition_date` date NOT NULL,
  `disaster_event` varchar(150) DEFAULT NULL,
  `event_id` int(11) DEFAULT NULL,
  `created_by` int(11) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`preposition_id`),
  KEY `from_office_id` (`from_office_id`),
  KEY `to_barangay_id` (`to_barangay_id`),
  KEY `created_by` (`created_by`),
  KEY `fk_prepo_event` (`event_id`),
  CONSTRAINT `fk_prepo_event` FOREIGN KEY (`event_id`) REFERENCES `disaster_events` (`event_id`),
  CONSTRAINT `preposition_records_ibfk_1` FOREIGN KEY (`from_office_id`) REFERENCES `offices` (`office_id`) ON DELETE CASCADE,
  CONSTRAINT `preposition_records_ibfk_2` FOREIGN KEY (`to_barangay_id`) REFERENCES `barangays` (`barangay_id`) ON DELETE CASCADE,
  CONSTRAINT `preposition_records_ibfk_3` FOREIGN KEY (`created_by`) REFERENCES `users` (`user_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `preposition_records`
--

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `preposition_records` WRITE;
/*!40000 ALTER TABLE `preposition_records` DISABLE KEYS */;
/*!40000 ALTER TABLE `preposition_records` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;

--
-- Table structure for table `relief_request_batches`
--

DROP TABLE IF EXISTS `relief_request_batches`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `relief_request_batches` (
  `batch_id` int(11) NOT NULL AUTO_INCREMENT,
  `office_id` int(11) NOT NULL,
  `event_id` int(11) NOT NULL,
  `requested_food_packs` int(11) DEFAULT NULL,
  `priority` enum('high','medium','low') DEFAULT NULL,
  `reason` text DEFAULT NULL,
  `remarks` text DEFAULT NULL,
  `damage_report_file` varchar(255) DEFAULT NULL,
  `photo_files` varchar(500) DEFAULT NULL,
  `other_files` varchar(500) DEFAULT NULL,
  `created_by` int(11) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `submitted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`batch_id`),
  KEY `office_id` (`office_id`),
  KEY `event_id` (`event_id`),
  KEY `created_by` (`created_by`),
  CONSTRAINT `relief_request_batches_ibfk_1` FOREIGN KEY (`office_id`) REFERENCES `offices` (`office_id`),
  CONSTRAINT `relief_request_batches_ibfk_2` FOREIGN KEY (`event_id`) REFERENCES `disaster_events` (`event_id`),
  CONSTRAINT `relief_request_batches_ibfk_3` FOREIGN KEY (`created_by`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `relief_request_batches`
--

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `relief_request_batches` WRITE;
/*!40000 ALTER TABLE `relief_request_batches` DISABLE KEYS */;
INSERT INTO `relief_request_batches` VALUES
(1,3,1,600,'medium','','',NULL,NULL,NULL,4,'2026-07-20 06:52:00',NULL),
(2,3,1,1500,'high','Rising floodwater near the irrigation canal is displacing households; requesting priority food pack allocation.','',NULL,NULL,NULL,4,'2026-07-19 06:52:00','2026-07-19 06:52:00'),
(3,3,1,900,'medium','Verified barangay reports show sustained flooding; requesting food packs to cover the affected families.','Please prioritize Abot given the higher affected household count.',NULL,NULL,NULL,4,'2026-07-17 06:52:00','2026-07-17 06:52:00'),
(4,3,1,700,'low','Minor flooding reported; requesting food packs as a precaution.','',NULL,NULL,NULL,4,'2026-07-16 06:52:00','2026-07-16 06:52:00'),
(5,3,2,900,'medium','Post-typhoon flooding required food pack assistance for the two barangays.','',NULL,NULL,NULL,4,'2025-06-25 06:52:00','2025-06-25 06:52:00'),
(6,3,3,1200,'high','Widespread flooding across three barangays required urgent food pack support.','',NULL,NULL,NULL,4,'2025-05-16 06:52:00','2025-05-16 06:52:00'),
(7,3,1,750,'high','updated reason','updated remarks',NULL,NULL,NULL,4,'2026-07-20 07:01:32',NULL),
(8,3,1,400,'medium','Carosucan Norte flooding requires food pack support.','Test submission with file upload.','damage_report.pdf','photo1.jpg',NULL,4,'2026-07-20 07:02:35','2026-07-20 07:02:35'),
(9,2,1,5600,'medium','Verified barangay reports show typhoon-related flooding requiring food pack support.',NULL,NULL,NULL,NULL,3,'2026-07-19 09:00:00','2026-07-19 09:00:00'),
(10,3,1,2200,'medium','Verified barangay reports show typhoon-related flooding requiring food pack support.',NULL,NULL,NULL,NULL,4,'2026-07-19 09:00:00','2026-07-19 09:00:00'),
(11,4,1,4600,'medium','Verified barangay reports show typhoon-related flooding requiring food pack support.',NULL,NULL,NULL,NULL,5,'2026-07-19 09:00:00','2026-07-19 09:00:00');
/*!40000 ALTER TABLE `relief_request_batches` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;

--
-- Table structure for table `report_logs`
--

DROP TABLE IF EXISTS `report_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `report_logs` (
  `report_id` int(11) NOT NULL AUTO_INCREMENT,
  `report_type` varchar(50) NOT NULL,
  `format` enum('pdf','excel') NOT NULL,
  `pages` int(11) DEFAULT 1,
  `filters_json` text DEFAULT NULL,
  `generated_by` int(11) DEFAULT NULL,
  `generated_at` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`report_id`),
  KEY `generated_by` (`generated_by`),
  CONSTRAINT `report_logs_ibfk_1` FOREIGN KEY (`generated_by`) REFERENCES `users` (`user_id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=42 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `report_logs`
--

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `report_logs` WRITE;
/*!40000 ALTER TABLE `report_logs` DISABLE KEYS */;
INSERT INTO `report_logs` VALUES
(1,'relief_requests','pdf',1,'{\"event_id\": null, \"municipality\": \"all\", \"days\": 30}',2,'2026-07-20 03:26:19'),
(2,'relief_requests','excel',1,'{\"event_id\": null, \"municipality\": \"all\", \"days\": 30}',2,'2026-07-20 03:26:19'),
(3,'distribution','pdf',1,'{\"event_id\": null, \"municipality\": \"all\", \"days\": 30}',2,'2026-07-20 03:26:19'),
(4,'distribution','excel',1,'{\"event_id\": null, \"municipality\": \"all\", \"days\": 30}',2,'2026-07-20 03:26:19'),
(5,'warehouse_inventory','pdf',1,'{\"event_id\": null, \"municipality\": \"all\", \"days\": 30}',2,'2026-07-20 03:26:19'),
(6,'warehouse_inventory','excel',1,'{\"event_id\": null, \"municipality\": \"all\", \"days\": 30}',2,'2026-07-20 03:26:19'),
(7,'stock_movement','pdf',1,'{\"event_id\": null, \"municipality\": \"all\", \"days\": 30}',2,'2026-07-20 03:26:20'),
(8,'stock_movement','excel',1,'{\"event_id\": null, \"municipality\": \"all\", \"days\": 30}',2,'2026-07-20 03:26:20'),
(9,'municipality_summary','pdf',1,'{\"event_id\": null, \"municipality\": \"all\", \"days\": 30}',2,'2026-07-20 03:26:20'),
(10,'municipality_summary','excel',1,'{\"event_id\": null, \"municipality\": \"all\", \"days\": 30}',2,'2026-07-20 03:26:20'),
(11,'typhoon_summary','pdf',1,'{\"event_id\": null, \"municipality\": \"all\", \"days\": 30}',2,'2026-07-20 03:26:20'),
(12,'typhoon_summary','excel',1,'{\"event_id\": null, \"municipality\": \"all\", \"days\": 30}',2,'2026-07-20 03:26:20'),
(13,'analytics','pdf',1,'{\"event_id\": null, \"municipality\": \"all\", \"days\": 30}',2,'2026-07-20 03:26:20'),
(14,'analytics','excel',1,'{\"event_id\": null, \"municipality\": \"all\", \"days\": 30}',2,'2026-07-20 03:26:20'),
(15,'relief_requests','pdf',1,'{\"event_id\": 1, \"municipality\": \"all\", \"days\": 30}',2,'2026-07-20 03:28:23'),
(16,'relief_requests','pdf',1,'{\"event_id\": 1, \"municipality\": \"all\", \"days\": 30}',2,'2026-07-20 03:35:47'),
(17,'relief_requests','excel',1,'{\"event_id\": 1, \"municipality\": \"all\", \"days\": 30}',2,'2026-07-20 03:35:47'),
(18,'relief_requests','pdf',1,'{\"event_id\": 1, \"municipality\": \"all\", \"days\": 30}',2,'2026-07-20 03:40:20'),
(19,'relief_requests','pdf',1,'{\"event_id\": 1, \"days\": 30}',3,'2026-07-21 04:36:05'),
(20,'relief_requests','excel',1,'{\"event_id\": 1, \"days\": 30}',3,'2026-07-21 04:36:05'),
(21,'distribution','pdf',1,'{\"event_id\": 1, \"days\": 30}',3,'2026-07-21 04:36:05'),
(22,'distribution','excel',1,'{\"event_id\": 1, \"days\": 30}',3,'2026-07-21 04:36:05'),
(23,'warehouse_inventory','pdf',1,'{\"event_id\": 1, \"days\": 30}',3,'2026-07-21 04:36:05'),
(24,'warehouse_inventory','excel',1,'{\"event_id\": 1, \"days\": 30}',3,'2026-07-21 04:36:05'),
(25,'stock_movement','pdf',1,'{\"event_id\": 1, \"days\": 30}',3,'2026-07-21 04:36:05'),
(26,'stock_movement','excel',1,'{\"event_id\": 1, \"days\": 30}',3,'2026-07-21 04:36:05'),
(27,'municipality_summary','pdf',1,'{\"event_id\": 1, \"days\": 30}',3,'2026-07-21 04:36:05'),
(28,'municipality_summary','excel',1,'{\"event_id\": 1, \"days\": 30}',3,'2026-07-21 04:36:05'),
(29,'typhoon_summary','pdf',1,'{\"event_id\": 1, \"days\": 30}',3,'2026-07-21 04:36:05'),
(30,'typhoon_summary','excel',1,'{\"event_id\": 1, \"days\": 30}',3,'2026-07-21 04:36:05'),
(31,'analytics','pdf',1,'{\"event_id\": 1, \"days\": 30}',3,'2026-07-21 04:36:05'),
(32,'analytics','excel',1,'{\"event_id\": 1, \"days\": 30}',3,'2026-07-21 04:36:05'),
(33,'damage_reports','pdf',1,'{\"event_id\": 1, \"days\": 30}',11,'2026-07-23 07:26:13'),
(34,'damage_reports','excel',1,'{\"event_id\": 1, \"days\": 30}',11,'2026-07-23 07:26:13'),
(35,'relief_deliveries','pdf',1,'{\"event_id\": 1, \"days\": 30}',11,'2026-07-23 07:26:13'),
(36,'relief_deliveries','excel',1,'{\"event_id\": 1, \"days\": 30}',11,'2026-07-23 07:26:14'),
(37,'damage_reports','pdf',1,'{\"event_id\": 1, \"days\": 30}',11,'2026-07-23 07:26:27'),
(38,'relief_deliveries','excel',1,'{\"event_id\": 1, \"days\": 30}',11,'2026-07-23 07:26:27'),
(39,'damage_reports','pdf',1,'{\"event_id\": 1, \"days\": \"all\"}',11,'2026-07-23 07:36:36'),
(40,'relief_requests','pdf',1,'{\"event_id\": 1, \"municipality\": \"all\", \"days\": \"all\"}',2,'2026-07-23 07:37:55'),
(41,'relief_requests','excel',1,'{\"event_id\": 1, \"days\": \"all\"}',3,'2026-07-23 07:37:56');
/*!40000 ALTER TABLE `report_logs` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;

--
-- Table structure for table `system_settings`
--

DROP TABLE IF EXISTS `system_settings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `system_settings` (
  `setting_key` varchar(50) NOT NULL,
  `setting_value` varchar(255) NOT NULL,
  `updated_by` int(11) DEFAULT NULL,
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`setting_key`),
  KEY `updated_by` (`updated_by`),
  CONSTRAINT `system_settings_ibfk_1` FOREIGN KEY (`updated_by`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `system_settings`
--

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `system_settings` WRITE;
/*!40000 ALTER TABLE `system_settings` DISABLE KEYS */;
INSERT INTO `system_settings` VALUES
('low_stock_alert_enabled','1',1,'2026-07-22 04:29:04'),
('warehouse_healthy_threshold','0.75',1,'2026-07-22 04:29:04'),
('warehouse_moderate_threshold','0.35',1,'2026-07-22 04:29:04');
/*!40000 ALTER TABLE `system_settings` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `user_id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('system_admin','pswdo_admin','cswdo_admin','barangay_user') NOT NULL,
  `office_id` int(11) DEFAULT NULL,
  `barangay_id` int(11) DEFAULT NULL,
  `designation` varchar(100) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  `last_login` datetime DEFAULT NULL,
  `last_activity` datetime DEFAULT NULL,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `email` (`email`),
  KEY `office_id` (`office_id`),
  KEY `users_barangay_fk` (`barangay_id`),
  CONSTRAINT `users_barangay_fk` FOREIGN KEY (`barangay_id`) REFERENCES `barangays` (`barangay_id`) ON DELETE SET NULL,
  CONSTRAINT `users_ibfk_1` FOREIGN KEY (`office_id`) REFERENCES `offices` (`office_id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=41 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES
(1,'System Administrator','sysadmin@reliefline.gov.ph','scrypt:32768:8:1$ACWFzaLGy9heyhXz$fb98ee72820adb627fcedd46fc7575eb6191e91565ba4c33b8f9ac73c4920b13e2b7a1294e50bb2795bbf60d443179676a03cba6dd1b67ba20267dea3f2b2b60','system_admin',NULL,NULL,NULL,'2026-06-25 10:39:03',1,'2026-07-23 07:46:34','2026-07-23 07:48:42'),
(2,'PSWDO Administrator','pswdo@reliefline.gov.ph','scrypt:32768:8:1$6TKHiPTTe8cNW2G9$489aa75bdbeb97d32a1854fac246977b379b30d8430abc884c4213dfa4aef475fb32fe0af6a399c54f5d5614d0e929b691bb3d939954e05738d49c68d7e28747','pswdo_admin',1,NULL,NULL,'2026-06-25 10:39:03',1,'2026-07-23 07:47:21','2026-07-23 07:49:06'),
(3,'Urdaneta CSWDO Admin','urdaneta@reliefline.gov.ph','scrypt:32768:8:1$3XpPWB2j3U6cFEzt$11cfc1508ba0ea780607ac904e1af7cad0b2f81480173bd897d859e86be85f98b4434d9fc072ff21c5c2a7cc9f285a67e72f59347c0ed8b74568dceab25e28bf','cswdo_admin',2,NULL,NULL,'2026-06-25 10:39:03',1,'2026-07-23 07:46:23','2026-07-23 07:48:00'),
(4,'Santa Barbara MSWDO Admin','santabarbara@reliefline.gov.ph','scrypt:32768:8:1$UpNPKFY5PCbB9wFL$4806ee7e20ba4583748074d364f7c27e3d314c755cd82a4ff7df618515e6af9266c13c39fd53515c759c6b24f644cdd26299f1ddcc07965750fbbadb2cc7fca0','cswdo_admin',3,NULL,NULL,'2026-06-25 10:39:03',1,'2026-07-22 06:41:32','2026-07-22 06:41:32'),
(5,'Calasiao MSWDO Admin','calasiao@reliefline.gov.ph','scrypt:32768:8:1$snI4mqxzFZtzg1kf$ce648ebad02a52f42aa4aa9f9359c8adc2eb5976dccddb80dfc3a50eead60feafc5557767a42489f273620b76014b41d0eb92496443a9023251e6dda8bc631e9','cswdo_admin',4,NULL,NULL,'2026-06-25 10:39:03',1,'2026-07-22 04:44:33',NULL),
(11,'Ramon Bautista','anonas.urdaneta@reliefline.gov.ph','scrypt:32768:8:1$7mAFGoC9Rv002oFD$21b158fb581a3fb1c1be771529c8396b12c1beff127436286c8f5a6df7b6cc8a284d179a2cbcc806ad637e7a0f66f702acd019be6009ed5ebaaa4647682fe291','barangay_user',NULL,1,'Barangay Captain','2026-07-23 04:36:56',1,'2026-07-23 07:47:09','2026-07-23 07:48:20'),
(12,'Cecilia Manalo','bactadeast.urdaneta@reliefline.gov.ph','scrypt:32768:8:1$Kfio6bqQW9wDGBco$2acd213abfc0e108d5e4e41fb706cfbd829bd8c8048f622813b72df4795532092147a761a8241354afbd5d7ed364860a92dccd11d14ee13a8481c969b877c246','barangay_user',NULL,2,'Barangay Captain','2026-07-23 04:36:56',1,'2026-07-23 06:27:18','2026-07-23 06:27:18'),
(13,'Ferdinand Cruz','bayaoas.urdaneta@reliefline.gov.ph','scrypt:32768:8:1$QwNXrI3vmjalmxYe$b42811b74e3a36c1ede2b478e54d853b0bc94da0878169a658010c8665fe1a6d82b6b989d026280555cf6928279e5dd4358509399e545cf151595f362c122516','barangay_user',NULL,3,'Barangay Captain','2026-07-23 04:36:56',1,NULL,NULL),
(14,'Marilou Santos','bolaoen.urdaneta@reliefline.gov.ph','scrypt:32768:8:1$2zsdzaaE93XM5qXZ$c24179079505bfe8221a8ac18a226d76fe59059f3105a3e6690973142c08ed11d854fd67e652a961d62bd1b844ecfcb39a72c35df5ca8efeea342acb7cc02de9','barangay_user',NULL,4,'Barangay Captain','2026-07-23 04:36:56',1,NULL,NULL),
(15,'Edgardo Villanueva','cabaruan.urdaneta@reliefline.gov.ph','scrypt:32768:8:1$YwaBV6BDYb32qki6$a29f379021fb516c58e13dde2902c82278114f0639e2771a10f70514054723fdb167898feada08c334b5cea8aeced4409377041498482eff57f2f72450c8b840','barangay_user',NULL,5,'Barangay Captain','2026-07-23 04:36:56',1,NULL,NULL),
(16,'Rosalinda Aquino','cabuloan.urdaneta@reliefline.gov.ph','scrypt:32768:8:1$mTXXGY5sNNnzZucy$e7511497836ee07d7678d3c41534c73d61a5559385a1ddb6497c287627eeefcd2441e7d7b91a78e3b0d5794402a170b1e88489fbbaede583da6ea66c1f13a631','barangay_user',NULL,6,'Barangay Captain','2026-07-23 04:36:56',1,'2026-07-23 06:27:18','2026-07-23 06:29:51'),
(17,'Danilo Mendoza','camantiles.urdaneta@reliefline.gov.ph','scrypt:32768:8:1$L81ZWS1ayKE8mIsM$41e21a429254b6b7794f4cfeef5b2db8b68e9c2692462e40b6beb42d32a38e4126879d13dd3782caa65761bc765d31dde5ab6d0aa9e998e43e12b3ccfabe938a','barangay_user',NULL,7,'Barangay Captain','2026-07-23 04:36:56',1,NULL,NULL),
(18,'Teresita Ramos','casantaan.urdaneta@reliefline.gov.ph','scrypt:32768:8:1$amtqwfsek3Jtnjm0$ab33655a6d77b14a0f36c42e52fd35acc925c499e06fe29e68b596851850921cdbcf2867ad01e4f4857128ccc6774c7d22466e74202290022682e714dc0dcb98','barangay_user',NULL,8,'Barangay Captain','2026-07-23 04:36:56',1,NULL,NULL),
(19,'Rogelio Domingo','catablan.urdaneta@reliefline.gov.ph','scrypt:32768:8:1$9w1ttG1Y0HwQgZY7$2bc665900c21f184dc37592c7d145f409824d355a49c84b196a7495e167ed5c5209d3d7444b20ea6ea50f2338a89ac43758caeaa7403a910257932d58a15e30b','barangay_user',NULL,9,'Barangay Captain','2026-07-23 04:36:56',1,NULL,NULL),
(20,'Corazon Fernandez','cayambanan.urdaneta@reliefline.gov.ph','scrypt:32768:8:1$yzkCRZ7HMLoGVQ3t$129c5a4d3eb778e4fee20c93afb6d89ab0c203051e0527d503cc63eb553036c73dedef4c0a70db28b26925cec681bf86ab7420aee6116ec4f56b79316d4534c3','barangay_user',NULL,10,'Barangay Captain','2026-07-23 04:36:56',1,NULL,NULL),
(21,'Alberto Garcia','abot.santabarbara@reliefline.gov.ph','scrypt:32768:8:1$D1CBugYk6TVGTZlD$a1d7fa065e63c7e8643f717e5aa35ebcb710dcb17082239b89271a608fd48495456d7471d3b25cced7e9ffa4029732792f6fed7ee1980f2a7fcb7ec843793dc6','barangay_user',NULL,11,'Barangay Captain','2026-07-23 04:36:56',1,NULL,NULL),
(22,'Leonora Torres','banao.santabarbara@reliefline.gov.ph','scrypt:32768:8:1$vtVncBlWCagHfruS$4d62b454f34b68ecaba5b644b55dc0881403edb0b742b5e10cc96cabcf5685dc9b19e4adcf160ed8dab2995abafb05b5c031512ef37be5c10e4f81f5f79bec23','barangay_user',NULL,12,'Barangay Captain','2026-07-23 04:36:56',1,NULL,NULL),
(23,'Rodrigo Castillo','batayang.santabarbara@reliefline.gov.ph','scrypt:32768:8:1$bz0M9xcEE6nPgAKG$ca5df47b9449687103a689cc26de6ce2ce60369d2ea5784984c2390ade872e10a3f3b79eb5f864ea69dd34b2da69f6a50d1c1683778fae031b2ea16ae16a92d2','barangay_user',NULL,13,'Barangay Captain','2026-07-23 04:36:56',1,NULL,NULL),
(24,'Imelda Navarro','bungallon.santabarbara@reliefline.gov.ph','scrypt:32768:8:1$SqMHJswOxfoLl3h1$120b9159d7947f71a4b57195c17df496b4cc01d80f536668711bb276cbb69c525e0c7f40dc44e8b5700e9634308604ad79fcb249234ead6d55b98dd7939dada8','barangay_user',NULL,14,'Barangay Captain','2026-07-23 04:36:56',1,NULL,NULL),
(25,'Bienvenido Pascual','calepaan.santabarbara@reliefline.gov.ph','scrypt:32768:8:1$bQ75NS3Lme7vxjWN$c03248699c538c950f3deaeed737366098c2383c6ce9648b740a85c22b599eda76de6f3b64d4f3367e7e72f5aa0b572398ace7baa1bd146fb48a6074a2696593','barangay_user',NULL,15,'Barangay Captain','2026-07-23 04:36:56',1,NULL,NULL),
(26,'Nenita Ocampo','carosucannorte.santabarbara@reliefline.gov.ph','scrypt:32768:8:1$awpylHt4QUkieEUX$de0bb1be5427e9807f0d5e39e2990406d8ef47ca1b12c8ab99f9f496c9a386556b4b3949e49b55ef49ccccdb7092f725bdfef60995148bbc9dfd2117b84015bb','barangay_user',NULL,16,'Barangay Captain','2026-07-23 04:36:56',1,NULL,NULL),
(27,'Wilfredo Salazar','carosucansur.santabarbara@reliefline.gov.ph','scrypt:32768:8:1$PbINXkDwpM4o1ofa$50007d9b23e65a428cc96183ecf6c6d2bb0f9233e08722c71c709fe6bb93734401d580d6eb37b353b80a0c7a6bf9b92d07d8e0a26f080489a33c901699849424','barangay_user',NULL,17,'Barangay Captain','2026-07-23 04:36:56',1,'2026-07-23 05:22:11','2026-07-23 05:22:11'),
(28,'Adelaida Gonzales','coliling.santabarbara@reliefline.gov.ph','scrypt:32768:8:1$2jcwsFCZpplpF91I$8c9052e1ffe2cfc022aa03deb46d80a4748371a80c10dcebccbde1f1f544a33a00341adfedd8bfb11776b7d31e8c8e6b11e84849a3079a8284008db5287b3f62','barangay_user',NULL,18,'Barangay Captain','2026-07-23 04:36:56',1,NULL,NULL),
(29,'Rustico Del Rosario','hacienda.santabarbara@reliefline.gov.ph','scrypt:32768:8:1$OcnNyuwuWadZfTkJ$fde2dca3935704f0d712f78eb1ba23c584f7d4f68e6e1fb3f2701a9577f6e955a16f97019e81bd33d6b53b64923ff5f472ee482044d06f8d252d976e3e72273d','barangay_user',NULL,19,'Barangay Captain','2026-07-23 04:36:56',1,NULL,NULL),
(30,'Herminia Flores','mapolopolo.santabarbara@reliefline.gov.ph','scrypt:32768:8:1$ZWdNC65VnilRbPfm$1fdc51b74b82d70f607992e22fd010fa8f73b5df035cc7c9efe090997ab4518fd3ea9bcf914e1bc55f7684a46e2ca0efa3150b0989686c40aba64a59970f3be5','barangay_user',NULL,20,'Barangay Captain','2026-07-23 04:36:56',1,NULL,NULL),
(31,'Renato Marquez','ambonao.calasiao@reliefline.gov.ph','scrypt:32768:8:1$jE7FaRabd0KYYvFR$90384bf78927019175780537b8497b0ee7f96083413df22a33121c21067d78e259d7749c5f4344494f4ce9b41836fc195f45bae7652c64ebff59e21ce836b833','barangay_user',NULL,21,'Barangay Captain','2026-07-23 04:36:56',1,NULL,NULL),
(32,'Purificacion Ignacio','ambuetel.calasiao@reliefline.gov.ph','scrypt:32768:8:1$EHE90htnCSoHZ4Qm$983234cd7f30bd38ad8516c31c53c7b0d2cedb448a107206f5357fcd41714d257f6283b640ca81a6baf38a7336661ddafa79c220a2c47c1d1ffa0ddaecb97abd','barangay_user',NULL,22,'Barangay Captain','2026-07-23 04:36:56',1,NULL,NULL),
(33,'Jose Reyes','banaoang.calasiao@reliefline.gov.ph','scrypt:32768:8:1$av0BXelksBW841He$9f0dfe5394bc8ef8501a616cf22802839b0424c558113209c7acba5a49d36b18db256147e169016d54b3bf03872110aac161d08334ce6508019dd84640d37692','barangay_user',NULL,23,'Barangay Captain','2026-07-23 04:36:56',1,'2026-07-23 06:10:28','2026-07-23 06:10:28'),
(34,'Esperanza Rivera','bued.calasiao@reliefline.gov.ph','scrypt:32768:8:1$mnBTOaysNoBYqvXI$b557ef44e439d96b4fab661e5cd26f72c96964051c6eb74948643a2c79617e33dec22d185bba3b9b77663beda676f3d4f82bee4464d39038b0c16fe97040711c','barangay_user',NULL,24,'Barangay Captain','2026-07-23 04:36:56',1,NULL,NULL),
(35,'Nestor Agustin','buenlag.calasiao@reliefline.gov.ph','scrypt:32768:8:1$MNxFcFoKNyhpyIqs$175622ecd2f60f45bdbca2c968a7319548b3b1b1fca9a856d481ddc51f54c3a459766e72606617d3e5ab087e104238709eb53933c8edda177736074b960ebf7b','barangay_user',NULL,25,'Barangay Captain','2026-07-23 04:36:56',1,NULL,NULL),
(36,'Lourdes Panganiban','cabilocaan.calasiao@reliefline.gov.ph','scrypt:32768:8:1$cZGGpe2sMbFrmDib$220cfc0f2fc2964b2c217ab96dfbcbd186b33e8667e2af8a8cff3ddd4a99067ae32e01645e6b3eb9c49627ee173f06197b0fd6f20ee1e57dc245c2fe1ee000c9','barangay_user',NULL,26,'Barangay Captain','2026-07-23 04:36:56',1,NULL,NULL),
(37,'Cirilo Bernardo','dinalaoan.calasiao@reliefline.gov.ph','scrypt:32768:8:1$mc85Dtx7ldVdBQ1X$8a3337491083a92084a8c787891d481c2a79715e2c464282a4b9a2fbceb8912dfba7c01a2fe4b13416c3edb71484edb5927b34917122d0813d6b8e142eaeb4d8','barangay_user',NULL,27,'Barangay Captain','2026-07-23 04:36:56',1,NULL,NULL),
(38,'Julieta Enriquez','doyong.calasiao@reliefline.gov.ph','scrypt:32768:8:1$SKO0jXiQWnPrLBQ9$e5c4c76eb200b963dde29a21a0edf863f1b3a5750a6122239b1a3f01d3222d1ca247af9d835e613c7d861b40ecc0fa344868c9032d70d6aee264971d279b9524','barangay_user',NULL,28,'Barangay Captain','2026-07-23 04:36:56',1,NULL,NULL),
(39,'Bonifacio Lazaro','gabon.calasiao@reliefline.gov.ph','scrypt:32768:8:1$NQCEw9ZVNjHrqYdJ$fc0eb088aaddd126c055ce620770f4996fb56fdb552cb8fa964584cb3eabdea4124f929500626051c06bc4e2a6146934ea47a956bed2c52a12a14153c496538d','barangay_user',NULL,29,'Barangay Captain','2026-07-23 04:36:56',1,NULL,NULL),
(40,'Remedios Corpuz','lasip.calasiao@reliefline.gov.ph','scrypt:32768:8:1$hyCPITc545JSxO1x$719cb05c28fedbedbde1880e2d0e984444b07779f72127c4d5ffb0de5c52c0014de6424444b0e474cb73e54d0a332e99e6a73cb7b99070af399f8b70adb5733f','barangay_user',NULL,30,'Barangay Captain','2026-07-23 04:36:56',1,NULL,NULL);
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;

--
-- Table structure for table `vehicles`
--

DROP TABLE IF EXISTS `vehicles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `vehicles` (
  `vehicle_id` int(11) NOT NULL AUTO_INCREMENT,
  `vehicle_name` varchar(100) NOT NULL,
  `office_id` int(11) DEFAULT NULL,
  `plate_number` varchar(20) DEFAULT NULL,
  `capacity_packs` int(11) DEFAULT NULL,
  PRIMARY KEY (`vehicle_id`),
  KEY `office_id` (`office_id`),
  CONSTRAINT `vehicles_ibfk_1` FOREIGN KEY (`office_id`) REFERENCES `offices` (`office_id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `vehicles`
--

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `vehicles` WRITE;
/*!40000 ALTER TABLE `vehicles` DISABLE KEYS */;
INSERT INTO `vehicles` VALUES
(4,'Truck 001',5,'ABC-1234',2000),
(5,'Truck 002',5,'DEF-5678',1500),
(6,'Truck 003',5,'GHI-9012',1800);
/*!40000 ALTER TABLE `vehicles` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;

--
-- Table structure for table `warehouse_inventory`
--

DROP TABLE IF EXISTS `warehouse_inventory`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `warehouse_inventory` (
  `inventory_id` int(11) NOT NULL AUTO_INCREMENT,
  `office_id` int(11) NOT NULL,
  `item_type` varchar(50) NOT NULL,
  `item_name` varchar(100) NOT NULL DEFAULT 'Food Packs',
  `unit` varchar(20) NOT NULL DEFAULT 'packs',
  `quantity_available` int(11) NOT NULL DEFAULT 0,
  `min_stock_level` int(11) NOT NULL DEFAULT 0,
  `last_updated` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `updated_by` int(11) DEFAULT NULL,
  PRIMARY KEY (`inventory_id`),
  KEY `office_id` (`office_id`),
  KEY `updated_by` (`updated_by`),
  CONSTRAINT `warehouse_inventory_ibfk_1` FOREIGN KEY (`office_id`) REFERENCES `offices` (`office_id`) ON DELETE CASCADE,
  CONSTRAINT `warehouse_inventory_ibfk_2` FOREIGN KEY (`updated_by`) REFERENCES `users` (`user_id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `warehouse_inventory`
--

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `warehouse_inventory` WRITE;
/*!40000 ALTER TABLE `warehouse_inventory` DISABLE KEYS */;
INSERT INTO `warehouse_inventory` VALUES
(1,1,'food_pack','Food Packs','packs',5000,0,'2026-07-17 12:23:28',2),
(2,1,'hygiene_kit','Hygiene Kits','kits',1200,0,'2026-07-20 02:49:52',2),
(3,1,'kitchen_kit','Kitchen Kits','kits',800,0,'2026-07-20 02:49:52',2),
(4,2,'food_pack','Food Packs','packs',500,0,'2026-07-20 02:52:05',3),
(5,2,'hygiene_kit','Hygiene Kits','kits',400,0,'2026-07-20 02:49:52',3),
(6,2,'kitchen_kit','Kitchen Kits','kits',200,0,'2026-07-20 02:49:52',3),
(7,3,'food_pack','Food Packs','packs',1200,0,'2026-06-25 10:39:04',4),
(8,3,'hygiene_kit','Hygiene Kits','kits',300,0,'2026-07-20 02:49:52',4),
(9,3,'kitchen_kit','Kitchen Kits','kits',150,0,'2026-07-20 02:49:52',4),
(10,4,'food_pack','Food Packs','packs',1800,0,'2026-06-25 10:39:04',5),
(11,4,'hygiene_kit','Hygiene Kits','kits',500,0,'2026-07-20 02:49:52',5),
(12,4,'kitchen_kit','Kitchen Kits','kits',250,0,'2026-07-20 02:49:52',5),
(13,5,'food_pack','Food Packs','packs',12200,3000,'2026-07-20 07:03:37',NULL);
/*!40000 ALTER TABLE `warehouse_inventory` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;

--
-- Table structure for table `warehouse_stock_logs`
--

DROP TABLE IF EXISTS `warehouse_stock_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `warehouse_stock_logs` (
  `log_id` int(11) NOT NULL AUTO_INCREMENT,
  `office_id` int(11) NOT NULL,
  `item_type` varchar(50) NOT NULL,
  `item_name` varchar(100) NOT NULL,
  `delta` int(11) NOT NULL,
  `reason` varchar(255) DEFAULT NULL,
  `updated_by` int(11) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`log_id`),
  KEY `office_id` (`office_id`),
  KEY `updated_by` (`updated_by`),
  CONSTRAINT `warehouse_stock_logs_ibfk_1` FOREIGN KEY (`office_id`) REFERENCES `offices` (`office_id`) ON DELETE CASCADE,
  CONSTRAINT `warehouse_stock_logs_ibfk_2` FOREIGN KEY (`updated_by`) REFERENCES `users` (`user_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `warehouse_stock_logs`
--

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `warehouse_stock_logs` WRITE;
/*!40000 ALTER TABLE `warehouse_stock_logs` DISABLE KEYS */;
/*!40000 ALTER TABLE `warehouse_stock_logs` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;

--
-- Table structure for table `warehouse_transfers`
--

DROP TABLE IF EXISTS `warehouse_transfers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `warehouse_transfers` (
  `transfer_id` int(11) NOT NULL AUTO_INCREMENT,
  `from_office_id` int(11) NOT NULL,
  `to_office_id` int(11) NOT NULL,
  `item_type` enum('food_pack','hygiene_kit','kitchen_kit') DEFAULT 'food_pack',
  `quantity` int(11) NOT NULL,
  `status` enum('pending','completed','cancelled') DEFAULT 'pending',
  `requested_by` int(11) DEFAULT NULL,
  `requested_at` datetime DEFAULT current_timestamp(),
  `completed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`transfer_id`),
  KEY `from_office_id` (`from_office_id`),
  KEY `to_office_id` (`to_office_id`),
  KEY `requested_by` (`requested_by`),
  CONSTRAINT `warehouse_transfers_ibfk_1` FOREIGN KEY (`from_office_id`) REFERENCES `offices` (`office_id`) ON DELETE CASCADE,
  CONSTRAINT `warehouse_transfers_ibfk_2` FOREIGN KEY (`to_office_id`) REFERENCES `offices` (`office_id`) ON DELETE CASCADE,
  CONSTRAINT `warehouse_transfers_ibfk_3` FOREIGN KEY (`requested_by`) REFERENCES `users` (`user_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `warehouse_transfers`
--

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `warehouse_transfers` WRITE;
/*!40000 ALTER TABLE `warehouse_transfers` DISABLE KEYS */;
/*!40000 ALTER TABLE `warehouse_transfers` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*M!100616 SET NOTE_VERBOSITY=@OLD_NOTE_VERBOSITY */;

-- Dump completed on 2026-07-23  7:49:45
