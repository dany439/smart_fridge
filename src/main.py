from src.setup_db import ensure_schema
from src.shelf_life_data import SHELF_LIFE_DAYS
from src.smart_fridge_db import add_item_by_name, get_all_items, get_expiring_items, clear_database
from datetime import datetime

def demo():
    # 1️⃣ Ensure DB and tables exist
    ensure_schema()
    print("✅ Database schema verified or created.\n")

    # 2️⃣ Add sample items
    print("📦 Adding demo food items...")
    test_items = ["Milk", "Apple", "Chicken", "Lettuce", "Leftovers"]
    for name in test_items:
        shelf_life = SHELF_LIFE_DAYS.get(name, 7)
        add_item_by_name(
            name,
            quantity=1,
            unit="pcs",
            added_by="demo",
            average_shelf_life_days=shelf_life,
            detection_label=name,
            confidence=0.99,
        )
    print("✅ Demo items added.\n")

    # 3️⃣ Fetch and display all items
    print("🧊 CURRENT FRIDGE CONTENTS")
    print("-" * 80)
    for item in get_all_items():
        added = item["date_added"]
        exp = item["expiration_date"]
        status = item["status"]
        print(f"{item['food_name']:<12} | Added: {added} | Expires: {exp} | Status: {status}")

    # 4️⃣ Show items expiring soon
    expiring = get_expiring_items(3)
    if expiring:
        print("\n⚠️ ITEMS EXPIRING WITHIN 3 DAYS")
        print("-" * 80)
        for item in expiring:
            print(f"{item['food_name']:<12} → {item['expiration_date']} ({item['status']})")
    else:
        print("\n🎉 Nothing expiring soon!")

    clear_database()

if __name__ == "__main__":
    demo()
