import mysql.connector
import config
from datetime import date, timedelta
from shelf_life_data import SHELF_LIFE_DAYS 
from food_categories import FOOD_CATEGORIES
from typing import List, Dict

def normalize_str(s: str | None) -> str | None:
    return s.strip().lower() if isinstance(s, str) else s


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
    name = normalize_str(name)
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
    name = normalize_str(name)
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
    name = normalize_str(name)
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
    name = normalize_str(name)
    storage = normalize_str(storage)
    unit = normalize_str(unit)
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

def add_item_simple(
    name: str,
    quantity: float = 1,
    unit: str = "pcs",
    expiration_date: str | date | None = None,
    storage: str = "fridge",
    location_slot: str | None = None,
) -> int:
    """
    Add a food item by name only.
    Auto-calculates expiration date if omitted (uses shelf-life dictionary).
    """
    name = normalize_str(name)
    storage = normalize_str(storage)
    unit = normalize_str(unit)




    from datetime import date
    from smart_fridge_db import get_or_create_food_type_id, add_item

    # Look up or create the food type and its default shelf life
    shelf_life = SHELF_LIFE_DAYS.get(name, 7)
    food_type_id = get_or_create_food_type_id(
        name,
        average_shelf_life_days=shelf_life
    )

    # Normalize expiration_date
    if expiration_date is not None:
        if isinstance(expiration_date, str):
            expiration_date = date.fromisoformat(expiration_date)
    else:
        if storage == "fridge":
            expiration_date = date.today() + timedelta(days=shelf_life)
        else:  # freezer
            expiration_date = None

    if storage == "freezer":
        expiration_date = None

    # Insert into DB
    item_id = add_item(
        food_type_id=food_type_id,
        quantity=quantity,
        unit=unit,
        expiration_date=expiration_date,
        detection_label=name,
        added_by="user",
        storage=storage,
        location_slot=location_slot
    )

    print(
        f"✅ Added {quantity} {unit} of {name} ({storage})"
        f"{' expiring on ' + str(expiration_date) if expiration_date else ''}"
    )

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
    from food_classifier import classify_food

    # 1) Classify the image
    predicted_name, predicted_conf = classify_food(image_path)
    label = normalize_str(predicted_name) or "unknown"
    storage = normalize_str(storage)
    unit = normalize_str(unit)

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

    if storage == "freezer":
        exp_dt = None

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


