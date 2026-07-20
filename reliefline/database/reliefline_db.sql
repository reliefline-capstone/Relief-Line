-- phpMyAdmin SQL Dump
-- version 5.2.3
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Jul 18, 2026 at 06:47 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `reliefline_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `activity_logs`
--

CREATE TABLE `activity_logs` (
  `log_id` int(11) NOT NULL,
  `actor_id` int(11) DEFAULT NULL,
  `action_type` varchar(50) NOT NULL,
  `description` varchar(255) NOT NULL,
  `is_read` tinyint(1) NOT NULL DEFAULT 0,
  `office_id` int(11) DEFAULT NULL,
  `barangay_id` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `activity_logs`
--

INSERT INTO `activity_logs` (`log_id`, `actor_id`, `action_type`, `description`, `is_read`, `office_id`, `barangay_id`, `created_at`) VALUES
(3, 2, 'allocation_approved', 'Approved 2,300 food packs for Urdaneta City from Warehouse A', 1, 5, 1, '2026-07-16 21:35:28'),
(4, 2, 'distribution_delivered', 'D-2026-005 delivered to Urdaneta City, received by Aivan Flores', 1, 5, 1, '2026-07-16 21:35:28'),
(5, 2, 'allocation_approved', 'Approved 900 food packs for Santa Barbara from Warehouse A', 1, 5, 15, '2026-07-16 21:35:28'),
(6, 2, 'distribution_status', 'Distribution marked In Transit for Bactad East, Urdaneta City', 1, 5, 2, '2026-07-16 21:35:28'),
(7, 2, 'allocation_rejected', 'Rejected relief request from Urdaneta City: adequate stock on hand', 1, 5, 5, '2026-07-16 21:35:28'),
(8, 2, 'distribution_status', 'D-2026-009 marked Loaded', 1, 5, 30, '2026-07-16 21:45:02'),
(9, 2, 'distribution_status', 'D-2026-009 marked Dispatched', 1, 5, 30, '2026-07-16 21:45:02'),
(10, 2, 'distribution_status', 'D-2026-009 marked In Transit', 1, 5, 30, '2026-07-16 21:45:02'),
(11, 2, 'distribution_delivered', 'D-2026-009 delivered to Calasiao, received by Test Recipient', 1, 5, 30, '2026-07-16 21:45:02');

-- --------------------------------------------------------

--
-- Table structure for table `allocation_records`
--

CREATE TABLE `allocation_records` (
  `allocation_id` int(11) NOT NULL,
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
  `decided_by` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `allocation_records`
--

INSERT INTO `allocation_records` (`allocation_id`, `barangay_id`, `office_id`, `predicted_quantity`, `allocated_quantity`, `historical_allocation`, `allocation_date`, `disaster_event`, `event_id`, `status`, `created_by`, `created_at`, `rejection_reason`, `fulfilling_office_id`, `expected_delivery_date`, `remarks`, `decided_by`) VALUES
(8, 1, 2, 2300, 2300, 0, '2026-07-16', NULL, 1, 'approved', 2, '2026-07-17 13:35:28', NULL, 5, '2026-07-19', NULL, 2),
(9, 2, 2, 1500, 1500, 0, '2026-07-16', NULL, 1, 'approved', 2, '2026-07-17 13:35:28', NULL, 5, '2026-07-19', NULL, 2),
(10, 15, 3, 900, 900, 0, '2026-07-16', NULL, 1, 'approved', 2, '2026-07-17 13:35:28', NULL, 5, '2026-07-19', NULL, 2),
(11, 18, 3, 600, 600, 0, '2026-07-16', NULL, 1, 'approved', 2, '2026-07-17 13:35:28', NULL, 5, '2026-07-19', NULL, 2),
(12, 30, 4, 1800, 1800, 0, '2026-07-16', NULL, 1, 'approved', 2, '2026-07-17 13:35:28', NULL, 5, '2026-07-19', NULL, 2),
(13, 26, 4, 1200, 1200, 0, '2026-07-16', NULL, 1, 'approved', 2, '2026-07-17 13:35:28', NULL, 5, '2026-07-19', NULL, 2),
(14, 28, 4, 1100, 1100, 0, '2026-07-16', NULL, 1, 'approved', 2, '2026-07-17 13:35:28', NULL, 5, '2026-07-19', NULL, 2),
(15, 3, 2, 1000, 0, 0, '2026-07-16', NULL, 1, 'pending', NULL, '2026-07-17 13:35:28', NULL, NULL, NULL, NULL, NULL),
(16, 12, 3, 700, 0, 0, '2026-07-16', NULL, 1, 'pending', NULL, '2026-07-17 13:35:28', NULL, NULL, NULL, NULL, NULL),
(17, 23, 4, 500, 300, 0, '2026-07-16', NULL, 1, 'approved', 2, '2026-07-17 13:35:28', NULL, 5, '2026-07-18', NULL, 2),
(18, 5, 2, 800, 0, 0, '2026-07-16', NULL, 1, 'pending', NULL, '2026-07-17 13:35:28', 'Municipal warehouse already has adequate stock for this barangay; redirected to Bayaoas instead.', NULL, NULL, NULL, 2);

-- --------------------------------------------------------

--
-- Table structure for table `barangays`
--

CREATE TABLE `barangays` (
  `barangay_id` int(11) NOT NULL,
  `barangay_name` varchar(100) NOT NULL,
  `city_municipality` varchar(100) NOT NULL,
  `population` int(11) NOT NULL DEFAULT 0,
  `num_households` int(11) NOT NULL DEFAULT 0,
  `poverty_incidence` decimal(5,2) NOT NULL DEFAULT 0.00,
  `disaster_risk_index` decimal(4,2) NOT NULL DEFAULT 0.00,
  `past_calamity_freq` int(11) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `barangays`
--

INSERT INTO `barangays` (`barangay_id`, `barangay_name`, `city_municipality`, `population`, `num_households`, `poverty_incidence`, `disaster_risk_index`, `past_calamity_freq`) VALUES
(1, 'Anonas', 'Urdaneta City', 3200, 640, 32.50, 6.50, 5),
(2, 'Bactad East', 'Urdaneta City', 4100, 820, 28.00, 5.80, 4),
(3, 'Bayaoas', 'Urdaneta City', 2800, 560, 40.00, 7.20, 7),
(4, 'Bolaoen', 'Urdaneta City', 1900, 380, 35.00, 6.00, 4),
(5, 'Cabaruan', 'Urdaneta City', 2500, 500, 38.50, 7.80, 6),
(6, 'Cabuloan', 'Urdaneta City', 3600, 720, 30.00, 5.50, 5),
(7, 'Camantiles', 'Urdaneta City', 1500, 300, 45.00, 8.00, 8),
(8, 'Casantaan', 'Urdaneta City', 2100, 420, 33.00, 6.30, 5),
(9, 'Catablan', 'Urdaneta City', 2700, 540, 29.50, 5.90, 4),
(10, 'Cayambanan', 'Urdaneta City', 1800, 360, 42.00, 7.50, 6),
(11, 'Abot', 'Santa Barbara', 1600, 320, 38.00, 6.80, 5),
(12, 'Ban-ao', 'Santa Barbara', 2200, 440, 31.50, 5.70, 4),
(13, 'Batayang', 'Santa Barbara', 1900, 380, 36.00, 7.00, 6),
(14, 'Bungallon', 'Santa Barbara', 2800, 560, 27.00, 5.20, 3),
(15, 'Calepaan', 'Santa Barbara', 1400, 280, 44.50, 8.10, 7),
(16, 'Carosucan Norte', 'Santa Barbara', 2100, 420, 33.50, 6.40, 5),
(17, 'Carosucan Sur', 'Santa Barbara', 1700, 340, 37.00, 6.90, 5),
(18, 'Coliling', 'Santa Barbara', 1300, 260, 46.00, 8.30, 8),
(19, 'Hacienda', 'Santa Barbara', 2500, 500, 29.00, 5.60, 4),
(20, 'Mapolopolo', 'Santa Barbara', 1100, 220, 50.00, 8.80, 9),
(21, 'Ambonao', 'Calasiao', 3800, 760, 26.00, 5.10, 3),
(22, 'Ambuetel', 'Calasiao', 2300, 460, 34.00, 6.60, 5),
(23, 'Banaoang', 'Calasiao', 1700, 340, 39.00, 7.30, 6),
(24, 'Bued', 'Calasiao', 4200, 840, 24.50, 4.90, 3),
(25, 'Buenlag', 'Calasiao', 2900, 580, 30.50, 5.80, 4),
(26, 'Cabilocaan', 'Calasiao', 1500, 300, 43.00, 7.90, 7),
(27, 'Dinalaoan', 'Calasiao', 2000, 400, 36.50, 6.70, 5),
(28, 'Doyong', 'Calasiao', 1800, 360, 41.00, 7.60, 6),
(29, 'Gabon', 'Calasiao', 2600, 520, 28.50, 5.40, 4),
(30, 'Lasip', 'Calasiao', 1200, 240, 48.00, 8.50, 8);

-- --------------------------------------------------------

--
-- Table structure for table `barangay_disaster_status`
--

CREATE TABLE `barangay_disaster_status` (
  `status_id` int(11) NOT NULL,
  `event_id` int(11) NOT NULL,
  `barangay_id` int(11) NOT NULL,
  `status` enum('normal','monitoring','needs_assistance','high_priority') DEFAULT 'normal',
  `affected_families` int(11) NOT NULL DEFAULT 0,
  `updated_by` int(11) DEFAULT NULL,
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `barangay_disaster_status`
--

INSERT INTO `barangay_disaster_status` (`status_id`, `event_id`, `barangay_id`, `status`, `affected_families`, `updated_by`, `updated_at`) VALUES
(1, 1, 1, 'high_priority', 1200, 2, '2026-07-17 05:35:28'),
(2, 1, 2, 'needs_assistance', 800, 2, '2026-07-17 05:35:28'),
(3, 1, 3, 'monitoring', 400, 2, '2026-07-17 05:35:28'),
(4, 1, 5, 'needs_assistance', 600, 2, '2026-07-17 05:35:28'),
(5, 1, 15, 'high_priority', 900, 2, '2026-07-17 05:35:28'),
(6, 1, 18, 'needs_assistance', 600, 2, '2026-07-17 05:35:28'),
(7, 1, 12, 'monitoring', 300, 2, '2026-07-17 05:35:28'),
(8, 1, 30, 'high_priority', 700, 2, '2026-07-17 05:35:28'),
(9, 1, 26, 'needs_assistance', 500, 2, '2026-07-17 05:35:28'),
(10, 1, 28, 'monitoring', 350, 2, '2026-07-17 05:35:28'),
(11, 1, 23, 'monitoring', 250, 2, '2026-07-17 05:35:28');

-- --------------------------------------------------------

--
-- Table structure for table `city_demand_summary`
--

CREATE TABLE `city_demand_summary` (
  `summary_id` int(11) NOT NULL,
  `city_municipality` varchar(100) NOT NULL,
  `total_barangays` int(11) NOT NULL DEFAULT 0,
  `total_projected_demand` int(11) NOT NULL DEFAULT 0,
  `total_historical_allocation` int(11) NOT NULL DEFAULT 0,
  `total_available_stock` int(11) NOT NULL DEFAULT 0,
  `demand_level` enum('low','moderate','high','critical') NOT NULL DEFAULT 'low',
  `generated_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `daily_ops_stats`
--

