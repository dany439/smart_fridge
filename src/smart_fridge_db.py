import mysql.connector
from . import config
from datetime import date, timedelta
from src.shelf_life_data import SHELF_LIFE_DAYS 

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
             expiration_date=None, location_slot: str = None,
             image_path: str = None, storage: str = 'fridge') -> int:      # ← NEW param
    if date_added is None:
        date_added = date.today()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO food_items
                    (food_type_id, quantity, unit, date_added, expiration_date,
                     detection_label, confidence_score, image_path, location_slot,
                     added_by, storage)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, (food_type_id, quantity, unit, date_added, expiration_date,
                  detection_label, confidence, image_path, location_slot,
                  added_by, storage))
            conn.commit()
            return cur.lastrowid
    finally:
        conn.close()

def add_item_by_name(name: str, quantity: float = 1, unit: str = 'pcs',
                     added_by: str = 'user', detection_label: str = None,
                     confidence: float = None, category: str = None,
                     average_shelf_life_days: int = None, storage: str = 'fridge', **kwargs) -> int:  # ← NEW
    ftid = get_or_create_food_type_id(name, category=category,
                                      average_shelf_life_days=average_shelf_life_days)
    return add_item(ftid, quantity=quantity, unit=unit, added_by=added_by,
                    detection_label=detection_label or name, confidence=confidence,
                    storage=storage, **kwargs)

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
    """Return items expiring within next 'days' days (fridge only)."""
    conn = get_connection()
    try:
        with conn.cursor(dictionary=True) as cur:
            cur.execute("""
                SELECT *
                FROM item_status_view
                WHERE storage = 'fridge'
                  AND expiration_date IS NOT NULL
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

def clear_database():
    """Deletes all rows from food_items and food_types."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
            cur.execute("TRUNCATE TABLE food_items;")
            cur.execute("TRUNCATE TABLE food_types;")
            cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
        conn.commit()
        print("🧹 Database cleared.")
    finally:
        conn.close()

def get_freezer_items():
    conn = get_connection()
    try:
        with conn.cursor(dictionary=True) as cur:
            cur.execute("SELECT * FROM item_status_view WHERE storage='freezer' ORDER BY food_name;")
            return cur.fetchall()
    finally:
        conn.close()

def add_item_simple(name: str, quantity: float = 1, unit: str = "pcs", 
                    expiration_date: str | None = None, storage: str = "fridge") -> int:
    """
    Add a food item by name only.
    You specify: name, quantity, unit, and optionally expiration_date.
    If expiration_date is omitted, it's auto-calculated using the shelf-life dictionary.
    """
    from .smart_fridge_db import get_or_create_food_type_id, add_item   # to avoid circular imports

    # Look up or create the food type and its default shelf life
    shelf_life = SHELF_LIFE_DAYS.get(name, 7)
    food_type_id = get_or_create_food_type_id(name, average_shelf_life_days=shelf_life)

    # Determine the expiry date if none given
    if not expiration_date and storage == "fridge":
        expiration_date = date.today().toordinal() + shelf_life  # temp as int
        expiration_date = date.fromordinal(expiration_date)
    elif storage == "freezer":
        expiration_date = None  # frozen items don't expire

    # Insert into DB
    item_id = add_item(
        food_type_id=food_type_id,
        quantity=quantity,
        unit=unit,
        expiration_date=expiration_date,
        detection_label=name,
        added_by="user",
        storage=storage
    )

    print(f"✅ Added {quantity} {unit} of {name} ({storage})"
          f"{' expiring on ' + str(expiration_date) if expiration_date else ''}")
    return item_id

def add_item_by_image(
    image_path: str,
    quantity: float,
    unit: str = "pcs",
    name: str | None = None,                 # optional: if you already know the label
    expiration_date: str | date | None = None,
    storage: str = "fridge",                 # 'fridge' | 'freezer'
    detection_label: str | None = None,      # optional: if coming from a model
    confidence: float | None = None,
    location_slot: str | None = None,
) -> int:
    """
    Create/lookup the food type (by 'name' or 'detection_label'), then insert an item
    with the provided image, quantity, unit, and optional expiry date.
    If no expiry is passed:
      - fridge: uses SHELF_LIFE_DAYS to compute a date
      - freezer: keeps expiration_date = NULL
    """
    label = name or detection_label or "Unknown"
    shelf_life = SHELF_LIFE_DAYS.get(label, 7)

    # ensure food type exists
    ftid = get_or_create_food_type_id(label, average_shelf_life_days=shelf_life)

    # normalize expiration_date
    exp_dt: date | None
    if expiration_date:
        exp_dt = date.fromisoformat(expiration_date) if isinstance(expiration_date, str) else expiration_date
    else:
        exp_dt = None if storage == "freezer" else (date.today() + timedelta(days=shelf_life))

    # insert
    return add_item(
        food_type_id=ftid,
        quantity=quantity,
        unit=unit,
        expiration_date=exp_dt,
        detection_label=label,
        confidence=confidence,
        image_path=image_path,
        location_slot=location_slot,
        added_by="camera",
        storage=storage,
    )


