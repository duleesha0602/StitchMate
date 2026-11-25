import pymysql
import pymysql.cursors
from werkzeug.security import generate_password_hash

# MySQL Configuration for XAMPP / phpMyAdmin
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'port': 3306,
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

DB_NAME = 'stitchmate_db'

def get_server_connection():
    """Connect to MySQL server without specifying a database"""
    return pymysql.connect(**DB_CONFIG)

def get_db_connection():
    """Connect directly to the stitchmate_db database"""
    config = DB_CONFIG.copy()
    config['database'] = DB_NAME
    return pymysql.connect(**config)

def init_db():
    """Create stitchmate_db database, tables, run migrations, and seed sample data"""
    # 1. Create Database if not exists
    server_conn = get_server_connection()
    try:
        with server_conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        server_conn.commit()
    finally:
        server_conn.close()

    # 2. Connect to database and create/migrate tables
    db_conn = get_db_connection()
    try:
        with db_conn.cursor() as cursor:
            # Users table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS `users` (
                `id` INT AUTO_INCREMENT PRIMARY KEY,
                `username` VARCHAR(100) NOT NULL UNIQUE,
                `password` VARCHAR(255) NOT NULL,
                `role` ENUM('tailor', 'customer') NOT NULL,
                `language` VARCHAR(10) DEFAULT 'en',
                `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # Tailor Profiles table
            cursor.execute("""
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
            """)

            # Customers table
            cursor.execute("""
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
            """)

            # Customer Contact Numbers
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS `customer_contact_numbers` (
                `id` INT AUTO_INCREMENT PRIMARY KEY,
                `customer_id` INT NOT NULL,
                `phone_number` VARCHAR(50) NOT NULL,
                `type` ENUM('Current', 'Previous') DEFAULT 'Current',
                `is_primary` TINYINT(1) DEFAULT 0,
                `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (`customer_id`) REFERENCES `customers`(`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # Measurements table (with extended fields)
            cursor.execute("""
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
            """)

            # Custom Measurement Types (Req 13)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS `custom_measurement_types` (
                `id` INT AUTO_INCREMENT PRIMARY KEY,
                `tailor_id` INT NOT NULL,
                `name` VARCHAR(100) NOT NULL,
                `unit` ENUM('Inches', 'CM') DEFAULT 'Inches',
                `description` VARCHAR(255) DEFAULT NULL,
                `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (`tailor_id`) REFERENCES `tailor_profiles`(`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # Custom Measurement Values
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS `custom_measurement_values` (
                `id` INT AUTO_INCREMENT PRIMARY KEY,
                `measurement_id` INT NOT NULL,
                `type_id` INT NOT NULL,
                `value` DECIMAL(6,2) NOT NULL,
                `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (`measurement_id`) REFERENCES `measurements`(`id`) ON DELETE CASCADE,
                FOREIGN KEY (`type_id`) REFERENCES `custom_measurement_types`(`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # Orders table (with Cancelled status support)
            cursor.execute("""
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
            """)

            # Order Status History table
            cursor.execute("""
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
            """)

            # Notifications table
            cursor.execute("""
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
            """)

            # Migrations for existing database:
            # 1. Update orders status ENUM to include 'Cancelled'
            try:
                cursor.execute("""
                    ALTER TABLE `orders` 
                    MODIFY COLUMN `status` ENUM('Pending', 'Cutting', 'Stitching', 'Ready', 'Cancelled') DEFAULT 'Pending';
                """)
            except Exception:
                pass

            # 2. Modify orders.measurement_id to allow NULL and ON DELETE SET NULL
            try:
                cursor.execute("""
                    ALTER TABLE `orders` MODIFY COLUMN `measurement_id` INT DEFAULT NULL;
                """)
            except Exception:
                pass

            # 3. Add extended columns to measurements if not present
            for col in ['arm_length', 'trouser_length', 'inseam']:
                try:
                    cursor.execute(f"ALTER TABLE `measurements` ADD COLUMN `{col}` DECIMAL(6,2) DEFAULT NULL;")
                except Exception:
                    pass

            # 4. Add photo column to tailor_profiles if not present
            try:
                cursor.execute("ALTER TABLE `tailor_profiles` ADD COLUMN `photo` VARCHAR(255) DEFAULT 'avatar_tailor_artisan_1793872634583.jpg';")
            except Exception:
                pass

            # 5. Add language column to users if not present
            try:
                cursor.execute("ALTER TABLE `users` ADD COLUMN `language` VARCHAR(10) DEFAULT 'en';")
            except Exception:
                pass

            # Seed custom measurement types if empty
            cursor.execute("SELECT COUNT(*) AS cnt FROM `custom_measurement_types`")
            if cursor.fetchone()['cnt'] == 0:
                cursor.execute("SELECT id FROM `tailor_profiles` LIMIT 1")
                tp = cursor.fetchone()
                if tp:
                    cursor.execute("""
                        INSERT INTO `custom_measurement_types` (`tailor_id`, `name`, `unit`, `description`) VALUES
                        (%s, 'Ankle Circumference', 'Inches', 'Measured around ankle'),
                        (%s, 'Bicep Round', 'Inches', 'Widest part of upper arm')
                    """, (tp['id'], tp['id']))

            # Check if sample tailor exists
            cursor.execute("SELECT COUNT(*) AS cnt FROM `users` WHERE `role` = 'tailor'")
            tailor_count = cursor.fetchone()['cnt']
            
            if tailor_count == 0:
                seed_initial_data(cursor)

        db_conn.commit()
    finally:
        db_conn.close()

def seed_initial_data(cursor):
    """Seed initial screenshot data: Nilu, Sachi, Nimal, ORD001-ORD004, MEA001-MEA003"""
    pwd_hash = generate_password_hash('tailor123')
    cursor.execute("""
        INSERT INTO `users` (`username`, `password`, `role`, `language`)
        VALUES (%s, %s, 'tailor', 'en')
    """, ('tailor@stitchmate.lk', pwd_hash))
    tailor_user_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO `tailor_profiles` (`user_id`, `name`, `shop_name`, `email`, `primary_contact`, `additional_contact`, `address`, `photo`)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (tailor_user_id, 'Kavinda Perera', 'StitchMate Atelier', 'tailor@stitchmate.lk', '0771234567', '0112345678', 'No. 45, High Level Road, Maharagama', 'avatar_tailor_artisan_1793872634583.jpg'))
    tailor_profile_id = cursor.lastrowid

    # Seed initial custom measurement types
    cursor.execute("""
        INSERT INTO `custom_measurement_types` (`tailor_id`, `name`, `unit`, `description`) VALUES
        (%s, 'Arm Length', 'Inches', 'Length from shoulder tip to wrist'),
        (%s, 'Trouser Length', 'Inches', 'Outseam from waist to ankle'),
        (%s, 'Inseam', 'Inches', 'Inner leg length from crotch to ankle')
    """, (tailor_profile_id, tailor_profile_id, tailor_profile_id))

    # Nilu (CUS001)
    nilu_pwd = generate_password_hash('customer123')
    cursor.execute("""
        INSERT INTO `users` (`username`, `password`, `role`, `language`)
        VALUES (%s, %s, 'customer', 'en')
    """, ('nilu', nilu_pwd))
    nilu_user_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO `customers` (`customer_code`, `user_id`, `name`, `nickname`, `gender`, `primary_contact`, `address`, `photo`, `login_status`)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Online')
    """, ('CUS001', nilu_user_id, 'Nilmini Perera', 'Nilu', 'Female', '0761234567', 'Temple Road, Maharagama', 'avatar_tailor_artisan_1793872634583.jpg'))
    cus1_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO `customer_contact_numbers` (`customer_id`, `phone_number`, `type`, `is_primary`) VALUES
        (%s, '0771234567', 'Previous', 0),
        (%s, '0711234567', 'Previous', 0),
        (%s, '0761234567', 'Current', 1)
    """, (cus1_id, cus1_id, cus1_id))

    # Sachi (CUS002)
    cursor.execute("""
        INSERT INTO `customers` (`customer_code`, `user_id`, `name`, `nickname`, `gender`, `primary_contact`, `address`, `login_status`)
        VALUES (%s, NULL, %s, %s, %s, %s, %s, 'Walk-in')
    """, ('CUS002', 'Sachini Fernando', 'Sachi', 'Female', '0712345678', 'Station Road, Nugegoda'))
    cus2_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO `customer_contact_numbers` (`customer_id`, `phone_number`, `type`, `is_primary`)
        VALUES (%s, '0712345678', 'Current', 1)
    """, (cus2_id,))

    # Nimal (CUS003)
    cursor.execute("""
        INSERT INTO `customers` (`customer_code`, `user_id`, `name`, `nickname`, `gender`, `primary_contact`, `address`, `login_status`)
        VALUES (%s, NULL, %s, %s, %s, %s, %s, 'Walk-in')
    """, ('CUS003', 'Nimal Jayasinghe', 'Nimal', 'Male', '0758889999', 'Main Street, Colombo 03'))
    cus3_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO `customer_contact_numbers` (`customer_id`, `phone_number`, `type`, `is_primary`)
        VALUES (%s, '0758889999', 'Current', 1)
    """, (cus3_id,))

    # Measurements
    cursor.execute("""
        INSERT INTO `measurements` (`measurement_code`, `customer_id`, `measurement_date`, `unit`, `chest`, `waist`, `hip`, `shoulder`, `dress_length`, `arm_length`, `notes`)
        VALUES (%s, %s, '2026-09-20', 'Inches', 34, 28, 36, 14, 40, 22, 'Comfortable fit for casual frock')
    """, ('MEA001', cus1_id))
    mea1_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO `measurements` (`measurement_code`, `customer_id`, `measurement_date`, `unit`, `chest`, `waist`, `sleeve_length`, `notes`)
        VALUES (%s, %s, '2026-10-02', 'Inches', 32, 26, 6, 'Blouse fitting with puff sleeves')
    """, ('MEA002', cus2_id))
    mea2_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO `measurements` (`measurement_code`, `customer_id`, `measurement_date`, `unit`, `chest`, `waist`, `shoulder`, `neck`, `trouser_length`, `inseam`, `notes`)
        VALUES (%s, %s, '2026-10-10', 'CM', 96, 84, 44, 38, 102, 78, 'Formal slim fit long sleeve shirt and trouser')
    """, ('MEA003', cus3_id))
    mea3_id = cursor.lastrowid

    # Orders
    cursor.execute("""
        INSERT INTO `orders` (
            `order_code`, `customer_id`, `measurement_id`, `clothing_type`,
            `design_description`, `fabric_type`, `fabric_colour`, `fabric_description`,
            `order_date`, `due_date`, `total_price`, `advance_paid`, `advance_amount`, `remaining_balance`, `status`
        ) VALUES (
            'ORD001', %s, %s, 'Frock',
            'A-line party frock with pleats and waist bow', 'Cotton', 'Blue', 'Floral pattern light cotton',
            '2026-10-25', '2026-11-05', 5000.00, 1, 1500.00, 3500.00, 'Stitching'
        )
    """, (cus1_id, mea1_id))
    ord1_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO `orders` (
            `order_code`, `customer_id`, `measurement_id`, `clothing_type`,
            `design_description`, `fabric_type`, `fabric_colour`, `fabric_description`,
            `order_date`, `due_date`, `total_price`, `advance_paid`, `advance_amount`, `remaining_balance`, `status`
        ) VALUES (
            'ORD002', %s, %s, 'Blouse',
            'V-neck saree blouse with piping on neck and arms', 'Silk', 'Rose Pink', 'Pure raw silk fabric',
            '2026-10-28', '2026-11-08', 2500.00, 0, 0.00, 2500.00, 'Pending'
        )
    """, (cus2_id, mea2_id))
    ord2_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO `orders` (
            `order_code`, `customer_id`, `measurement_id`, `clothing_type`,
            `design_description`, `fabric_type`, `fabric_colour`, `fabric_description`,
            `order_date`, `due_date`, `total_price`, `advance_paid`, `advance_amount`, `remaining_balance`, `status`
        ) VALUES (
            'ORD003', %s, %s, 'Shirt',
            'Long sleeve formal shirt with French collar', 'Linen', 'White', 'Premium white organic linen',
            '2026-10-20', '2026-11-03', 3200.00, 1, 1000.00, 2200.00, 'Cutting'
        )
    """, (cus3_id, mea3_id))
    ord3_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO `orders` (
            `order_code`, `customer_id`, `measurement_id`, `clothing_type`,
            `design_description`, `fabric_type`, `fabric_colour`, `fabric_description`,
            `order_date`, `due_date`, `total_price`, `advance_paid`, `advance_amount`, `remaining_balance`, `status`
        ) VALUES (
            'ORD004', %s, %s, 'Skirt',
            'High-waisted pleated midi skirt with side zip', 'Cotton', 'Navy Blue', 'Structured twill cotton',
            '2026-10-22', '2026-11-04', 1800.00, 1, 1800.00, 0.00, 'Ready'
        )
    """, (cus1_id, mea1_id))
    ord4_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO `order_status_history` (`order_id`, `old_status`, `new_status`, `changed_by`, `note`) VALUES
        (%s, 'New Order', 'Pending', 'Tailor', 'Order received'),
        (%s, 'Pending', 'Cutting', 'Tailor', 'Fabric cutting finished'),
        (%s, 'Cutting', 'Stitching', 'Tailor', 'Under stitching work'),
        (%s, 'New Order', 'Pending', 'Tailor', 'Awaiting fabric preparation'),
        (%s, 'New Order', 'Cutting', 'Tailor', 'Cut patterns laid out'),
        (%s, 'New Order', 'Pending', 'Tailor', 'Order registered'),
        (%s, 'Pending', 'Cutting', 'Tailor', 'Fabric measured and cut'),
        (%s, 'Cutting', 'Stitching', 'Tailor', 'Sewing completed'),
        (%s, 'Stitching', 'Ready', 'Tailor', 'Ironed and packed ready for collection')
    """, (ord1_id, ord1_id, ord1_id, ord2_id, ord3_id, ord4_id, ord4_id, ord4_id, ord4_id))

    cursor.execute("""
        INSERT INTO `notifications` (`customer_id`, `order_id`, `title`, `message`, `is_read`, `created_at`)
        VALUES (%s, %s, %s, %s, 0, '2026-11-04 14:30:00')
    """, (cus1_id, ord4_id, 'Your order is ready! → Nilu', 'Your Skirt (ORD004) is now ready for collection.'))
