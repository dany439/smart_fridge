USE smart_fridge;

-- 1) Add storage column to items
CREATE TABLE IF NOT EXISTS food_items (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    food_type_id INT NOT NULL,
    quantity DECIMAL(8,2) DEFAULT 1.00,
    unit VARCHAR(20) DEFAULT 'pcs',
    date_added DATE NOT NULL,
    expiration_date DATE,
    detection_label VARCHAR(100),
    confidence_score DECIMAL(5,3),
    image_path VARCHAR(255),
    location_slot VARCHAR(50),
    added_by ENUM('user','camera','barcode') DEFAULT 'user',
    storage ENUM('fridge','freezer') NOT NULL DEFAULT 'fridge',          -- ← NEW
    CONSTRAINT fk_food_items_type
      FOREIGN KEY (food_type_id) REFERENCES food_types(food_type_id)
      ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_expiration_date (expiration_date),
    INDEX idx_storage (storage)
) ENGINE=InnoDB;

-- 2) Recreate the status view to account for freezer
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
        WHEN i.storage = 'freezer'              THEN 'frozen'
        WHEN i.expiration_date IS NULL          THEN 'unknown'
        WHEN i.expiration_date < CURDATE()      THEN 'expired'
        WHEN DATEDIFF(i.expiration_date, CURDATE()) <= 2 THEN 'expiring soon'
        ELSE 'fresh'
    END AS status,
    i.storage,                                                  -- ← include storage in the view
    i.location_slot,
    i.added_by,
    i.detection_label,
    i.confidence_score,
    i.image_path
FROM food_items i
JOIN food_types t ON i.food_type_id = t.food_type_id;

-- 3) Trigger: do not set expiration for frozen items
DROP TRIGGER IF EXISTS set_expiration_date_before_insert;
DELIMITER $$
CREATE TRIGGER set_expiration_date_before_insert
BEFORE INSERT ON food_items
FOR EACH ROW
BEGIN
    DECLARE shelf_life INT;

    -- If frozen, we keep expiration_date as NULL (treated as 'frozen')
    IF NEW.storage = 'freezer' THEN
        SET NEW.expiration_date = NULL;
    ELSE
        SELECT average_shelf_life_days INTO shelf_life
        FROM food_types WHERE food_type_id = NEW.food_type_id;

        IF NEW.expiration_date IS NULL AND shelf_life IS NOT NULL THEN
            SET NEW.expiration_date = DATE_ADD(NEW.date_added, INTERVAL shelf_life DAY);
        END IF;
    END IF;
END$$
DELIMITER ;