CREATE TABLE `daily_ops_stats` (
  `stat_id` int(11) NOT NULL,
  `office_id` int(11) NOT NULL,
  `stat_date` date NOT NULL,
  `vehicles_active` int(11) DEFAULT 0,
  `updated_by` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `daily_ops_stats`
--

INSERT INTO `daily_ops_stats` (`stat_id`, `office_id`, `stat_date`, `vehicles_active`, `updated_by`) VALUES
(1, 2, '2026-07-17', 1, 2),
(2, 3, '2026-07-17', 1, 2),
(3, 4, '2026-07-17', 1, 2);

-- --------------------------------------------------------

--
-- Table structure for table `disaster_events`
--

CREATE TABLE `disaster_events` (
  `event_id` int(11) NOT NULL,
  `event_name` varchar(150) NOT NULL,
  `event_type` enum('typhoon','flood','other') DEFAULT 'typhoon',
  `status` enum('active','monitoring','ended') DEFAULT 'active',
  `weather_condition` varchar(50) DEFAULT NULL,
  `start_date` date NOT NULL,
  `end_date` date DEFAULT NULL,
  `created_by` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `disaster_events`
--

INSERT INTO `disaster_events` (`event_id`, `event_name`, `event_type`, `status`, `weather_condition`, `start_date`, `end_date`, `created_by`, `created_at`) VALUES
(1, 'Typhoon Crising', 'typhoon', 'active', 'Thunderstorm', '2026-07-10', NULL, 1, '2026-07-10 05:08:52');

-- --------------------------------------------------------

--
-- Table structure for table `distribution_records`
--

CREATE TABLE `distribution_records` (
  `distribution_id` int(11) NOT NULL,
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
  `travel_time` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `distribution_records`
--

INSERT INTO `distribution_records` (`distribution_id`, `barangay_id`, `allocation_id`, `quantity_released`, `distribution_date`, `validation_type`, `validation_file`, `submitted_by`, `status`, `submitted_at`, `vehicle_id`, `driver_id`, `dispatch_status`, `departure_time`, `expected_arrival_time`, `received_by`, `time_received`, `condition`, `travel_time`) VALUES
(5, 1, 8, 2300, '2026-07-17', NULL, NULL, 2, 'confirmed', '2026-07-17 13:35:28', 4, 4, 'delivered', '08:00:00', '10:30:00', 'Aivan Flores', NULL, 'complete', '2 hrs 30 mins'),
(6, 2, 9, 1500, '2026-07-17', NULL, NULL, 2, 'pending', '2026-07-17 13:35:28', 5, 5, 'in_transit', '07:30:00', '09:45:00', NULL, NULL, NULL, NULL),
(7, 15, 10, 900, '2026-07-17', NULL, NULL, 2, 'pending', '2026-07-17 13:35:28', 6, 6, 'dispatched', '09:00:00', '11:15:00', NULL, NULL, NULL, NULL),
(8, 18, 11, 600, '2026-07-17', NULL, NULL, 2, 'pending', '2026-07-17 13:35:28', 5, 5, 'loaded', NULL, NULL, NULL, NULL, NULL, NULL),
(9, 30, 12, 1800, '2026-07-17', 'photo', 'delivery_receipt_test.pdf', 2, 'confirmed', '2026-07-17 13:35:28', 5, 5, 'delivered', '13:45:02', NULL, 'Test Recipient', '15:15:00', 'complete', '1 hr 45 mins'),
(10, 26, 13, 1200, '2026-07-17', NULL, NULL, 2, 'pending', '2026-07-17 13:35:28', NULL, NULL, 'delayed', NULL, NULL, NULL, NULL, NULL, NULL),
(11, 28, 14, 1100, '2026-07-17', NULL, NULL, 2, 'confirmed', '2026-07-17 13:35:28', 4, 4, 'delivered', '06:45:00', '09:00:00', 'Maria Santos', NULL, 'complete', '2 hrs 15 mins');

-- --------------------------------------------------------

--
-- Table structure for table `drivers`
--

CREATE TABLE `drivers` (
  `driver_id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `office_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `drivers`
--

INSERT INTO `drivers` (`driver_id`, `name`, `office_id`) VALUES
(4, 'Juan Dela Cruz', 5),
(5, 'Pedro Santos', 5),
(6, 'Mark Reyes', 5);

-- --------------------------------------------------------

--
-- Table structure for table `model_metrics`
--

CREATE TABLE `model_metrics` (
  `metric_id` int(11) NOT NULL,
  `model_version` varchar(50) NOT NULL DEFAULT 'v1.0',
  `mae` decimal(10,4) DEFAULT NULL,
  `rmse` decimal(10,4) DEFAULT NULL,
  `mape` decimal(10,4) DEFAULT NULL,
  `r_squared` decimal(10,4) DEFAULT NULL,
  `training_samples` int(11) DEFAULT NULL,
  `trained_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `offices`
--

CREATE TABLE `offices` (
  `office_id` int(11) NOT NULL,
  `office_name` varchar(100) NOT NULL,
  `office_type` enum('pswdo','cswdo','barangay') NOT NULL,
  `area_covered` varchar(100) NOT NULL,
  `capacity_food_pack` int(11) NOT NULL DEFAULT 20000,
  `full_address` varchar(255) DEFAULT NULL,
  `manager_name` varchar(100) DEFAULT NULL,
  `contact_number` varchar(20) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `offices`
--

INSERT INTO `offices` (`office_id`, `office_name`, `office_type`, `area_covered`, `capacity_food_pack`) VALUES
(1, 'Provincial Social Welfare and Development Office', 'pswdo', 'Province of Pangasinan', 20000),
(2, 'Urdaneta City Social Welfare and Development Office', 'cswdo', 'Urdaneta City', 22000),
(3, 'Santa Barbara Municipal Social Welfare and Development Office', 'cswdo', 'Santa Barbara', 20000),
(4, 'Calasiao Municipal Social Welfare and Development Office', 'cswdo', 'Calasiao', 18000),
(5, 'Warehouse A', 'pswdo', 'Lingayen', 22000),
(6, 'Warehouse C', 'pswdo', 'Alaminos', 18000);

-- --------------------------------------------------------

--
-- Table structure for table `prediction_logs`
--

CREATE TABLE `prediction_logs` (
  `log_id` int(11) NOT NULL,
  `barangay_id` int(11) NOT NULL,
  `predicted_quantity` int(11) NOT NULL,
  `input_snapshot` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`input_snapshot`)),
  `predicted_at` datetime DEFAULT current_timestamp(),
  `model_version` varchar(50) DEFAULT 'v1.0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `prediction_logs`
--

INSERT INTO `prediction_logs` (`log_id`, `barangay_id`, `predicted_quantity`, `input_snapshot`, `predicted_at`, `model_version`) VALUES
(1, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-06-30 11:33:59', 'v1.0'),
(2, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-06-30 11:33:59', 'v1.0'),
(3, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-06-30 11:33:59', 'v1.0'),
(4, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-06-30 11:33:59', 'v1.0'),
(5, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-06-30 11:33:59', 'v1.0'),
(6, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-06-30 11:33:59', 'v1.0'),
(7, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-06-30 11:33:59', 'v1.0'),
(8, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-06-30 11:33:59', 'v1.0'),
(9, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-06-30 11:33:59', 'v1.0'),
(10, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-06-30 11:33:59', 'v1.0'),
(11, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-06-30 11:33:59', 'v1.0'),
(12, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-06-30 11:33:59', 'v1.0'),
(13, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-06-30 11:33:59', 'v1.0'),
(14, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-06-30 11:33:59', 'v1.0'),
(15, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-06-30 11:33:59', 'v1.0'),
(16, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-06-30 11:33:59', 'v1.0'),
(17, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-06-30 11:33:59', 'v1.0'),
(18, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-06-30 11:33:59', 'v1.0'),
(19, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-06-30 11:33:59', 'v1.0'),
(20, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-06-30 11:33:59', 'v1.0'),
(21, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-06-30 11:33:59', 'v1.0'),
(22, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-06-30 11:33:59', 'v1.0'),
(23, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-06-30 11:33:59', 'v1.0'),
(24, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-06-30 11:33:59', 'v1.0'),
(25, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-06-30 11:33:59', 'v1.0'),
(26, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-06-30 11:33:59', 'v1.0'),
(27, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-06-30 11:33:59', 'v1.0'),
(28, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-06-30 11:33:59', 'v1.0'),
(29, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-06-30 11:33:59', 'v1.0'),
(30, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-06-30 11:33:59', 'v1.0'),
(31, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-06-30 11:37:22', 'v1.0'),
(32, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-06-30 11:37:22', 'v1.0'),
(33, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-06-30 11:37:22', 'v1.0'),
(34, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-06-30 11:37:22', 'v1.0'),
(35, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-06-30 11:37:22', 'v1.0'),
(36, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-06-30 11:37:22', 'v1.0'),
(37, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-06-30 11:37:22', 'v1.0'),
(38, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-06-30 11:37:22', 'v1.0'),
(39, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-06-30 11:37:22', 'v1.0'),
(40, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-06-30 11:37:22', 'v1.0'),
(41, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-06-30 11:37:22', 'v1.0'),
(42, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-06-30 11:37:22', 'v1.0'),
(43, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-06-30 11:37:22', 'v1.0'),
(44, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-06-30 11:37:22', 'v1.0'),
(45, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-06-30 11:37:22', 'v1.0'),
(46, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-06-30 11:37:22', 'v1.0'),
(47, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-06-30 11:37:22', 'v1.0'),
(48, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-06-30 11:37:22', 'v1.0'),
(49, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-06-30 11:37:22', 'v1.0'),
(50, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-06-30 11:37:22', 'v1.0'),
(51, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-06-30 11:37:22', 'v1.0'),
(52, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-06-30 11:37:22', 'v1.0'),
(53, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-06-30 11:37:22', 'v1.0'),
(54, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-06-30 11:37:22', 'v1.0'),
(55, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-06-30 11:37:22', 'v1.0'),
(56, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-06-30 11:37:22', 'v1.0'),
(57, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-06-30 11:37:22', 'v1.0'),
(58, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-06-30 11:37:22', 'v1.0'),
(59, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-06-30 11:37:22', 'v1.0'),
(60, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-06-30 11:37:22', 'v1.0'),
(61, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 12:40:48', 'v1.0'),
(62, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 12:40:48', 'v1.0'),
(63, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 12:40:48', 'v1.0'),
(64, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 12:40:48', 'v1.0'),
(65, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 12:40:48', 'v1.0'),
(66, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 12:40:48', 'v1.0'),
(67, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 12:40:48', 'v1.0'),
(68, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 12:40:48', 'v1.0'),
(69, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 12:40:48', 'v1.0'),
(70, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 12:40:48', 'v1.0'),
(71, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 12:40:48', 'v1.0'),
(72, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 12:40:48', 'v1.0'),
(73, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 12:40:48', 'v1.0'),
(74, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 12:40:48', 'v1.0'),
(75, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 12:40:48', 'v1.0'),
(76, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 12:40:48', 'v1.0'),
(77, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 12:40:48', 'v1.0'),
(78, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 12:40:48', 'v1.0'),
(79, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 12:40:48', 'v1.0'),
(80, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 12:40:48', 'v1.0'),
(81, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 12:40:48', 'v1.0'),
(82, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 12:40:48', 'v1.0'),
(83, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 12:40:48', 'v1.0'),
(84, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 12:40:48', 'v1.0'),
(85, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 12:40:48', 'v1.0'),
(86, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 12:40:48', 'v1.0'),
(87, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 12:40:48', 'v1.0'),
(88, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 12:40:48', 'v1.0'),
(89, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 12:40:48', 'v1.0'),
(90, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 12:40:48', 'v1.0'),
(91, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 12:40:52', 'v1.0'),
(92, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 12:40:52', 'v1.0'),
(93, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 12:40:52', 'v1.0'),
(94, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 12:40:52', 'v1.0'),
(95, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 12:40:52', 'v1.0'),
(96, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 12:40:52', 'v1.0'),
(97, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 12:40:52', 'v1.0'),
(98, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 12:40:52', 'v1.0'),
(99, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 12:40:52', 'v1.0'),
(100, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 12:40:52', 'v1.0'),
(101, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 12:40:52', 'v1.0'),
(102, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 12:40:52', 'v1.0'),
(103, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 12:40:52', 'v1.0'),
(104, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 12:40:52', 'v1.0'),
(105, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 12:40:52', 'v1.0'),
(106, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 12:40:52', 'v1.0'),
(107, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 12:40:52', 'v1.0'),
(108, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 12:40:52', 'v1.0'),
(109, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 12:40:52', 'v1.0'),
(110, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 12:40:52', 'v1.0'),
(111, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 12:40:52', 'v1.0'),
(112, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 12:40:52', 'v1.0'),
(113, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 12:40:52', 'v1.0'),
(114, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 12:40:52', 'v1.0'),
(115, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 12:40:52', 'v1.0'),
(116, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 12:40:52', 'v1.0'),
(117, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 12:40:52', 'v1.0'),
(118, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 12:40:52', 'v1.0'),
(119, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 12:40:52', 'v1.0'),
(120, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 12:40:52', 'v1.0'),
(121, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 12:41:07', 'v1.0'),
(122, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 12:41:07', 'v1.0'),
(123, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 12:41:07', 'v1.0'),
(124, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 12:41:07', 'v1.0'),
(125, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 12:41:07', 'v1.0'),
(126, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 12:41:07', 'v1.0'),
(127, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 12:41:07', 'v1.0'),
(128, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 12:41:07', 'v1.0'),
(129, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 12:41:07', 'v1.0'),
(130, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 12:41:07', 'v1.0'),
(131, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 12:41:07', 'v1.0'),
(132, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 12:41:07', 'v1.0'),
(133, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 12:41:07', 'v1.0'),
(134, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 12:41:07', 'v1.0'),
(135, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 12:41:07', 'v1.0'),
(136, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 12:41:07', 'v1.0'),
(137, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 12:41:07', 'v1.0'),
(138, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 12:41:07', 'v1.0'),
(139, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 12:41:07', 'v1.0'),
(140, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 12:41:07', 'v1.0'),
(141, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 12:41:07', 'v1.0'),
(142, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 12:41:07', 'v1.0'),
(143, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 12:41:07', 'v1.0'),
(144, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 12:41:07', 'v1.0'),
(145, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 12:41:07', 'v1.0'),
(146, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 12:41:07', 'v1.0'),
(147, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 12:41:07', 'v1.0'),
(148, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 12:41:07', 'v1.0'),
(149, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 12:41:07', 'v1.0'),
(150, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 12:41:07', 'v1.0'),
(151, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 12:53:39', 'v1.0'),
(152, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 12:53:39', 'v1.0'),
(153, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 12:53:39', 'v1.0'),
(154, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 12:53:39', 'v1.0'),
(155, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 12:53:39', 'v1.0'),
(156, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 12:53:39', 'v1.0'),
(157, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 12:53:39', 'v1.0'),
(158, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 12:53:39', 'v1.0'),
(159, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 12:53:39', 'v1.0'),
(160, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 12:53:39', 'v1.0'),
(161, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 12:53:39', 'v1.0'),
(162, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 12:53:39', 'v1.0'),
(163, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 12:53:39', 'v1.0'),
(164, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 12:53:39', 'v1.0'),
(165, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 12:53:39', 'v1.0'),
(166, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 12:53:39', 'v1.0'),
(167, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 12:53:39', 'v1.0'),
(168, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 12:53:39', 'v1.0'),
(169, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 12:53:39', 'v1.0'),
(170, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 12:53:39', 'v1.0'),
(171, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 12:53:39', 'v1.0'),
(172, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 12:53:39', 'v1.0'),
(173, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 12:53:39', 'v1.0'),
(174, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 12:53:39', 'v1.0'),
(175, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 12:53:39', 'v1.0'),
(176, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 12:53:39', 'v1.0'),
(177, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 12:53:39', 'v1.0'),
(178, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 12:53:39', 'v1.0'),
(179, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 12:53:39', 'v1.0'),
(180, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 12:53:39', 'v1.0'),
(181, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:40:30', 'v1.0'),
(182, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:40:30', 'v1.0'),
(183, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:40:30', 'v1.0'),
(184, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:40:30', 'v1.0'),
(185, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:40:30', 'v1.0'),
(186, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:40:30', 'v1.0'),
(187, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:40:30', 'v1.0'),
(188, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:40:30', 'v1.0'),
(189, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:40:30', 'v1.0'),
(190, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:40:30', 'v1.0'),
(191, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:40:30', 'v1.0'),
(192, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:40:30', 'v1.0'),
(193, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:40:30', 'v1.0'),
(194, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:40:30', 'v1.0'),
(195, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:40:30', 'v1.0'),
(196, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:40:30', 'v1.0'),
(197, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:40:30', 'v1.0'),
(198, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:40:30', 'v1.0'),
(199, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:40:30', 'v1.0'),
(200, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 13:40:30', 'v1.0'),
(201, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:40:30', 'v1.0'),
(202, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:40:30', 'v1.0'),
(203, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:40:30', 'v1.0'),
(204, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:40:30', 'v1.0'),
(205, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:40:30', 'v1.0'),
(206, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:40:30', 'v1.0'),
(207, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:40:30', 'v1.0'),
(208, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:40:30', 'v1.0'),
(209, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:40:30', 'v1.0'),
(210, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:40:30', 'v1.0'),
(211, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:40:33', 'v1.0'),
(212, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:40:33', 'v1.0'),
(213, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:40:33', 'v1.0'),
(214, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:40:33', 'v1.0'),
(215, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:40:33', 'v1.0'),
(216, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:40:33', 'v1.0'),
(217, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:40:33', 'v1.0'),
(218, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:40:33', 'v1.0'),
(219, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:40:33', 'v1.0'),
(220, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:40:33', 'v1.0'),
(221, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:40:33', 'v1.0'),
(222, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:40:33', 'v1.0'),
(223, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:40:33', 'v1.0'),
(224, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:40:33', 'v1.0'),
(225, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:40:33', 'v1.0'),
(226, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:40:33', 'v1.0'),
(227, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:40:33', 'v1.0'),
(228, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:40:33', 'v1.0'),
(229, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:40:33', 'v1.0'),
(230, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 13:40:33', 'v1.0'),
(231, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:40:33', 'v1.0'),
(232, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:40:33', 'v1.0'),
(233, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:40:33', 'v1.0'),
(234, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:40:33', 'v1.0'),
(235, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:40:33', 'v1.0'),
(236, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:40:33', 'v1.0'),
(237, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:40:33', 'v1.0'),
(238, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:40:33', 'v1.0');
INSERT INTO `prediction_logs` (`log_id`, `barangay_id`, `predicted_quantity`, `input_snapshot`, `predicted_at`, `model_version`) VALUES
(239, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:40:33', 'v1.0'),
(240, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:40:33', 'v1.0'),
(241, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:42:51', 'v1.0'),
(242, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:42:51', 'v1.0'),
(243, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:42:51', 'v1.0'),
(244, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:42:51', 'v1.0'),
(245, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:42:51', 'v1.0'),
(246, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:42:51', 'v1.0'),
(247, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:42:51', 'v1.0'),
(248, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:42:51', 'v1.0'),
(249, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:42:51', 'v1.0'),
(250, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:42:51', 'v1.0'),
(251, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:42:51', 'v1.0'),
(252, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:42:51', 'v1.0'),
(253, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:42:51', 'v1.0'),
(254, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:42:51', 'v1.0'),
(255, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:42:51', 'v1.0'),
(256, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:42:51', 'v1.0'),
(257, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:42:51', 'v1.0'),
(258, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:42:51', 'v1.0'),
(259, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:42:51', 'v1.0'),
(260, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 13:42:51', 'v1.0'),
(261, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:42:51', 'v1.0'),
(262, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:42:51', 'v1.0'),
(263, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:42:51', 'v1.0'),
(264, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:42:51', 'v1.0'),
(265, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:42:51', 'v1.0'),
(266, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:42:51', 'v1.0'),
(267, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:42:51', 'v1.0'),
(268, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:42:51', 'v1.0'),
(269, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:42:51', 'v1.0'),
(270, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:42:51', 'v1.0'),
(271, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:42:56', 'v1.0'),
(272, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:42:56', 'v1.0'),
(273, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:42:56', 'v1.0'),
(274, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:42:56', 'v1.0'),
(275, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:42:56', 'v1.0'),
(276, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:42:56', 'v1.0'),
(277, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:42:56', 'v1.0'),
(278, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:42:56', 'v1.0'),
(279, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:42:56', 'v1.0'),
(280, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:42:56', 'v1.0'),
(281, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:42:56', 'v1.0'),
(282, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:42:56', 'v1.0'),
(283, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:42:56', 'v1.0'),
(284, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:42:56', 'v1.0'),
(285, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:42:56', 'v1.0'),
(286, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:42:56', 'v1.0'),
(287, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:42:56', 'v1.0'),
(288, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:42:56', 'v1.0'),
(289, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:42:56', 'v1.0'),
(290, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 13:42:56', 'v1.0'),
(291, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:42:56', 'v1.0'),
(292, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:42:56', 'v1.0'),
(293, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:42:56', 'v1.0'),
(294, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:42:56', 'v1.0'),
(295, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:42:56', 'v1.0'),
(296, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:42:56', 'v1.0'),
(297, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:42:56', 'v1.0'),
(298, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:42:56', 'v1.0'),
(299, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:42:56', 'v1.0'),
(300, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:42:56', 'v1.0'),
(301, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:42:58', 'v1.0'),
(302, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:42:58', 'v1.0'),
(303, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:42:58', 'v1.0'),
(304, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:42:58', 'v1.0'),
(305, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:42:59', 'v1.0'),
(306, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:42:59', 'v1.0'),
(307, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:42:59', 'v1.0'),
(308, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:42:59', 'v1.0'),
(309, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:42:59', 'v1.0'),
(310, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:42:59', 'v1.0'),
(311, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:42:59', 'v1.0'),
(312, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:42:59', 'v1.0'),
(313, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:42:59', 'v1.0'),
(314, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:42:59', 'v1.0'),
(315, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:42:59', 'v1.0'),
(316, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:42:59', 'v1.0'),
(317, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:42:59', 'v1.0'),
(318, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:42:59', 'v1.0'),
(319, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:42:59', 'v1.0'),
(320, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 13:42:59', 'v1.0'),
(321, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:42:59', 'v1.0'),
(322, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:42:59', 'v1.0'),
(323, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:42:59', 'v1.0'),
(324, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:42:59', 'v1.0'),
(325, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:42:59', 'v1.0'),
(326, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:42:59', 'v1.0'),
(327, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:42:59', 'v1.0'),
(328, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:42:59', 'v1.0'),
(329, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:42:59', 'v1.0'),
(330, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:42:59', 'v1.0'),
(331, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:45:59', 'v1.0'),
(332, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:45:59', 'v1.0'),
(333, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:45:59', 'v1.0'),
(334, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:45:59', 'v1.0'),
(335, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:45:59', 'v1.0'),
(336, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:45:59', 'v1.0'),
(337, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:45:59', 'v1.0'),
(338, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:45:59', 'v1.0'),
(339, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:45:59', 'v1.0'),
(340, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:45:59', 'v1.0'),
(341, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:45:59', 'v1.0'),
(342, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:45:59', 'v1.0'),
(343, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:45:59', 'v1.0'),
(344, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:45:59', 'v1.0'),
(345, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:45:59', 'v1.0'),
(346, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:45:59', 'v1.0'),
(347, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:45:59', 'v1.0'),
(348, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:45:59', 'v1.0'),
(349, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:46:00', 'v1.0'),
(350, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 13:46:00', 'v1.0'),
(351, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:46:00', 'v1.0'),
(352, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:46:00', 'v1.0'),
(353, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:46:00', 'v1.0'),
(354, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:46:00', 'v1.0'),
(355, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:46:00', 'v1.0'),
(356, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:46:00', 'v1.0'),
(357, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:46:00', 'v1.0'),
(358, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:46:00', 'v1.0'),
(359, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:46:00', 'v1.0'),
(360, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:46:00', 'v1.0'),
(361, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:46:01', 'v1.0'),
(362, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:46:01', 'v1.0'),
(363, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:46:01', 'v1.0'),
(364, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:46:01', 'v1.0'),
(365, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:46:01', 'v1.0'),
(366, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:46:01', 'v1.0'),
(367, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:46:01', 'v1.0'),
(368, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:46:01', 'v1.0'),
(369, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:46:01', 'v1.0'),
(370, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:46:01', 'v1.0'),
(371, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:46:01', 'v1.0'),
(372, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:46:01', 'v1.0'),
(373, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:46:01', 'v1.0'),
(374, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:46:01', 'v1.0'),
(375, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:46:01', 'v1.0'),
(376, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:46:01', 'v1.0'),
(377, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:46:01', 'v1.0'),
(378, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:46:01', 'v1.0'),
(379, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:46:01', 'v1.0'),
(380, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 13:46:01', 'v1.0'),
(381, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:46:01', 'v1.0'),
(382, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:46:01', 'v1.0'),
(383, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:46:01', 'v1.0'),
(384, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:46:01', 'v1.0'),
(385, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:46:01', 'v1.0'),
(386, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:46:01', 'v1.0'),
(387, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:46:01', 'v1.0'),
(388, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:46:01', 'v1.0'),
(389, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:46:01', 'v1.0'),
(390, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:46:01', 'v1.0'),
(391, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:46:06', 'v1.0'),
(392, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:46:06', 'v1.0'),
(393, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:46:06', 'v1.0'),
(394, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:46:06', 'v1.0'),
(395, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:46:06', 'v1.0'),
(396, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:46:06', 'v1.0'),
(397, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:46:06', 'v1.0'),
(398, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:46:06', 'v1.0'),
(399, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:46:06', 'v1.0'),
(400, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:46:06', 'v1.0'),
(401, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:46:06', 'v1.0'),
(402, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:46:06', 'v1.0'),
(403, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:46:06', 'v1.0'),
(404, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:46:06', 'v1.0'),
(405, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:46:06', 'v1.0'),
(406, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:46:06', 'v1.0'),
(407, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:46:06', 'v1.0'),
(408, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:46:06', 'v1.0'),
(409, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:46:06', 'v1.0'),
(410, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 13:46:06', 'v1.0'),
(411, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:46:06', 'v1.0'),
(412, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:46:06', 'v1.0'),
(413, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:46:06', 'v1.0'),
(414, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:46:06', 'v1.0'),
(415, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:46:06', 'v1.0'),
(416, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:46:06', 'v1.0'),
(417, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:46:06', 'v1.0'),
(418, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:46:06', 'v1.0'),
(419, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:46:06', 'v1.0'),
(420, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:46:06', 'v1.0'),
(421, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:49:42', 'v1.0'),
(422, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:49:42', 'v1.0'),
(423, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:49:42', 'v1.0'),
(424, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:49:42', 'v1.0'),
(425, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:49:42', 'v1.0'),
(426, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:49:42', 'v1.0'),
(427, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:49:42', 'v1.0'),
(428, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:49:42', 'v1.0'),
(429, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:49:42', 'v1.0'),
(430, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:49:42', 'v1.0'),
(431, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:49:42', 'v1.0'),
(432, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:49:42', 'v1.0'),
(433, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:49:42', 'v1.0'),
(434, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:49:42', 'v1.0'),
(435, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:49:42', 'v1.0'),
(436, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:49:42', 'v1.0'),
(437, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:49:42', 'v1.0'),
(438, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:49:42', 'v1.0'),
(439, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:49:42', 'v1.0'),
(440, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 13:49:42', 'v1.0'),
(441, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:49:42', 'v1.0'),
(442, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:49:42', 'v1.0'),
(443, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:49:42', 'v1.0'),
(444, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:49:42', 'v1.0'),
(445, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:49:42', 'v1.0'),
(446, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:49:42', 'v1.0'),
(447, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:49:42', 'v1.0'),
(448, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:49:42', 'v1.0'),
(449, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:49:42', 'v1.0'),
(450, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:49:42', 'v1.0'),
(451, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:50:39', 'v1.0'),
(452, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:50:39', 'v1.0'),
(453, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:50:39', 'v1.0'),
(454, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:50:39', 'v1.0'),
(455, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:50:39', 'v1.0'),
(456, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:50:39', 'v1.0'),
(457, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:50:39', 'v1.0'),
(458, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:50:39', 'v1.0'),
(459, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:50:39', 'v1.0'),
(460, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:50:39', 'v1.0'),
(461, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:50:39', 'v1.0'),
(462, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:50:39', 'v1.0'),
(463, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:50:39', 'v1.0'),
(464, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:50:39', 'v1.0'),
(465, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:50:39', 'v1.0'),
(466, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:50:39', 'v1.0'),
(467, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:50:39', 'v1.0'),
(468, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:50:39', 'v1.0'),
(469, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:50:39', 'v1.0'),
(470, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 13:50:39', 'v1.0'),
(471, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:50:39', 'v1.0'),
(472, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:50:39', 'v1.0'),
(473, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:50:39', 'v1.0'),
(474, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:50:39', 'v1.0'),
(475, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:50:39', 'v1.0');
INSERT INTO `prediction_logs` (`log_id`, `barangay_id`, `predicted_quantity`, `input_snapshot`, `predicted_at`, `model_version`) VALUES
(476, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:50:39', 'v1.0'),
(477, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:50:39', 'v1.0'),
(478, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:50:39', 'v1.0'),
(479, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:50:39', 'v1.0'),
(480, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:50:39', 'v1.0'),
(481, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:50:46', 'v1.0'),
(482, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:50:46', 'v1.0'),
(483, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:50:46', 'v1.0'),
(484, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:50:46', 'v1.0'),
(485, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:50:46', 'v1.0'),
(486, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:50:46', 'v1.0'),
(487, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:50:46', 'v1.0'),
(488, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:50:46', 'v1.0'),
(489, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:50:46', 'v1.0'),
(490, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:50:46', 'v1.0'),
(491, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:50:46', 'v1.0'),
(492, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:50:46', 'v1.0'),
(493, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:50:46', 'v1.0'),
(494, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:50:46', 'v1.0'),
(495, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:50:46', 'v1.0'),
(496, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:50:46', 'v1.0'),
(497, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:50:46', 'v1.0'),
(498, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:50:46', 'v1.0'),
(499, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:50:46', 'v1.0'),
(500, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 13:50:46', 'v1.0'),
(501, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:50:46', 'v1.0'),
(502, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:50:46', 'v1.0'),
(503, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:50:46', 'v1.0'),
(504, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:50:46', 'v1.0'),
(505, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:50:46', 'v1.0'),
(506, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:50:46', 'v1.0'),
(507, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:50:46', 'v1.0'),
(508, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:50:46', 'v1.0'),
(509, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:50:46', 'v1.0'),
(510, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:50:46', 'v1.0'),
(511, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:51:01', 'v1.0'),
(512, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:51:01', 'v1.0'),
(513, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:51:01', 'v1.0'),
(514, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:51:01', 'v1.0'),
(515, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:51:01', 'v1.0'),
(516, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:51:01', 'v1.0'),
(517, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:51:01', 'v1.0'),
(518, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:51:01', 'v1.0'),
(519, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:51:01', 'v1.0'),
(520, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:51:01', 'v1.0'),
(521, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:51:01', 'v1.0'),
(522, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:51:01', 'v1.0'),
(523, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:51:01', 'v1.0'),
(524, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:51:01', 'v1.0'),
(525, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:51:01', 'v1.0'),
(526, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:51:01', 'v1.0'),
(527, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:51:01', 'v1.0'),
(528, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:51:01', 'v1.0'),
(529, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:51:01', 'v1.0'),
(530, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 13:51:01', 'v1.0'),
(531, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:51:01', 'v1.0'),
(532, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:51:01', 'v1.0'),
(533, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:51:01', 'v1.0'),
(534, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:51:01', 'v1.0'),
(535, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:51:01', 'v1.0'),
(536, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:51:01', 'v1.0'),
(537, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:51:01', 'v1.0'),
(538, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:51:01', 'v1.0'),
(539, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:51:01', 'v1.0'),
(540, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:51:01', 'v1.0'),
(541, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:51:47', 'v1.0'),
(542, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:51:47', 'v1.0'),
(543, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:51:47', 'v1.0'),
(544, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:51:47', 'v1.0'),
(545, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:51:47', 'v1.0'),
(546, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:51:47', 'v1.0'),
(547, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:51:47', 'v1.0'),
(548, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:51:47', 'v1.0'),
(549, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:51:47', 'v1.0'),
(550, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:51:47', 'v1.0'),
(551, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:51:47', 'v1.0'),
(552, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:51:47', 'v1.0'),
(553, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:51:47', 'v1.0'),
(554, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:51:47', 'v1.0'),
(555, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:51:47', 'v1.0'),
(556, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:51:47', 'v1.0'),
(557, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:51:47', 'v1.0'),
(558, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:51:47', 'v1.0'),
(559, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:51:47', 'v1.0'),
(560, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 13:51:47', 'v1.0'),
(561, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:51:47', 'v1.0'),
(562, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:51:47', 'v1.0'),
(563, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:51:47', 'v1.0'),
(564, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:51:47', 'v1.0'),
(565, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:51:47', 'v1.0'),
(566, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:51:47', 'v1.0'),
(567, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:51:47', 'v1.0'),
(568, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:51:47', 'v1.0'),
(569, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:51:47', 'v1.0'),
(570, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:51:47', 'v1.0'),
(571, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:51:56', 'v1.0'),
(572, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:51:56', 'v1.0'),
(573, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:51:56', 'v1.0'),
(574, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:51:56', 'v1.0'),
(575, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:51:56', 'v1.0'),
(576, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:51:56', 'v1.0'),
(577, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:51:56', 'v1.0'),
(578, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:51:56', 'v1.0'),
(579, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:51:56', 'v1.0'),
(580, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:51:56', 'v1.0'),
(581, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:51:56', 'v1.0'),
(582, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:51:56', 'v1.0'),
(583, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:51:56', 'v1.0'),
(584, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:51:56', 'v1.0'),
(585, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:51:56', 'v1.0'),
(586, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:51:56', 'v1.0'),
(587, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:51:56', 'v1.0'),
(588, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:51:56', 'v1.0'),
(589, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:51:56', 'v1.0'),
(590, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 13:51:56', 'v1.0'),
(591, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:51:56', 'v1.0'),
(592, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:51:56', 'v1.0'),
(593, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:51:56', 'v1.0'),
(594, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:51:56', 'v1.0'),
(595, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:51:56', 'v1.0'),
(596, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:51:56', 'v1.0'),
(597, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:51:56', 'v1.0'),
(598, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:51:56', 'v1.0'),
(599, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:51:56', 'v1.0'),
(600, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:51:56', 'v1.0'),
(601, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:58:49', 'v1.0'),
(602, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:58:49', 'v1.0'),
(603, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:58:49', 'v1.0'),
(604, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:58:49', 'v1.0'),
(605, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:58:49', 'v1.0'),
(606, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:58:49', 'v1.0'),
(607, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:58:49', 'v1.0'),
(608, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:58:49', 'v1.0'),
(609, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:58:49', 'v1.0'),
(610, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:58:49', 'v1.0'),
(611, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:58:49', 'v1.0'),
(612, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:58:49', 'v1.0'),
(613, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:58:49', 'v1.0'),
(614, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:58:49', 'v1.0'),
(615, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:58:49', 'v1.0'),
(616, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:58:49', 'v1.0'),
(617, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:58:49', 'v1.0'),
(618, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:58:49', 'v1.0'),
(619, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:58:49', 'v1.0'),
(620, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 13:58:49', 'v1.0'),
(621, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:58:49', 'v1.0'),
(622, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:58:49', 'v1.0'),
(623, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:58:49', 'v1.0'),
(624, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:58:49', 'v1.0'),
(625, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:58:49', 'v1.0'),
(626, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:58:49', 'v1.0'),
(627, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:58:49', 'v1.0'),
(628, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:58:49', 'v1.0'),
(629, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:58:49', 'v1.0'),
(630, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:58:49', 'v1.0'),
(631, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(632, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(633, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(634, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(635, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(636, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(637, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(638, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(639, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(640, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(641, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(642, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(643, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(644, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(645, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(646, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(647, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(648, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(649, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(650, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(651, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(652, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(653, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(654, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(655, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(656, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(657, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(658, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(659, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(660, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(661, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(662, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(663, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(664, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(665, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(666, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(667, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(668, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(669, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(670, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(671, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(672, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(673, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(674, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(675, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(676, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(677, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(678, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(679, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(680, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(681, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(682, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(683, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(684, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(685, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(686, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(687, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(688, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(689, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(690, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:58:50', 'v1.0'),
(691, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:58:51', 'v1.0'),
(692, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:58:51', 'v1.0'),
(693, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:58:51', 'v1.0'),
(694, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:58:51', 'v1.0'),
(695, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:58:51', 'v1.0'),
(696, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:58:51', 'v1.0'),
(697, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:58:51', 'v1.0'),
(698, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:58:51', 'v1.0'),
(699, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:58:51', 'v1.0'),
(700, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:58:51', 'v1.0'),
(701, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:58:51', 'v1.0'),
(702, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:58:51', 'v1.0'),
(703, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:58:51', 'v1.0'),
(704, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 13:58:51', 'v1.0'),
(705, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:58:51', 'v1.0'),
(706, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:58:51', 'v1.0'),
(707, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:58:51', 'v1.0'),
(708, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:58:51', 'v1.0'),
(709, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:58:51', 'v1.0'),
(710, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 13:58:51', 'v1.0'),
(711, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:58:51', 'v1.0'),
(712, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:58:51', 'v1.0');
INSERT INTO `prediction_logs` (`log_id`, `barangay_id`, `predicted_quantity`, `input_snapshot`, `predicted_at`, `model_version`) VALUES
(713, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 13:58:51', 'v1.0'),
(714, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:58:51', 'v1.0'),
(715, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:58:51', 'v1.0'),
(716, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:58:51', 'v1.0'),
(717, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 13:58:51', 'v1.0'),
(718, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 13:58:51', 'v1.0'),
(719, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 13:58:51', 'v1.0'),
(720, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 13:58:51', 'v1.0'),
(721, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:02:47', 'v1.0'),
(722, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:02:47', 'v1.0'),
(723, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:02:47', 'v1.0'),
(724, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:02:47', 'v1.0'),
(725, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:02:47', 'v1.0'),
(726, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:02:47', 'v1.0'),
(727, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:02:47', 'v1.0'),
(728, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:02:47', 'v1.0'),
(729, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:02:47', 'v1.0'),
(730, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:02:47', 'v1.0'),
(731, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:02:47', 'v1.0'),
(732, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:02:47', 'v1.0'),
(733, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:02:47', 'v1.0'),
(734, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:02:47', 'v1.0'),
(735, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:02:47', 'v1.0'),
(736, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:02:47', 'v1.0'),
(737, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:02:47', 'v1.0'),
(738, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:02:47', 'v1.0'),
(739, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:02:47', 'v1.0'),
(740, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 14:02:47', 'v1.0'),
(741, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:02:47', 'v1.0'),
(742, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:02:47', 'v1.0'),
(743, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:02:47', 'v1.0'),
(744, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:02:47', 'v1.0'),
(745, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:02:47', 'v1.0'),
(746, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:02:47', 'v1.0'),
(747, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:02:47', 'v1.0'),
(748, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:02:47', 'v1.0'),
(749, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:02:47', 'v1.0'),
(750, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:02:47', 'v1.0'),
(751, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:27:41', 'v1.0'),
(752, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:27:41', 'v1.0'),
(753, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:27:41', 'v1.0'),
(754, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:27:41', 'v1.0'),
(755, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:27:41', 'v1.0'),
(756, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:27:41', 'v1.0'),
(757, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:27:41', 'v1.0'),
(758, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:27:41', 'v1.0'),
(759, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:27:41', 'v1.0'),
(760, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:27:41', 'v1.0'),
(761, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:27:41', 'v1.0'),
(762, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:27:41', 'v1.0'),
(763, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:27:41', 'v1.0'),
(764, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:27:41', 'v1.0'),
(765, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:27:41', 'v1.0'),
(766, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:27:41', 'v1.0'),
(767, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:27:41', 'v1.0'),
(768, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:27:41', 'v1.0'),
(769, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:27:41', 'v1.0'),
(770, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 14:27:41', 'v1.0'),
(771, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:27:41', 'v1.0'),
(772, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:27:41', 'v1.0'),
(773, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:27:41', 'v1.0'),
(774, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:27:41', 'v1.0'),
(775, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:27:41', 'v1.0'),
(776, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:27:41', 'v1.0'),
(777, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:27:41', 'v1.0'),
(778, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:27:41', 'v1.0'),
(779, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:27:41', 'v1.0'),
(780, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:27:41', 'v1.0'),
(781, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:27:44', 'v1.0'),
(782, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:27:44', 'v1.0'),
(783, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:27:44', 'v1.0'),
(784, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:27:44', 'v1.0'),
(785, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:27:44', 'v1.0'),
(786, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:27:44', 'v1.0'),
(787, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:27:44', 'v1.0'),
(788, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:27:44', 'v1.0'),
(789, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:27:44', 'v1.0'),
(790, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:27:44', 'v1.0'),
(791, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:27:44', 'v1.0'),
(792, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:27:44', 'v1.0'),
(793, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:27:44', 'v1.0'),
(794, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:27:44', 'v1.0'),
(795, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:27:44', 'v1.0'),
(796, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:27:44', 'v1.0'),
(797, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:27:44', 'v1.0'),
(798, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:27:44', 'v1.0'),
(799, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:27:44', 'v1.0'),
(800, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 14:27:44', 'v1.0'),
(801, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:27:44', 'v1.0'),
(802, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:27:44', 'v1.0'),
(803, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:27:44', 'v1.0'),
(804, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:27:44', 'v1.0'),
(805, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:27:44', 'v1.0'),
(806, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:27:44', 'v1.0'),
(807, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:27:44', 'v1.0'),
(808, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:27:44', 'v1.0'),
(809, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:27:44', 'v1.0'),
(810, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:27:44', 'v1.0'),
(811, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:27:45', 'v1.0'),
(812, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:27:45', 'v1.0'),
(813, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:27:45', 'v1.0'),
(814, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:27:45', 'v1.0'),
(815, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:27:45', 'v1.0'),
(816, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:27:45', 'v1.0'),
(817, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:27:45', 'v1.0'),
(818, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:27:45', 'v1.0'),
(819, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:27:45', 'v1.0'),
(820, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:27:45', 'v1.0'),
(821, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:27:45', 'v1.0'),
(822, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:27:45', 'v1.0'),
(823, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:27:45', 'v1.0'),
(824, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:27:45', 'v1.0'),
(825, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:27:45', 'v1.0'),
(826, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:27:45', 'v1.0'),
(827, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:27:45', 'v1.0'),
(828, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:27:45', 'v1.0'),
(829, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:27:45', 'v1.0'),
(830, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 14:27:45', 'v1.0'),
(831, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:27:45', 'v1.0'),
(832, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:27:45', 'v1.0'),
(833, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:27:45', 'v1.0'),
(834, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:27:45', 'v1.0'),
(835, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:27:45', 'v1.0'),
(836, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:27:45', 'v1.0'),
(837, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:27:45', 'v1.0'),
(838, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:27:45', 'v1.0'),
(839, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:27:45', 'v1.0'),
(840, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:27:45', 'v1.0'),
(841, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:28:31', 'v1.0'),
(842, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:28:31', 'v1.0'),
(843, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:28:31', 'v1.0'),
(844, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:28:31', 'v1.0'),
(845, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:28:31', 'v1.0'),
(846, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:28:31', 'v1.0'),
(847, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:28:31', 'v1.0'),
(848, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:28:31', 'v1.0'),
(849, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:28:31', 'v1.0'),
(850, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:28:31', 'v1.0'),
(851, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:28:31', 'v1.0'),
(852, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:28:31', 'v1.0'),
(853, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:28:31', 'v1.0'),
(854, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:28:31', 'v1.0'),
(855, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:28:31', 'v1.0'),
(856, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:28:31', 'v1.0'),
(857, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:28:31', 'v1.0'),
(858, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:28:31', 'v1.0'),
(859, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:28:31', 'v1.0'),
(860, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 14:28:31', 'v1.0'),
(861, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:28:31', 'v1.0'),
(862, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:28:31', 'v1.0'),
(863, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:28:31', 'v1.0'),
(864, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:28:31', 'v1.0'),
(865, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:28:31', 'v1.0'),
(866, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:28:31', 'v1.0'),
(867, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:28:31', 'v1.0'),
(868, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:28:31', 'v1.0'),
(869, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:28:31', 'v1.0'),
(870, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:28:31', 'v1.0'),
(871, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:30:31', 'v1.0'),
(872, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:30:31', 'v1.0'),
(873, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:30:31', 'v1.0'),
(874, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:30:31', 'v1.0'),
(875, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:30:31', 'v1.0'),
(876, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:30:31', 'v1.0'),
(877, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:30:31', 'v1.0'),
(878, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:30:31', 'v1.0'),
(879, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:30:31', 'v1.0'),
(880, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:30:31', 'v1.0'),
(881, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:30:31', 'v1.0'),
(882, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:30:31', 'v1.0'),
(883, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:30:31', 'v1.0'),
(884, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:30:31', 'v1.0'),
(885, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:30:31', 'v1.0'),
(886, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:30:31', 'v1.0'),
(887, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:30:31', 'v1.0'),
(888, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:30:31', 'v1.0'),
(889, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:30:31', 'v1.0'),
(890, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 14:30:31', 'v1.0'),
(891, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:30:31', 'v1.0'),
(892, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:30:31', 'v1.0'),
(893, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:30:31', 'v1.0'),
(894, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:30:31', 'v1.0'),
(895, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:30:31', 'v1.0'),
(896, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:30:31', 'v1.0'),
(897, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:30:31', 'v1.0'),
(898, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:30:31', 'v1.0'),
(899, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:30:31', 'v1.0'),
(900, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:30:31', 'v1.0'),
(901, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:33:58', 'v1.0'),
(902, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:33:58', 'v1.0'),
(903, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:33:58', 'v1.0'),
(904, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:33:58', 'v1.0'),
(905, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:33:58', 'v1.0'),
(906, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:33:58', 'v1.0'),
(907, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:33:58', 'v1.0'),
(908, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:33:58', 'v1.0'),
(909, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:33:58', 'v1.0'),
(910, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:33:58', 'v1.0'),
(911, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:33:58', 'v1.0'),
(912, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:33:58', 'v1.0'),
(913, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:33:58', 'v1.0'),
(914, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:33:58', 'v1.0'),
(915, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:33:58', 'v1.0'),
(916, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:33:58', 'v1.0'),
(917, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:33:58', 'v1.0'),
(918, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:33:58', 'v1.0'),
(919, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:33:58', 'v1.0'),
(920, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 14:33:58', 'v1.0'),
(921, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:33:58', 'v1.0'),
(922, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:33:58', 'v1.0'),
(923, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:33:58', 'v1.0'),
(924, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:33:58', 'v1.0'),
(925, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:33:58', 'v1.0'),
(926, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:33:58', 'v1.0'),
(927, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:33:58', 'v1.0'),
(928, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:33:58', 'v1.0'),
(929, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:33:58', 'v1.0'),
(930, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:33:58', 'v1.0'),
(931, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:35:28', 'v1.0'),
(932, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:35:28', 'v1.0'),
(933, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:35:28', 'v1.0'),
(934, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:35:28', 'v1.0'),
(935, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:35:28', 'v1.0'),
(936, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:35:28', 'v1.0'),
(937, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:35:28', 'v1.0'),
(938, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:35:28', 'v1.0'),
(939, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:35:28', 'v1.0'),
(940, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:35:28', 'v1.0'),
(941, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:35:28', 'v1.0'),
(942, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:35:28', 'v1.0'),
(943, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:35:28', 'v1.0'),
(944, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:35:28', 'v1.0'),
(945, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:35:28', 'v1.0'),
(946, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:35:28', 'v1.0'),
(947, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:35:28', 'v1.0'),
(948, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:35:28', 'v1.0'),
(949, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:35:28', 'v1.0');
INSERT INTO `prediction_logs` (`log_id`, `barangay_id`, `predicted_quantity`, `input_snapshot`, `predicted_at`, `model_version`) VALUES
(950, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 14:35:28', 'v1.0'),
(951, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:35:28', 'v1.0'),
(952, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:35:28', 'v1.0'),
(953, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:35:28', 'v1.0'),
(954, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:35:28', 'v1.0'),
(955, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:35:28', 'v1.0'),
(956, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:35:28', 'v1.0'),
(957, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:35:28', 'v1.0'),
(958, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:35:28', 'v1.0'),
(959, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:35:28', 'v1.0'),
(960, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:35:28', 'v1.0'),
(961, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:35:30', 'v1.0'),
(962, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:35:30', 'v1.0'),
(963, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:35:30', 'v1.0'),
(964, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:35:30', 'v1.0'),
(965, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:35:30', 'v1.0'),
(966, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:35:30', 'v1.0'),
(967, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:35:30', 'v1.0'),
(968, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:35:30', 'v1.0'),
(969, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:35:30', 'v1.0'),
(970, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:35:30', 'v1.0'),
(971, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:35:30', 'v1.0'),
(972, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:35:30', 'v1.0'),
(973, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:35:30', 'v1.0'),
(974, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:35:30', 'v1.0'),
(975, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:35:30', 'v1.0'),
(976, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:35:30', 'v1.0'),
(977, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:35:30', 'v1.0'),
(978, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:35:30', 'v1.0'),
(979, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:35:30', 'v1.0'),
(980, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 14:35:30', 'v1.0'),
(981, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:35:30', 'v1.0'),
(982, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:35:30', 'v1.0'),
(983, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:35:30', 'v1.0'),
(984, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:35:30', 'v1.0'),
(985, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:35:30', 'v1.0'),
(986, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:35:30', 'v1.0'),
(987, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:35:30', 'v1.0'),
(988, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:35:30', 'v1.0'),
(989, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:35:30', 'v1.0'),
(990, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:35:30', 'v1.0'),
(991, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:35:44', 'v1.0'),
(992, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:35:44', 'v1.0'),
(993, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:35:44', 'v1.0'),
(994, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:35:44', 'v1.0'),
(995, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:35:44', 'v1.0'),
(996, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:35:44', 'v1.0'),
(997, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:35:44', 'v1.0'),
(998, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:35:44', 'v1.0'),
(999, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:35:44', 'v1.0'),
(1000, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:35:44', 'v1.0'),
(1001, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:35:44', 'v1.0'),
(1002, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:35:44', 'v1.0'),
(1003, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:35:44', 'v1.0'),
(1004, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:35:44', 'v1.0'),
(1005, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:35:44', 'v1.0'),
(1006, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:35:44', 'v1.0'),
(1007, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:35:44', 'v1.0'),
(1008, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:35:44', 'v1.0'),
(1009, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:35:44', 'v1.0'),
(1010, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 14:35:44', 'v1.0'),
(1011, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:35:44', 'v1.0'),
(1012, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:35:44', 'v1.0'),
(1013, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:35:44', 'v1.0'),
(1014, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:35:44', 'v1.0'),
(1015, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:35:44', 'v1.0'),
(1016, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:35:44', 'v1.0'),
(1017, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:35:44', 'v1.0'),
(1018, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:35:44', 'v1.0'),
(1019, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:35:44', 'v1.0'),
(1020, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:35:44', 'v1.0'),
(1021, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1022, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1023, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1024, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1025, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1026, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1027, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1028, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1029, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1030, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1031, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1032, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1033, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1034, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1035, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1036, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1037, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1038, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1039, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1040, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1041, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1042, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1043, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1044, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1045, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1046, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1047, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1048, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1049, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1050, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1051, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1052, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1053, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1054, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1055, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1056, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1057, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1058, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1059, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1060, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1061, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1062, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1063, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1064, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1065, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1066, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1067, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1068, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1069, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1070, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1071, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1072, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1073, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1074, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1075, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1076, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1077, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1078, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1079, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1080, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:38:37', 'v1.0'),
(1081, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:38:38', 'v1.0'),
(1082, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:38:38', 'v1.0'),
(1083, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:38:38', 'v1.0'),
(1084, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:38:38', 'v1.0'),
(1085, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:38:38', 'v1.0'),
(1086, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:38:38', 'v1.0'),
(1087, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:38:38', 'v1.0'),
(1088, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:38:38', 'v1.0'),
(1089, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:38:38', 'v1.0'),
(1090, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:38:38', 'v1.0'),
(1091, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:38:38', 'v1.0'),
(1092, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:38:38', 'v1.0'),
(1093, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:38:38', 'v1.0'),
(1094, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:38:38', 'v1.0'),
(1095, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:38:38', 'v1.0'),
(1096, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:38:38', 'v1.0'),
(1097, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:38:38', 'v1.0'),
(1098, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:38:38', 'v1.0'),
(1099, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:38:38', 'v1.0'),
(1100, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 14:38:38', 'v1.0'),
(1101, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:38:38', 'v1.0'),
(1102, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:38:38', 'v1.0'),
(1103, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:38:38', 'v1.0'),
(1104, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:38:38', 'v1.0'),
(1105, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:38:38', 'v1.0'),
(1106, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:38:38', 'v1.0'),
(1107, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:38:38', 'v1.0'),
(1108, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:38:38', 'v1.0'),
(1109, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:38:38', 'v1.0'),
(1110, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:38:38', 'v1.0'),
(1111, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:39:54', 'v1.0'),
(1112, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:39:54', 'v1.0'),
(1113, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:39:54', 'v1.0'),
(1114, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:39:54', 'v1.0'),
(1115, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:39:54', 'v1.0'),
(1116, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:39:54', 'v1.0'),
(1117, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:39:54', 'v1.0'),
(1118, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:39:54', 'v1.0'),
(1119, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:39:54', 'v1.0'),
(1120, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:39:54', 'v1.0'),
(1121, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:39:54', 'v1.0'),
(1122, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:39:54', 'v1.0'),
(1123, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:39:54', 'v1.0'),
(1124, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:39:54', 'v1.0'),
(1125, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:39:54', 'v1.0'),
(1126, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:39:54', 'v1.0'),
(1127, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:39:54', 'v1.0'),
(1128, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:39:54', 'v1.0'),
(1129, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:39:54', 'v1.0'),
(1130, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 14:39:54', 'v1.0'),
(1131, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:39:54', 'v1.0'),
(1132, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:39:54', 'v1.0'),
(1133, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:39:54', 'v1.0'),
(1134, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:39:54', 'v1.0'),
(1135, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:39:54', 'v1.0'),
(1136, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:39:54', 'v1.0'),
(1137, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:39:54', 'v1.0'),
(1138, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:39:54', 'v1.0'),
(1139, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:39:54', 'v1.0'),
(1140, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:39:54', 'v1.0'),
(1141, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:41:33', 'v1.0'),
(1142, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:41:33', 'v1.0'),
(1143, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:41:33', 'v1.0'),
(1144, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:41:33', 'v1.0'),
(1145, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:41:33', 'v1.0'),
(1146, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:41:33', 'v1.0'),
(1147, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:41:33', 'v1.0'),
(1148, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:41:33', 'v1.0'),
(1149, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:41:33', 'v1.0'),
(1150, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:41:33', 'v1.0'),
(1151, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:41:33', 'v1.0'),
(1152, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:41:33', 'v1.0'),
(1153, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:41:33', 'v1.0'),
(1154, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:41:33', 'v1.0'),
(1155, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:41:33', 'v1.0'),
(1156, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:41:33', 'v1.0'),
(1157, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:41:33', 'v1.0'),
(1158, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:41:33', 'v1.0'),
(1159, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:41:33', 'v1.0'),
(1160, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 14:41:33', 'v1.0'),
(1161, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:41:33', 'v1.0'),
(1162, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:41:33', 'v1.0'),
(1163, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:41:33', 'v1.0'),
(1164, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:41:33', 'v1.0'),
(1165, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:41:33', 'v1.0'),
(1166, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:41:33', 'v1.0'),
(1167, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:41:33', 'v1.0'),
(1168, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:41:33', 'v1.0'),
(1169, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:41:33', 'v1.0'),
(1170, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:41:33', 'v1.0'),
(1171, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:42:24', 'v1.0'),
(1172, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:42:24', 'v1.0'),
(1173, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:42:24', 'v1.0'),
(1174, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:42:24', 'v1.0'),
(1175, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:42:24', 'v1.0'),
(1176, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:42:24', 'v1.0'),
(1177, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:42:24', 'v1.0'),
(1178, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:42:24', 'v1.0'),
(1179, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:42:24', 'v1.0'),
(1180, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:42:24', 'v1.0'),
(1181, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:42:24', 'v1.0'),
(1182, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:42:24', 'v1.0'),
(1183, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:42:24', 'v1.0'),
(1184, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:42:24', 'v1.0'),
(1185, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:42:24', 'v1.0');
INSERT INTO `prediction_logs` (`log_id`, `barangay_id`, `predicted_quantity`, `input_snapshot`, `predicted_at`, `model_version`) VALUES
(1186, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:42:24', 'v1.0'),
(1187, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:42:24', 'v1.0'),
(1188, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:42:24', 'v1.0'),
(1189, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:42:24', 'v1.0'),
(1190, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 14:42:24', 'v1.0'),
(1191, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:42:24', 'v1.0'),
(1192, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:42:24', 'v1.0'),
(1193, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:42:24', 'v1.0'),
(1194, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:42:24', 'v1.0'),
(1195, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:42:24', 'v1.0'),
(1196, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:42:24', 'v1.0'),
(1197, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:42:24', 'v1.0'),
(1198, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:42:24', 'v1.0'),
(1199, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:42:24', 'v1.0'),
(1200, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:42:24', 'v1.0'),
(1201, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:42:30', 'v1.0'),
(1202, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:42:30', 'v1.0'),
(1203, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:42:30', 'v1.0'),
(1204, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:42:30', 'v1.0'),
(1205, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:42:30', 'v1.0'),
(1206, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:42:30', 'v1.0'),
(1207, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:42:30', 'v1.0'),
(1208, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:42:30', 'v1.0'),
(1209, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:42:30', 'v1.0'),
(1210, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:42:30', 'v1.0'),
(1211, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:42:30', 'v1.0'),
(1212, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:42:30', 'v1.0'),
(1213, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:42:30', 'v1.0'),
(1214, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:42:30', 'v1.0'),
(1215, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:42:30', 'v1.0'),
(1216, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:42:30', 'v1.0'),
(1217, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:42:30', 'v1.0'),
(1218, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:42:30', 'v1.0'),
(1219, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:42:30', 'v1.0'),
(1220, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 14:42:30', 'v1.0'),
(1221, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:42:30', 'v1.0'),
(1222, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:42:30', 'v1.0'),
(1223, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:42:30', 'v1.0'),
(1224, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:42:30', 'v1.0'),
(1225, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:42:30', 'v1.0'),
(1226, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:42:30', 'v1.0'),
(1227, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:42:30', 'v1.0'),
(1228, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:42:30', 'v1.0'),
(1229, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:42:30', 'v1.0'),
(1230, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:42:30', 'v1.0'),
(1231, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:44:25', 'v1.0'),
(1232, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:44:25', 'v1.0'),
(1233, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:44:25', 'v1.0'),
(1234, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:44:25', 'v1.0'),
(1235, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:44:25', 'v1.0'),
(1236, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:44:25', 'v1.0'),
(1237, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:44:25', 'v1.0'),
(1238, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:44:25', 'v1.0'),
(1239, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:44:25', 'v1.0'),
(1240, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:44:25', 'v1.0'),
(1241, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:44:25', 'v1.0'),
(1242, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:44:25', 'v1.0'),
(1243, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:44:25', 'v1.0'),
(1244, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:44:25', 'v1.0'),
(1245, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:44:25', 'v1.0'),
(1246, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:44:25', 'v1.0'),
(1247, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:44:25', 'v1.0'),
(1248, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:44:25', 'v1.0'),
(1249, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:44:25', 'v1.0'),
(1250, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 14:44:25', 'v1.0'),
(1251, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:44:25', 'v1.0'),
(1252, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:44:25', 'v1.0'),
(1253, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:44:25', 'v1.0'),
(1254, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:44:25', 'v1.0'),
(1255, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:44:25', 'v1.0'),
(1256, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:44:25', 'v1.0'),
(1257, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:44:25', 'v1.0'),
(1258, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:44:25', 'v1.0'),
(1259, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:44:25', 'v1.0'),
(1260, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:44:25', 'v1.0'),
(1261, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:44:45', 'v1.0'),
(1262, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:44:45', 'v1.0'),
(1263, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:44:45', 'v1.0'),
(1264, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:44:45', 'v1.0'),
(1265, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:44:45', 'v1.0'),
(1266, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:44:45', 'v1.0'),
(1267, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:44:45', 'v1.0'),
(1268, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:44:45', 'v1.0'),
(1269, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:44:45', 'v1.0'),
(1270, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:44:45', 'v1.0'),
(1271, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:44:45', 'v1.0'),
(1272, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:44:45', 'v1.0'),
(1273, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:44:45', 'v1.0'),
(1274, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:44:45', 'v1.0'),
(1275, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:44:45', 'v1.0'),
(1276, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:44:45', 'v1.0'),
(1277, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:44:45', 'v1.0'),
(1278, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:44:45', 'v1.0'),
(1279, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:44:45', 'v1.0'),
(1280, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 14:44:45', 'v1.0'),
(1281, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:44:45', 'v1.0'),
(1282, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:44:45', 'v1.0'),
(1283, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:44:45', 'v1.0'),
(1284, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:44:45', 'v1.0'),
(1285, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:44:45', 'v1.0'),
(1286, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:44:45', 'v1.0'),
(1287, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:44:45', 'v1.0'),
(1288, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:44:45', 'v1.0'),
(1289, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:44:45', 'v1.0'),
(1290, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:44:45', 'v1.0'),
(1291, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:44:46', 'v1.0'),
(1292, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:44:46', 'v1.0'),
(1293, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:44:46', 'v1.0'),
(1294, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:44:46', 'v1.0'),
(1295, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:44:46', 'v1.0'),
(1296, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:44:46', 'v1.0'),
(1297, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:44:46', 'v1.0'),
(1298, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:44:46', 'v1.0'),
(1299, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:44:46', 'v1.0'),
(1300, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:44:46', 'v1.0'),
(1301, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:44:46', 'v1.0'),
(1302, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:44:46', 'v1.0'),
(1303, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:44:46', 'v1.0'),
(1304, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:44:46', 'v1.0'),
(1305, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:44:46', 'v1.0'),
(1306, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:44:46', 'v1.0'),
(1307, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:44:46', 'v1.0'),
(1308, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:44:46', 'v1.0'),
(1309, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:44:46', 'v1.0'),
(1310, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 14:44:46', 'v1.0'),
(1311, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:44:46', 'v1.0'),
(1312, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:44:46', 'v1.0'),
(1313, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:44:46', 'v1.0'),
(1314, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:44:46', 'v1.0'),
(1315, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:44:46', 'v1.0'),
(1316, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:44:46', 'v1.0'),
(1317, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:44:46', 'v1.0'),
(1318, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:44:46', 'v1.0'),
(1319, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:44:46', 'v1.0'),
(1320, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:44:46', 'v1.0'),
(1321, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:46:38', 'v1.0'),
(1322, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:46:38', 'v1.0'),
(1323, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:46:38', 'v1.0'),
(1324, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:46:38', 'v1.0'),
(1325, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:46:38', 'v1.0'),
(1326, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:46:38', 'v1.0'),
(1327, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:46:38', 'v1.0'),
(1328, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:46:38', 'v1.0'),
(1329, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:46:38', 'v1.0'),
(1330, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:46:38', 'v1.0'),
(1331, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:46:38', 'v1.0'),
(1332, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:46:38', 'v1.0'),
(1333, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:46:38', 'v1.0'),
(1334, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:46:38', 'v1.0'),
(1335, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:46:38', 'v1.0'),
(1336, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:46:38', 'v1.0'),
(1337, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:46:38', 'v1.0'),
(1338, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:46:38', 'v1.0'),
(1339, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:46:38', 'v1.0'),
(1340, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 14:46:38', 'v1.0'),
(1341, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:46:38', 'v1.0'),
(1342, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:46:38', 'v1.0'),
(1343, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:46:38', 'v1.0'),
(1344, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:46:38', 'v1.0'),
(1345, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:46:38', 'v1.0'),
(1346, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:46:38', 'v1.0'),
(1347, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:46:38', 'v1.0'),
(1348, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:46:38', 'v1.0'),
(1349, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:46:38', 'v1.0'),
(1350, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:46:38', 'v1.0'),
(1351, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:47:10', 'v1.0'),
(1352, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:47:10', 'v1.0'),
(1353, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:47:10', 'v1.0'),
(1354, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:47:10', 'v1.0'),
(1355, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:47:10', 'v1.0'),
(1356, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:47:10', 'v1.0'),
(1357, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:47:10', 'v1.0'),
(1358, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:47:10', 'v1.0'),
(1359, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:47:10', 'v1.0'),
(1360, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:47:10', 'v1.0'),
(1361, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:47:10', 'v1.0'),
(1362, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:47:10', 'v1.0'),
(1363, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:47:10', 'v1.0'),
(1364, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:47:10', 'v1.0'),
(1365, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:47:10', 'v1.0'),
(1366, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:47:10', 'v1.0'),
(1367, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:47:10', 'v1.0'),
(1368, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:47:10', 'v1.0'),
(1369, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:47:10', 'v1.0'),
(1370, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 14:47:10', 'v1.0'),
(1371, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:47:10', 'v1.0'),
(1372, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:47:10', 'v1.0'),
(1373, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:47:10', 'v1.0'),
(1374, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:47:10', 'v1.0'),
(1375, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:47:10', 'v1.0'),
(1376, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:47:10', 'v1.0'),
(1377, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:47:10', 'v1.0'),
(1378, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:47:10', 'v1.0'),
(1379, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:47:10', 'v1.0'),
(1380, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:47:10', 'v1.0'),
(1381, 21, 0, '{\"population\": 3800, \"num_households\": 760, \"poverty_incidence\": 26.0, \"disaster_risk_index\": 5.1, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:49:26', 'v1.0'),
(1382, 22, 0, '{\"population\": 2300, \"num_households\": 460, \"poverty_incidence\": 34.0, \"disaster_risk_index\": 6.6, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:49:26', 'v1.0'),
(1383, 23, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 39.0, \"disaster_risk_index\": 7.3, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:49:26', 'v1.0'),
(1384, 24, 0, '{\"population\": 4200, \"num_households\": 840, \"poverty_incidence\": 24.5, \"disaster_risk_index\": 4.9, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:49:26', 'v1.0'),
(1385, 25, 0, '{\"population\": 2900, \"num_households\": 580, \"poverty_incidence\": 30.5, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:49:26', 'v1.0'),
(1386, 26, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 43.0, \"disaster_risk_index\": 7.9, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:49:26', 'v1.0'),
(1387, 27, 0, '{\"population\": 2000, \"num_households\": 400, \"poverty_incidence\": 36.5, \"disaster_risk_index\": 6.7, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:49:26', 'v1.0'),
(1388, 28, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 41.0, \"disaster_risk_index\": 7.6, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:49:26', 'v1.0'),
(1389, 29, 0, '{\"population\": 2600, \"num_households\": 520, \"poverty_incidence\": 28.5, \"disaster_risk_index\": 5.4, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:49:26', 'v1.0'),
(1390, 30, 0, '{\"population\": 1200, \"num_households\": 240, \"poverty_incidence\": 48.0, \"disaster_risk_index\": 8.5, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:49:26', 'v1.0'),
(1391, 11, 0, '{\"population\": 1600, \"num_households\": 320, \"poverty_incidence\": 38.0, \"disaster_risk_index\": 6.8, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:49:26', 'v1.0'),
(1392, 12, 0, '{\"population\": 2200, \"num_households\": 440, \"poverty_incidence\": 31.5, \"disaster_risk_index\": 5.7, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:49:26', 'v1.0'),
(1393, 13, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 36.0, \"disaster_risk_index\": 7.0, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:49:26', 'v1.0'),
(1394, 14, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 27.0, \"disaster_risk_index\": 5.2, \"past_calamity_freq\": 3, \"historical_allocation\": 0}', '2026-07-02 14:49:26', 'v1.0'),
(1395, 15, 0, '{\"population\": 1400, \"num_households\": 280, \"poverty_incidence\": 44.5, \"disaster_risk_index\": 8.1, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:49:26', 'v1.0'),
(1396, 16, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.5, \"disaster_risk_index\": 6.4, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:49:26', 'v1.0'),
(1397, 17, 0, '{\"population\": 1700, \"num_households\": 340, \"poverty_incidence\": 37.0, \"disaster_risk_index\": 6.9, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:49:26', 'v1.0'),
(1398, 18, 0, '{\"population\": 1300, \"num_households\": 260, \"poverty_incidence\": 46.0, \"disaster_risk_index\": 8.3, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:49:26', 'v1.0'),
(1399, 19, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 29.0, \"disaster_risk_index\": 5.6, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:49:26', 'v1.0'),
(1400, 20, 0, '{\"population\": 1100, \"num_households\": 220, \"poverty_incidence\": 50.0, \"disaster_risk_index\": 8.8, \"past_calamity_freq\": 9, \"historical_allocation\": 0}', '2026-07-02 14:49:26', 'v1.0'),
(1401, 1, 0, '{\"population\": 3200, \"num_households\": 640, \"poverty_incidence\": 32.5, \"disaster_risk_index\": 6.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:49:26', 'v1.0'),
(1402, 2, 0, '{\"population\": 4100, \"num_households\": 820, \"poverty_incidence\": 28.0, \"disaster_risk_index\": 5.8, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:49:26', 'v1.0'),
(1403, 3, 0, '{\"population\": 2800, \"num_households\": 560, \"poverty_incidence\": 40.0, \"disaster_risk_index\": 7.2, \"past_calamity_freq\": 7, \"historical_allocation\": 0}', '2026-07-02 14:49:26', 'v1.0'),
(1404, 4, 0, '{\"population\": 1900, \"num_households\": 380, \"poverty_incidence\": 35.0, \"disaster_risk_index\": 6.0, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:49:26', 'v1.0'),
(1405, 5, 0, '{\"population\": 2500, \"num_households\": 500, \"poverty_incidence\": 38.5, \"disaster_risk_index\": 7.8, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:49:26', 'v1.0'),
(1406, 6, 0, '{\"population\": 3600, \"num_households\": 720, \"poverty_incidence\": 30.0, \"disaster_risk_index\": 5.5, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:49:26', 'v1.0'),
(1407, 7, 0, '{\"population\": 1500, \"num_households\": 300, \"poverty_incidence\": 45.0, \"disaster_risk_index\": 8.0, \"past_calamity_freq\": 8, \"historical_allocation\": 0}', '2026-07-02 14:49:26', 'v1.0'),
(1408, 8, 0, '{\"population\": 2100, \"num_households\": 420, \"poverty_incidence\": 33.0, \"disaster_risk_index\": 6.3, \"past_calamity_freq\": 5, \"historical_allocation\": 0}', '2026-07-02 14:49:26', 'v1.0'),
(1409, 9, 0, '{\"population\": 2700, \"num_households\": 540, \"poverty_incidence\": 29.5, \"disaster_risk_index\": 5.9, \"past_calamity_freq\": 4, \"historical_allocation\": 0}', '2026-07-02 14:49:26', 'v1.0'),
(1410, 10, 0, '{\"population\": 1800, \"num_households\": 360, \"poverty_incidence\": 42.0, \"disaster_risk_index\": 7.5, \"past_calamity_freq\": 6, \"historical_allocation\": 0}', '2026-07-02 14:49:26', 'v1.0');

-- --------------------------------------------------------

--
-- Table structure for table `preposition_records`
--

CREATE TABLE `preposition_records` (
  `preposition_id` int(11) NOT NULL,
  `from_office_id` int(11) NOT NULL,
  `to_barangay_id` int(11) NOT NULL,
  `item_type` enum('food_pack') NOT NULL DEFAULT 'food_pack',
  `quantity` int(11) NOT NULL DEFAULT 0,
  `status` enum('pending','approved','completed') NOT NULL DEFAULT 'pending',
  `preposition_date` date NOT NULL,
  `disaster_event` varchar(150) DEFAULT NULL,
  `event_id` int(11) DEFAULT NULL,
  `created_by` int(11) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `report_logs`
--

CREATE TABLE `report_logs` (
  `report_id` int(11) NOT NULL,
  `report_type` varchar(50) NOT NULL,
  `format` enum('pdf','excel') NOT NULL,
  `pages` int(11) DEFAULT 1,
  `filters_json` text DEFAULT NULL,
  `generated_by` int(11) DEFAULT NULL,
  `generated_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `user_id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('system_admin','pswdo_admin','cswdo_admin','barangay_user') NOT NULL,
  `office_id` int(11) DEFAULT NULL,
  `barangay_id` int(11) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`user_id`, `name`, `email`, `password`, `role`, `office_id`, `barangay_id`, `created_at`) VALUES
(1, 'System Administrator', 'sysadmin@reliefline.gov.ph', 'scrypt:32768:8:1$rZJ0wyp5jKMZSlSF$fe49193bc9ebc64cdbb2b683773f6fdfdbacb0ae75b5f870474893c8bbfceb1a491b599e33999380aa54ddb84b38d488fe7fd4d485d57541a14463e5582897f0', 'system_admin', NULL, NULL, '2026-06-25 10:39:03'),
(2, 'PSWDO Administrator', 'pswdo@reliefline.gov.ph', 'scrypt:32768:8:1$i6W0PofIveIO5HRC$992f01cbebdb36b7145ea6a45e26d03c7476191fa00288570c204acf977c0fa968bdf9d101971eb22d277d3e33a446119356d04be8beb6d9f8be5dea5b23797e', 'pswdo_admin', 1, NULL, '2026-06-25 10:39:03'),
(3, 'Urdaneta CSWDO Admin', 'urdaneta@reliefline.gov.ph', 'scrypt:32768:8:1$ZKjELLHvqL2AFLcS$bcf95bfc8b4a8f90d8930cbe8ea5b11b242c3497142aad77d691e8e4711b6703f717cc932f40808516d166c821556632a1a6a19840429c540fe2982690c95989', 'cswdo_admin', 2, NULL, '2026-06-25 10:39:03'),
(4, 'Santa Barbara MSWDO Admin', 'santabarbara@reliefline.gov.ph', 'scrypt:32768:8:1$6GMVBfFG9nDYWbzN$23657a4cc42e85e194a17b72620ece06ac186e68695f8efe80f98d20f853a20ce204617aaa74c60cd829613139207a736417f5b679a24fe515295c6f7dd0031f', 'cswdo_admin', 3, NULL, '2026-06-25 10:39:03'),
(5, 'Calasiao MSWDO Admin', 'calasiao@reliefline.gov.ph', 'scrypt:32768:8:1$E5AP4eiOESTpVX0D$3c017121506350fab6dc0b10fdecacc58b3c00e5d0fe652a78f5198f97195c740d3875869c8aca273b9d4dc01dddf96c858f4ea25f1c4d033f78e09afb68bd72', 'cswdo_admin', 4, NULL, '2026-06-25 10:39:03');

-- --------------------------------------------------------

--
-- Table structure for table `vehicles`
--

CREATE TABLE `vehicles` (
  `vehicle_id` int(11) NOT NULL,
  `vehicle_name` varchar(100) NOT NULL,
  `office_id` int(11) DEFAULT NULL,
  `plate_number` varchar(20) DEFAULT NULL,
  `capacity_packs` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `vehicles`
--

INSERT INTO `vehicles` (`vehicle_id`, `vehicle_name`, `office_id`, `plate_number`, `capacity_packs`) VALUES
(4, 'Truck 001', 5, 'ABC-1234', 2000),
(5, 'Truck 002', 5, 'DEF-5678', 1500),
(6, 'Truck 003', 5, 'GHI-9012', 1800);

-- --------------------------------------------------------

--
-- Table structure for table `warehouse_transfers`
--

CREATE TABLE `warehouse_transfers` (
  `transfer_id` int(11) NOT NULL,
  `from_office_id` int(11) NOT NULL,
  `to_office_id` int(11) NOT NULL,
  `item_type` enum('food_pack','hygiene_kit','kitchen_kit') DEFAULT 'food_pack',
  `quantity` int(11) NOT NULL,
  `status` enum('pending','completed','cancelled') DEFAULT 'pending',
  `requested_by` int(11) DEFAULT NULL,
  `requested_at` datetime DEFAULT current_timestamp(),
  `completed_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `warehouse_inventory`
--

CREATE TABLE `warehouse_inventory` (
  `inventory_id` int(11) NOT NULL,
  `office_id` int(11) NOT NULL,
  `item_type` varchar(50) NOT NULL,
  `item_name` varchar(100) NOT NULL DEFAULT 'Food Packs',
  `unit` varchar(20) NOT NULL DEFAULT 'packs',
  `quantity_available` int(11) NOT NULL DEFAULT 0,
  `min_stock_level` int(11) NOT NULL DEFAULT 0,
  `last_updated` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `updated_by` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `warehouse_inventory`
--

INSERT INTO `warehouse_inventory` (`inventory_id`, `office_id`, `item_type`, `item_name`, `unit`, `quantity_available`, `min_stock_level`, `last_updated`, `updated_by`) VALUES
(1, 1, 'food_pack', 'Food Packs', 'packs', 5000, 0, '2026-07-17 12:23:28', 2),
(2, 1, 'hygiene_kit', 'Hygiene Kits', 'kits', 1200, 0, '2026-06-25 10:39:04', 2),
(3, 1, 'kitchen_kit', 'Kitchen Kits', 'kits', 800, 0, '2026-06-25 10:39:04', 2),
(4, 2, 'food_pack', 'Food Packs', 'packs', 1500, 0, '2026-06-25 10:39:04', 3),
(5, 2, 'hygiene_kit', 'Hygiene Kits', 'kits', 400, 0, '2026-06-25 10:39:04', 3),
(6, 2, 'kitchen_kit', 'Kitchen Kits', 'kits', 200, 0, '2026-06-25 10:39:04', 3),
(7, 3, 'food_pack', 'Food Packs', 'packs', 1200, 0, '2026-06-25 10:39:04', 4),
(8, 3, 'hygiene_kit', 'Hygiene Kits', 'kits', 300, 0, '2026-06-25 10:39:04', 4),
(9, 3, 'kitchen_kit', 'Kitchen Kits', 'kits', 150, 0, '2026-06-25 10:39:04', 4),
(10, 4, 'food_pack', 'Food Packs', 'packs', 1800, 0, '2026-06-25 10:39:04', 5),
(11, 4, 'hygiene_kit', 'Hygiene Kits', 'kits', 500, 0, '2026-06-25 10:39:04', 5),
(12, 4, 'kitchen_kit', 'Kitchen Kits', 'kits', 250, 0, '2026-06-25 10:39:04', 5),
(13, 5, 'food_pack', 'Food Packs', 'packs', 12600, 3000, '2026-07-17 13:35:28', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `warehouse_stock_logs`
--

CREATE TABLE `warehouse_stock_logs` (
  `log_id` int(11) NOT NULL,
  `office_id` int(11) NOT NULL,
  `item_type` varchar(50) NOT NULL,
  `item_name` varchar(100) NOT NULL,
  `delta` int(11) NOT NULL,
  `reason` varchar(255) DEFAULT NULL,
  `updated_by` int(11) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `activity_logs`
--
ALTER TABLE `activity_logs`
  ADD PRIMARY KEY (`log_id`),
  ADD KEY `actor_id` (`actor_id`),
  ADD KEY `office_id` (`office_id`),
  ADD KEY `barangay_id` (`barangay_id`);

--
-- Indexes for table `allocation_records`
--
ALTER TABLE `allocation_records`
  ADD PRIMARY KEY (`allocation_id`),
  ADD KEY `barangay_id` (`barangay_id`),
  ADD KEY `office_id` (`office_id`),
  ADD KEY `created_by` (`created_by`),
  ADD KEY `fk_alloc_event` (`event_id`),
  ADD KEY `fk_alloc_fulfilling_office` (`fulfilling_office_id`),
  ADD KEY `fk_alloc_decided_by` (`decided_by`);

--
-- Indexes for table `barangays`
--
ALTER TABLE `barangays`
  ADD PRIMARY KEY (`barangay_id`);

--
-- Indexes for table `barangay_disaster_status`
--
ALTER TABLE `barangay_disaster_status`
  ADD PRIMARY KEY (`status_id`),
  ADD UNIQUE KEY `unique_event_barangay` (`event_id`,`barangay_id`),
  ADD KEY `barangay_id` (`barangay_id`),
  ADD KEY `updated_by` (`updated_by`);

--
-- Indexes for table `city_demand_summary`
--
ALTER TABLE `city_demand_summary`
  ADD PRIMARY KEY (`summary_id`),
  ADD KEY `city_municipality` (`city_municipality`);

--
-- Indexes for table `daily_ops_stats`
--
ALTER TABLE `daily_ops_stats`
  ADD PRIMARY KEY (`stat_id`),
  ADD UNIQUE KEY `unique_office_date` (`office_id`,`stat_date`),
  ADD KEY `updated_by` (`updated_by`);

--
-- Indexes for table `disaster_events`
--
ALTER TABLE `disaster_events`
  ADD PRIMARY KEY (`event_id`),
  ADD KEY `created_by` (`created_by`);

--
-- Indexes for table `distribution_records`
--
ALTER TABLE `distribution_records`
  ADD PRIMARY KEY (`distribution_id`),
  ADD KEY `barangay_id` (`barangay_id`),
  ADD KEY `allocation_id` (`allocation_id`),
  ADD KEY `submitted_by` (`submitted_by`),
  ADD KEY `fk_dist_vehicle` (`vehicle_id`),
  ADD KEY `fk_dist_driver` (`driver_id`);

--
-- Indexes for table `drivers`
--
ALTER TABLE `drivers`
  ADD PRIMARY KEY (`driver_id`),
  ADD KEY `office_id` (`office_id`);

--
-- Indexes for table `model_metrics`
--
ALTER TABLE `model_metrics`
  ADD PRIMARY KEY (`metric_id`);

--
-- Indexes for table `offices`
--
ALTER TABLE `offices`
  ADD PRIMARY KEY (`office_id`);

--
-- Indexes for table `prediction_logs`
--
ALTER TABLE `prediction_logs`
  ADD PRIMARY KEY (`log_id`),
  ADD KEY `barangay_id` (`barangay_id`);

--
-- Indexes for table `preposition_records`
--
ALTER TABLE `preposition_records`
  ADD PRIMARY KEY (`preposition_id`),
  ADD KEY `from_office_id` (`from_office_id`),
  ADD KEY `to_barangay_id` (`to_barangay_id`),
  ADD KEY `created_by` (`created_by`),
  ADD KEY `fk_prepo_event` (`event_id`);

--
-- Indexes for table `report_logs`
--
ALTER TABLE `report_logs`
  ADD PRIMARY KEY (`report_id`),
  ADD KEY `generated_by` (`generated_by`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`user_id`),
  ADD UNIQUE KEY `email` (`email`),
  ADD KEY `office_id` (`office_id`),
  ADD KEY `users_barangay_fk` (`barangay_id`);

--
-- Indexes for table `vehicles`
--
ALTER TABLE `vehicles`
  ADD PRIMARY KEY (`vehicle_id`),
  ADD KEY `office_id` (`office_id`);

--
-- Indexes for table `warehouse_transfers`
--
ALTER TABLE `warehouse_transfers`
  ADD PRIMARY KEY (`transfer_id`),
  ADD KEY `from_office_id` (`from_office_id`),
  ADD KEY `to_office_id` (`to_office_id`),
  ADD KEY `requested_by` (`requested_by`);

--
-- Indexes for table `warehouse_inventory`
--
ALTER TABLE `warehouse_inventory`
  ADD PRIMARY KEY (`inventory_id`),
  ADD KEY `office_id` (`office_id`),
  ADD KEY `updated_by` (`updated_by`);

--
-- Indexes for table `warehouse_stock_logs`
--
ALTER TABLE `warehouse_stock_logs`
  ADD PRIMARY KEY (`log_id`),
  ADD KEY `office_id` (`office_id`),
  ADD KEY `updated_by` (`updated_by`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `activity_logs`
--
ALTER TABLE `activity_logs`
  MODIFY `log_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT for table `allocation_records`
--
ALTER TABLE `allocation_records`
  MODIFY `allocation_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=19;

--
-- AUTO_INCREMENT for table `barangays`
--
ALTER TABLE `barangays`
  MODIFY `barangay_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=31;

--
-- AUTO_INCREMENT for table `barangay_disaster_status`
--
ALTER TABLE `barangay_disaster_status`
  MODIFY `status_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT for table `city_demand_summary`
--
ALTER TABLE `city_demand_summary`
  MODIFY `summary_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `daily_ops_stats`
--
ALTER TABLE `daily_ops_stats`
  MODIFY `stat_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `disaster_events`
--
ALTER TABLE `disaster_events`
  MODIFY `event_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `distribution_records`
--
ALTER TABLE `distribution_records`
  MODIFY `distribution_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT for table `drivers`
--
ALTER TABLE `drivers`
  MODIFY `driver_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT for table `model_metrics`
--
ALTER TABLE `model_metrics`
  MODIFY `metric_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `offices`
--
ALTER TABLE `offices`
  MODIFY `office_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT for table `prediction_logs`
--
ALTER TABLE `prediction_logs`
  MODIFY `log_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=1411;

--
-- AUTO_INCREMENT for table `preposition_records`
--
ALTER TABLE `preposition_records`
  MODIFY `preposition_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `report_logs`
--
ALTER TABLE `report_logs`
  MODIFY `report_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `user_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT for table `vehicles`
--
ALTER TABLE `vehicles`
  MODIFY `vehicle_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT for table `warehouse_transfers`
--
ALTER TABLE `warehouse_transfers`
  MODIFY `transfer_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `warehouse_inventory`
--
ALTER TABLE `warehouse_inventory`
  MODIFY `inventory_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=14;

--
-- AUTO_INCREMENT for table `warehouse_stock_logs`
--
ALTER TABLE `warehouse_stock_logs`
  MODIFY `log_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `activity_logs`
--
ALTER TABLE `activity_logs`
  ADD CONSTRAINT `activity_logs_ibfk_1` FOREIGN KEY (`actor_id`) REFERENCES `users` (`user_id`),
  ADD CONSTRAINT `activity_logs_ibfk_2` FOREIGN KEY (`office_id`) REFERENCES `offices` (`office_id`),
  ADD CONSTRAINT `activity_logs_ibfk_3` FOREIGN KEY (`barangay_id`) REFERENCES `barangays` (`barangay_id`);

--
-- Constraints for table `allocation_records`
--
ALTER TABLE `allocation_records`
  ADD CONSTRAINT `allocation_records_ibfk_1` FOREIGN KEY (`barangay_id`) REFERENCES `barangays` (`barangay_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `allocation_records_ibfk_2` FOREIGN KEY (`office_id`) REFERENCES `offices` (`office_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `allocation_records_ibfk_3` FOREIGN KEY (`created_by`) REFERENCES `users` (`user_id`) ON DELETE SET NULL,
  ADD CONSTRAINT `fk_alloc_decided_by` FOREIGN KEY (`decided_by`) REFERENCES `users` (`user_id`),
  ADD CONSTRAINT `fk_alloc_event` FOREIGN KEY (`event_id`) REFERENCES `disaster_events` (`event_id`),
  ADD CONSTRAINT `fk_alloc_fulfilling_office` FOREIGN KEY (`fulfilling_office_id`) REFERENCES `offices` (`office_id`);

--
-- Constraints for table `barangay_disaster_status`
--
ALTER TABLE `barangay_disaster_status`
  ADD CONSTRAINT `barangay_disaster_status_ibfk_1` FOREIGN KEY (`event_id`) REFERENCES `disaster_events` (`event_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `barangay_disaster_status_ibfk_2` FOREIGN KEY (`barangay_id`) REFERENCES `barangays` (`barangay_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `barangay_disaster_status_ibfk_3` FOREIGN KEY (`updated_by`) REFERENCES `users` (`user_id`);

--
-- Constraints for table `daily_ops_stats`
--
ALTER TABLE `daily_ops_stats`
  ADD CONSTRAINT `daily_ops_stats_ibfk_1` FOREIGN KEY (`office_id`) REFERENCES `offices` (`office_id`),
  ADD CONSTRAINT `daily_ops_stats_ibfk_2` FOREIGN KEY (`updated_by`) REFERENCES `users` (`user_id`);

--
-- Constraints for table `disaster_events`
--
ALTER TABLE `disaster_events`
  ADD CONSTRAINT `disaster_events_ibfk_1` FOREIGN KEY (`created_by`) REFERENCES `users` (`user_id`);

--
-- Constraints for table `distribution_records`
--
ALTER TABLE `distribution_records`
  ADD CONSTRAINT `distribution_records_ibfk_1` FOREIGN KEY (`barangay_id`) REFERENCES `barangays` (`barangay_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `distribution_records_ibfk_2` FOREIGN KEY (`allocation_id`) REFERENCES `allocation_records` (`allocation_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `distribution_records_ibfk_3` FOREIGN KEY (`submitted_by`) REFERENCES `users` (`user_id`) ON DELETE SET NULL,
  ADD CONSTRAINT `fk_dist_driver` FOREIGN KEY (`driver_id`) REFERENCES `drivers` (`driver_id`),
  ADD CONSTRAINT `fk_dist_vehicle` FOREIGN KEY (`vehicle_id`) REFERENCES `vehicles` (`vehicle_id`);

--
-- Constraints for table `drivers`
--
ALTER TABLE `drivers`
  ADD CONSTRAINT `drivers_ibfk_1` FOREIGN KEY (`office_id`) REFERENCES `offices` (`office_id`);

--
-- Constraints for table `prediction_logs`
--
ALTER TABLE `prediction_logs`
  ADD CONSTRAINT `prediction_logs_ibfk_1` FOREIGN KEY (`barangay_id`) REFERENCES `barangays` (`barangay_id`) ON DELETE CASCADE;

--
-- Constraints for table `preposition_records`
--
ALTER TABLE `preposition_records`
  ADD CONSTRAINT `fk_prepo_event` FOREIGN KEY (`event_id`) REFERENCES `disaster_events` (`event_id`),
  ADD CONSTRAINT `preposition_records_ibfk_1` FOREIGN KEY (`from_office_id`) REFERENCES `offices` (`office_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `preposition_records_ibfk_2` FOREIGN KEY (`to_barangay_id`) REFERENCES `barangays` (`barangay_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `preposition_records_ibfk_3` FOREIGN KEY (`created_by`) REFERENCES `users` (`user_id`) ON DELETE SET NULL;

--
-- Constraints for table `report_logs`
--
ALTER TABLE `report_logs`
  ADD CONSTRAINT `report_logs_ibfk_1` FOREIGN KEY (`generated_by`) REFERENCES `users` (`user_id`) ON DELETE SET NULL;

--
-- Constraints for table `users`
--
ALTER TABLE `users`
  ADD CONSTRAINT `users_barangay_fk` FOREIGN KEY (`barangay_id`) REFERENCES `barangays` (`barangay_id`) ON DELETE SET NULL,
  ADD CONSTRAINT `users_ibfk_1` FOREIGN KEY (`office_id`) REFERENCES `offices` (`office_id`) ON DELETE SET NULL;

--
-- Constraints for table `vehicles`
--
ALTER TABLE `vehicles`
  ADD CONSTRAINT `vehicles_ibfk_1` FOREIGN KEY (`office_id`) REFERENCES `offices` (`office_id`);

--
-- Constraints for table `warehouse_transfers`
--
ALTER TABLE `warehouse_transfers`
  ADD CONSTRAINT `warehouse_transfers_ibfk_1` FOREIGN KEY (`from_office_id`) REFERENCES `offices` (`office_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `warehouse_transfers_ibfk_2` FOREIGN KEY (`to_office_id`) REFERENCES `offices` (`office_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `warehouse_transfers_ibfk_3` FOREIGN KEY (`requested_by`) REFERENCES `users` (`user_id`) ON DELETE SET NULL;

--
-- Constraints for table `warehouse_inventory`
--
ALTER TABLE `warehouse_inventory`
  ADD CONSTRAINT `warehouse_inventory_ibfk_1` FOREIGN KEY (`office_id`) REFERENCES `offices` (`office_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `warehouse_inventory_ibfk_2` FOREIGN KEY (`updated_by`) REFERENCES `users` (`user_id`) ON DELETE SET NULL;

--
-- Constraints for table `warehouse_stock_logs`
--
ALTER TABLE `warehouse_stock_logs`
  ADD CONSTRAINT `warehouse_stock_logs_ibfk_1` FOREIGN KEY (`office_id`) REFERENCES `offices` (`office_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `warehouse_stock_logs_ibfk_2` FOREIGN KEY (`updated_by`) REFERENCES `users` (`user_id`) ON DELETE SET NULL;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
