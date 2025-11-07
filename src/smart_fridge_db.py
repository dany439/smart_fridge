import mysql.connector
from datetime import date
from . import config

def get_connection():
    """Create a new DB connection."""
    return mysql.connector.connect(
        host=config.MYSQL_HOST,
        port=config.MYSQL_PORT,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DB,
    )

# ---------- Food type helpers ----------

def get_food_type_id_by_name(name: str):
    """Return food_type_id for a given name, or None if not found."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT food_type_id FROM food_types WHERE name=%s;", (name,))
            row = cur.fetchone()
            return row[0] if row else None
    finally:
        conn.close()

def create_food_type(name: str, category: str = None, average_shelf_life_days: int = None,
                     calories_per_100g: float = None, notes: str = None) -> int:
    """Create a new food type and return its id."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO food_types (name, category, average_shelf_life_days, calories_per_100g, notes)
                VALUES (%s, %s, %s, %s, %s);
            """, (name, category, average_shelf_life_days, calories_per_100g, notes))
            conn.commit()
            return cur.lastrowid
    finally:
        conn.close()

def get_or_create_food_type_id(name: str, category: str = None, average_shelf_life_days: int = None) -> int:
    """Fetch id for a food type by name, or create it if missing."""
    ftid = get_food_type_id_by_name(name)
    if ftid is not None:
        return ftid
    return create_food_type(name=name, category=category, average_shelf_life_days=average_shelf_life_days)

# ---------- Item operations ----------

def add_item(food_type_id: int, quantity: float = 1, unit: str = 'pcs',
             added_by: str = 'user', detection_label: str = None,
             confidence: float = None, date_added: date = None,
             expiration_date=None, location_slot: str = None, image_path: str = None) -> int:
    """
    Insert an item. If expiration_date is None, the DB trigger uses the food type's shelf life.
    Returns the inserted item_id.
    """
    if date_added is None:
        date_added = date.today()

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO food_items
                    (food_type_id, quantity, unit, date_added, expiration_date,
                     detection_label, confidence_score, image_path, location_slot, added_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, (food_type_id, quantity, unit, date_added, expiration_date,
                  detection_label, confidence, image_path, location_slot, added_by))
            conn.commit()
            return cur.lastrowid
    finally:
        conn.close()

def add_item_by_name(name: str, quantity: float = 1, unit: str = 'pcs',
                     added_by: str = 'user', detection_label: str = None,
                     confidence: float = None, category: str = None,
                     average_shelf_life_days: int = None, **kwargs) -> int:
    """
    Convenience: ensure the food type exists, then add the item.
    kwargs are passed to add_item (e.g., location_slot, image_path).
    """
    ftid = get_or_create_food_type_id(name, category=category,
                                      average_shelf_life_days=average_shelf_life_days)
    return add_item(ftid, quantity=quantity, unit=unit, added_by=added_by,
                    detection_label=detection_label or name, confidence=confidence, **kwargs)

def get_all_items():
    """Return all items with computed status (via view) as dicts."""
    conn = get_connection()
    try:
        with conn.cursor(dictionary=True) as cur:
            cur.execute("SELECT * FROM item_status_view ORDER BY expiration_date IS NULL, expiration_date;")
            return cur.fetchall()
    finally:
        conn.close()

def get_expiring_items(days: int = 2):
    """Return items expiring within the next 'days' days (including today)."""
    conn = get_connection()
    try:
        with conn.cursor(dictionary=True) as cur:
            cur.execute("""
                SELECT * FROM item_status_view
                WHERE expiration_date IS NOT NULL
                  AND DATEDIFF(expiration_date, CURDATE()) BETWEEN 0 AND %s
                ORDER BY expiration_date;
            """, (days,))
            return cur.fetchall()
    finally:
        conn.close()

def delete_item(item_id: int) -> int:
    """Delete an item by id. Returns number of rows affected."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM food_items WHERE item_id=%s;", (item_id,))
            conn.commit()
            return cur.rowcount
    finally:
        conn.close()