def consume(name: str, qty_used: float, item_id: int | None = None) -> str:
    """
    Consume (use/eat) a quantity of a food item.

    Args:
        name (str): The food name as stored in item_status_view.food_name.
        qty_used (float): How much of the item you consumed.
        item_id (int | None): Optional. If given, we target that exact row.
                              If None:
                                - if there is exactly ONE item with this name → we use it
                                - if there are MULTIPLE items → we raise an error asking for item_id

    Returns:
        str: "deleted"  if the item was fully consumed and removed from DB
             "updated"  if only quantity was decreased

    Raises:
        ValueError: if qty_used is invalid, item not found, or more was requested than available.
    """

    name = normalize_str(name)

    # --- Basic validation on qty_used ---
    if qty_used <= 0:
        raise ValueError("Consumed quantity must be positive.")

    # ------------------------------------------------------------------
    # 1) FIRST PHASE: READ-ONLY SELECT (using first DB connection)
    # ------------------------------------------------------------------
    # We open a connection only to read from item_status_view and then
    # CLOSE IT COMPLETELY before doing any write queries.
    # This avoids "Commands out of sync" errors from MySQL.
    # ------------------------------------------------------------------
    conn = get_connection()
    try:
        # dictionary=True → rows are dicts: row["item_id"], row["quantity"], etc.
        with conn.cursor(dictionary=True) as cur:
            # Get all rows for this food name, ordered by soonest expiration first.
            cur.execute("""
                SELECT item_id, quantity, unit, expiration_date
                FROM item_status_view
                WHERE food_name = %s
                ORDER BY expiration_date ASC;
            """, (name,))
            items = cur.fetchall()
    finally:
        # Close the first connection entirely after reading.
        conn.close()

    # If there are no items at all with this name, we can't consume anything.
    if not items:
        raise ValueError(f"'{name}' is not in your fridge.")

    # ------------------------------------------------------------------
    # 2) DECIDE WHICH ROW TO CONSUME FROM
    # ------------------------------------------------------------------

    # If item_id is NOT provided:
    if item_id is None:
        # If there is exactly one matching item, it's safe to auto-pick it.
        if len(items) == 1:
            item = items[0]
        else:
            # Ambiguous: multiple items with same name.
            # We force the caller to specify item_id to avoid consuming wrong row.
            raise ValueError(
                f"Multiple '{name}' items exist. Specify item_id. "
                f"IDs available: " + ", ".join(str(i['item_id']) for i in items)
            )
    else:
        # If item_id IS provided, we search among the fetched rows for that exact id.
        matching = [i for i in items if i["item_id"] == item_id]
        if not matching:
            # No row with that id + name combination.
            raise ValueError(f"No '{name}' found with item_id={item_id}.")
        item = matching[0]

    # Extract current quantity and its unit from the chosen row.
    current_qty = float(item["quantity"])
    unit = item["unit"]
    item_id = item["item_id"]  # ensure we use the exact id from DB

    # ------------------------------------------------------------------
    # 3) VALIDATE THAT WE ARE NOT EATING MORE THAN WE HAVE
    # ------------------------------------------------------------------
    if qty_used > current_qty:
        raise ValueError(
            f"Cannot consume {qty_used}{unit}; only {current_qty}{unit} available."
        )

    # ------------------------------------------------------------------
    # 4) SECOND PHASE: WRITE OPERATION (new DB connection)
    # ------------------------------------------------------------------
    # We open a NEW connection for the DELETE/UPDATE.
    # This separation (read-connection vs write-connection) avoids the
    # "Commands out of sync" problems MySQL sometimes has when you do
    # SELECT then DELETE/UPDATE on the same connection/cursor.
    # ------------------------------------------------------------------
    conn2 = get_connection()
    try:
        with conn2.cursor() as cur2:

            # ---- Case A: we consumed exactly the entire quantity ----
            if qty_used == current_qty:
                # Delete the row completely from food_items.
                cur2.execute("DELETE FROM food_items WHERE item_id = %s", (item_id,))
                conn2.commit()
                print(f"🗑️ Fully consumed and removed {name} (ID {item_id})")
                return "deleted"

            # ---- Case B: partial consumption, we just reduce the quantity ----
            new_qty = current_qty - qty_used
            cur2.execute("""
                UPDATE food_items
                SET quantity = %s
                WHERE item_id = %s
            """, (new_qty, item_id))
            conn2.commit()

            print(f"🍽️ Consumed {qty_used}{unit} of {name}. Remaining: {new_qty}{unit}.")
            return "updated"

    finally:
        # Always close the second connection, even if an exception occurs.
        conn2.close()



def get_fridge_items_for_llm(user_id: int | None = None) -> List[Dict]:
    """
    Return ingredients in a simple format for the LLM:

    [
      {"name": "chicken breast", "expires_in_days": 2},
      {"name": "spinach", "expires_in_days": 5},
      ...
    ]

    - Uses item_status_view.
    - Includes BOTH fridge and freezer items (storage IN ('fridge','freezer')).
    - For rows with a real expiration_date, we compute days until expiry.
    - For rows with expiration_date = NULL (e.g. freezer items), we treat them
      as very long shelf-life (e.g. 365 days) so they are available but not urgent.
    - If multiple rows share the same food_name, we keep the *smallest*
      expires_in_days (most urgent one).
    - Currently user_id is ignored because the schema is global; kept only
      for future multi-user support.
    """
    conn = get_connection()
    try:
        with conn.cursor(dictionary=True) as cur:
            cur.execute("""
                SELECT food_name, expiration_date, storage, quantity
                FROM item_status_view
                WHERE quantity > 0
                  AND storage IN ('fridge', 'freezer');
            """)
            rows = cur.fetchall()
    finally:
        conn.close()

    today = date.today()
    name_to_days: Dict[str, int] = {}

    for row in rows:
        food_name = row["food_name"]
        exp_date = row["expiration_date"]
        storage = row["storage"]

        # If we have a real expiration_date, compute days left
        if exp_date is not None:
            days_left = (exp_date - today).days
            expires_in_days = max(days_left, 0)
        else:
            # No expiration_date (e.g. freezer item): treat as long shelf life.
            # You can tweak this number (365, 999, etc.) as you like.
            expires_in_days = 365

        # Aggregate: keep the most urgent (smallest days) per food_name
        if food_name in name_to_days:
            name_to_days[food_name] = min(name_to_days[food_name], expires_in_days)
        else:
            name_to_days[food_name] = expires_in_days

    # Convert to list for the LLM
    items: List[Dict] = [
        {"name": name, "expires_in_days": days}
        for name, days in name_to_days.items()
    ]

    return items

