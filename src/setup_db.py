import os
import mysql.connector


def ensure_schema(
    host: str = None,
    port: int = None,
    user: str = None,
    password: str = None,
    database: str = None,
):
    """
    Ensure the smart_fridge database and schema exist.
    Safe to run multiple times.
    """

    # --- Read config / env ---
    host = host or os.getenv("MYSQL_HOST", "127.0.0.1")
    port = int(port or os.getenv("MYSQL_PORT", "3306"))
    user = user or os.getenv("MYSQL_USER", "root")
    password = password or os.getenv("MYSQL_PASSWORD", "")
    database = database or os.getenv("MYSQL_DB", "smart_fridge")

    # ------------------------------------------------------------------
    # 1) Ensure database exists
    # ------------------------------------------------------------------
    server_conn = mysql.connector.connect(
        host=host,
        port=port,
        user=user,
        password=password,
    )
    server_conn.autocommit = True

    with server_conn.cursor() as cur:
        cur.execute(f"""
            CREATE DATABASE IF NOT EXISTS `{database}`
            CHARACTER SET utf8mb4
            COLLATE utf8mb4_general_ci;
        """)

    server_conn.close()

    # ------------------------------------------------------------------
    # 2) Connect to the database
    # ------------------------------------------------------------------
    conn = mysql.connector.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
    )

    try:
        with conn.cursor() as cur:

            # ----------------------------------------------------------
            # food_types
            # ----------------------------------------------------------
            cur.execute("""
                CREATE TABLE IF NOT EXISTS food_types (
                    food_type_id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL UNIQUE,
                    category VARCHAR(50) NOT NULL,
                    average_shelf_life_days INT DEFAULT NULL,
                    calories_per_100g DECIMAL(8,2) DEFAULT NULL,
                    notes TEXT DEFAULT NULL
                ) ENGINE=InnoDB;
            """)

            # ----------------------------------------------------------
            # food_items
            # ----------------------------------------------------------
            cur.execute("""
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
                    storage ENUM('fridge','freezer') NOT NULL DEFAULT 'fridge',

                    CONSTRAINT fk_food_items_type
                        FOREIGN KEY (food_type_id)
                        REFERENCES food_types(food_type_id)
                        ON DELETE CASCADE
                        ON UPDATE CASCADE,

                    INDEX idx_expiration_date (expiration_date),
                    INDEX idx_storage (storage)
                ) ENGINE=InnoDB;
            """)

            # ----------------------------------------------------------
            # item_status_view
            # ----------------------------------------------------------
            cur.execute("""
                CREATE OR REPLACE VIEW item_status_view AS
                SELECT
                    i.item_id,
                    t.food_type_id,
                    t.name AS food_name,
                    t.category AS food_category,
                    i.quantity,
                    i.unit,
                    i.date_added,
                    i.expiration_date,
                    CASE
                        WHEN i.storage = 'freezer' THEN 'frozen'
                        WHEN i.expiration_date IS NULL THEN 'unknown'
                        WHEN i.expiration_date < CURDATE() THEN 'expired'
                        WHEN DATEDIFF(i.expiration_date, CURDATE()) <= 2 THEN 'expiring soon'
                        ELSE 'fresh'
                    END AS status,
                    i.storage,
                    i.location_slot,
                    i.added_by,
                    i.detection_label,
                    i.confidence_score,
                    i.image_path
                FROM food_items i
                JOIN food_types t
                  ON i.food_type_id = t.food_type_id;
            """)

        conn.commit()

    finally:
        conn.close()
