-- Create database (optional if you already have one)
CREATE DATABASE IF NOT EXISTS smart_fridge
  CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE smart_fridge;

-- 1) Reference table: each row is a food type (reusable knowledge)
CREATE TABLE IF NOT EXISTS food_types (
    food_type_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,         -- e.g., 'Milk', 'Apple', 'Chicken Breast'
    category VARCHAR(50),                      -- e.g., 'Dairy', 'Fruit', 'Meat'
    average_shelf_life_days INT,               -- used to auto-calc expiration
    calories_per_100g DECIMAL(6,2),            -- optional nutrition
    notes TEXT
) ENGINE=InnoDB;

-- 2) Instance table: each row is a specific item in the fridge
CREATE TABLE IF NOT EXISTS food_items (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    food_type_id INT NOT NULL,
    quantity DECIMAL(8,2) DEFAULT 1.00,
    unit VARCHAR(20) DEFAULT 'pcs',
    date_added DATE NOT NULL,
    expiration_date DATE,                      -- auto-filled by trigger if NULL
    detection_label VARCHAR(100),
    confidence_score DECIMAL(5,3),             -- e.g., 0.945
    image_path VARCHAR(255),
    location_slot VARCHAR(50),
    added_by ENUM('user','camera','barcode') DEFAULT 'user',
    CONSTRAINT fk_food_items_type
      FOREIGN KEY (food_type_id) REFERENCES food_types(food_type_id)
      ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_expiration_date (expiration_date)
) ENGINE=InnoDB;

-- 3) View: computed status ('fresh' | 'expiring soon' | 'expired' | 'unknown')
-- Views are virtual and always up to date.
CREATE OR REPLACE VIEW item_status_view AS
SELECT 
    i.item_id,
    t.food_type_id,
    t.name       AS food_name,
    t.category   AS food_category,
    i.quantity,
    i.unit,
    i.date_added,
    i.expiration_date,
    CASE
        WHEN i.expiration_date IS NULL THEN 'unknown'
        WHEN i.expiration_date < CURDATE() THEN 'expired'
        WHEN DATEDIFF(i.expiration_date, CURDATE()) <= 2 THEN 'expiring soon'
        ELSE 'fresh'
    END AS status,
    i.location_slot,
    i.added_by,
    i.detection_label,
    i.confidence_score,
    i.image_path
FROM food_items i
JOIN food_types t ON i.food_type_id = t.food_type_id;

-- 4) Trigger: if expiration_date not provided, compute it from average_shelf_life_days
-- Note: DELIMITER is a client directive used by the MySQL CLI to allow BEGIN..END blocks.
DELIMITER $$

CREATE TRIGGER set_expiration_date_before_insert
BEFORE INSERT ON food_items
FOR EACH ROW
BEGIN
    DECLARE shelf_life INT;
    SELECT average_shelf_life_days
      INTO shelf_life
      FROM food_types
     WHERE food_type_id = NEW.food_type_id;

    IF NEW.expiration_date IS NULL AND shelf_life IS NOT NULL THEN
        SET NEW.expiration_date = DATE_ADD(NEW.date_added, INTERVAL shelf_life DAY);
    END IF;
END$$

DELIMITER ;
