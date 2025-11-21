import mysql.connector
from . import config
from datetime import date, timedelta
from src.shelf_life_data import SHELF_LIFE_DAYS 
from src.food_categories import FOOD_CATEGORIES

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

    # --- If category not manually provided, try dictionary ---
    if category is None:
        category = FOOD_CATEGORIES.get(name, "other")

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

def get_expired_items():
    """Return expired items (fridge only)."""
    conn = get_connection()
    try:
        with conn.cursor(dictionary=True) as cur:
            cur.execute("""
                SELECT *
                FROM item_status_view
                WHERE storage = 'fridge'
                  AND expiration_date IS NOT NULL
                  AND DATEDIFF(expiration_date, CURDATE()) < 0 
                ORDER BY expiration_date;
            """)
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

from datetime import date, timedelta  # make sure this is at the top of the file

def add_item_by_image(
    image_path: str,
    quantity: float,
    unit: str = "pcs",
    expiration_date: str | date | None = None,
    storage: str = "fridge",                 # 'fridge' | 'freezer'
    location_slot: str | None = None,
) -> int:
    """
    Add an item using only an image (plus basic quantity/unit/storage).

    Steps:
      1. Runs classify_food(image_path) -> (name, confidence)
      2. Uses that name to look up/create a food_type with a default shelf life.
      3. If no expiration_date is given:
           - fridge  -> today + shelf_life
           - freezer -> NULL (no expiry)
      4. Inserts the row via add_item, storing:
           - detection_label = predicted name
           - confidence      = model confidence
           - image_path      = given image_path
           - added_by        = "camera"
    """

    # Import here to avoid circular imports
    from .food_classifier import classify_food

    # 1) Classify the image
    predicted_name, predicted_conf = classify_food(image_path)
    label = predicted_name or "Unknown"

    # 2) Shelf life and food type
    shelf_life = SHELF_LIFE_DAYS.get(label, 7)
    ftid = get_or_create_food_type_id(
        label,
        average_shelf_life_days=shelf_life
    )

    # 3) Normalize expiration_date
    if expiration_date is None:
        if storage == "freezer":
            exp_dt = None
        else:
            exp_dt = date.today() + timedelta(days=shelf_life)
    else:
        exp_dt = date.fromisoformat(expiration_date) if isinstance(expiration_date, str) else expiration_date

    # 4) Insert into DB
    item_id = add_item(
    food_type_id=ftid,
    quantity=quantity,
    unit=unit,
    expiration_date=exp_dt,
    detection_label=label,
    confidence=predicted_conf,
    image_path=image_path,
    location_slot=location_slot,
    added_by="camera",
    storage=storage,
)

    # ---- CLEAN PRINT (assumes classifier always works) ----
    if exp_dt:
        print(f"✅ Added {quantity} {unit} of {label} ({storage}) expiring on {exp_dt}")
    else:
        print(f"✅ Added {quantity} {unit} of {label} ({storage})")

    return item_id


