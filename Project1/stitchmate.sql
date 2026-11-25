-- StitchMate Tailor Customer Management & Custom Measurement Locker System
-- Complete Database Schema for MySQL / phpMyAdmin (Updated Version)

CREATE DATABASE IF NOT EXISTS `stitchmate_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `stitchmate_db`;

-- 1. Users Table (Tailor and Customer logins + Language preference)
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(100) NOT NULL UNIQUE,
    `password` VARCHAR(255) NOT NULL,
    `role` ENUM('tailor', 'customer') NOT NULL,
    `language` VARCHAR(10) DEFAULT 'en',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Tailor Profiles Table (With photo and brand info)
CREATE TABLE IF NOT EXISTS `tailor_profiles` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `name` VARCHAR(150) NOT NULL,
    `shop_name` VARCHAR(150) NOT NULL,
    `email` VARCHAR(150) NOT NULL,
    `primary_contact` VARCHAR(50) NOT NULL,
    `additional_contact` VARCHAR(50) DEFAULT NULL,
    `address` TEXT DEFAULT NULL,
    `photo` VARCHAR(255) DEFAULT 'avatar_tailor_artisan_1793872634583.jpg',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Customers Table
CREATE TABLE IF NOT EXISTS `customers` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `customer_code` VARCHAR(20) NOT NULL UNIQUE,
    `user_id` INT DEFAULT NULL,
    `name` VARCHAR(150) NOT NULL,
    `nickname` VARCHAR(100) NOT NULL,
    `gender` ENUM('Male', 'Female') NOT NULL,
    `primary_contact` VARCHAR(50) NOT NULL,
    `address` TEXT DEFAULT NULL,
    `photo` VARCHAR(255) DEFAULT NULL,
    `login_status` ENUM('Walk-in', 'Online') DEFAULT 'Walk-in',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Customer Contact Numbers Table (With Previous history preservation)
CREATE TABLE IF NOT EXISTS `customer_contact_numbers` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `customer_id` INT NOT NULL,
    `phone_number` VARCHAR(50) NOT NULL,
    `type` ENUM('Current', 'Previous') DEFAULT 'Current',
    `is_primary` TINYINT(1) DEFAULT 0,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`customer_id`) REFERENCES `customers`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Measurements Table (Extended Fit Points & Historical preservation)
CREATE TABLE IF NOT EXISTS `measurements` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `measurement_code` VARCHAR(20) NOT NULL UNIQUE,
    `customer_id` INT NOT NULL,
    `measurement_date` DATE NOT NULL,
    `unit` ENUM('Inches', 'CM') DEFAULT 'Inches',
    `chest` DECIMAL(6,2) DEFAULT NULL,
    `waist` DECIMAL(6,2) DEFAULT NULL,
    `hip` DECIMAL(6,2) DEFAULT NULL,
    `shoulder` DECIMAL(6,2) DEFAULT NULL,
    `sleeve_length` DECIMAL(6,2) DEFAULT NULL,
    `dress_length` DECIMAL(6,2) DEFAULT NULL,
    `neck` DECIMAL(6,2) DEFAULT NULL,
    `arm_length` DECIMAL(6,2) DEFAULT NULL,
    `trouser_length` DECIMAL(6,2) DEFAULT NULL,
    `inseam` DECIMAL(6,2) DEFAULT NULL,
    `notes` TEXT DEFAULT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`customer_id`) REFERENCES `customers`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Custom Measurement Types (Tailor managed)
CREATE TABLE IF NOT EXISTS `custom_measurement_types` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `tailor_id` INT NOT NULL,
    `name` VARCHAR(100) NOT NULL,
    `unit` ENUM('Inches', 'CM') DEFAULT 'Inches',
    `description` VARCHAR(255) DEFAULT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`tailor_id`) REFERENCES `tailor_profiles`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. Custom Measurement Values
CREATE TABLE IF NOT EXISTS `custom_measurement_values` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `measurement_id` INT NOT NULL,
    `type_id` INT NOT NULL,
    `value` DECIMAL(6,2) NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`measurement_id`) REFERENCES `measurements`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`type_id`) REFERENCES `custom_measurement_types`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. Orders Table (With Cancelled status & SET NULL on measurement deletion)
CREATE TABLE IF NOT EXISTS `orders` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `order_code` VARCHAR(20) NOT NULL UNIQUE,
    `customer_id` INT NOT NULL,
    `measurement_id` INT DEFAULT NULL,
    `clothing_type` VARCHAR(100) NOT NULL,
    `other_clothing_name` VARCHAR(100) DEFAULT NULL,
    `design_description` TEXT DEFAULT NULL,
    `design_photo` VARCHAR(255) DEFAULT NULL,
    `fabric_type` VARCHAR(100) DEFAULT NULL,
    `fabric_colour` VARCHAR(100) DEFAULT NULL,
    `fabric_description` TEXT DEFAULT NULL,
    `fabric_photo` VARCHAR(255) DEFAULT NULL,
    `order_date` DATE NOT NULL,
    `due_date` DATE NOT NULL,
    `total_price` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `advance_paid` TINYINT(1) DEFAULT 0,
    `advance_amount` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `remaining_balance` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `status` ENUM('Pending', 'Cutting', 'Stitching', 'Ready', 'Cancelled') DEFAULT 'Pending',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`customer_id`) REFERENCES `customers`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`measurement_id`) REFERENCES `measurements`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 9. Order Status History Table
CREATE TABLE IF NOT EXISTS `order_status_history` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `order_id` INT NOT NULL,
    `old_status` VARCHAR(50) DEFAULT NULL,
    `new_status` VARCHAR(50) NOT NULL,
    `changed_by` VARCHAR(100) DEFAULT 'Tailor',
    `note` VARCHAR(255) DEFAULT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`order_id`) REFERENCES `orders`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 10. Notifications Table
CREATE TABLE IF NOT EXISTS `notifications` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `customer_id` INT NOT NULL,
    `order_id` INT DEFAULT NULL,
    `title` VARCHAR(255) NOT NULL,
    `message` TEXT NOT NULL,
    `is_read` TINYINT(1) DEFAULT 0,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`customer_id`) REFERENCES `customers`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`order_id`) REFERENCES `orders`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
