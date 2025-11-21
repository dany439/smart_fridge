from src.setup_db import ensure_schema
from src.shelf_life_data import SHELF_LIFE_DAYS
from src.food_categories import FOOD_CATEGORIES
from src.smart_fridge_db import add_item_by_name, get_all_items, get_expiring_items, get_freezer_items, clear_database, add_item_simple, add_item_by_image
from src.food_classifier import classify_food
from time import time

def demo():
    ensure_schema()
    
    # Add with auto expiry (uses shelf-life dictionary)
    add_item_simple("Milk", quantity=1, unit="bottle")

    add_item_simple("Burger", quantity=2, unit = "pcs", expiration_date= "2025-11-08")

    # Add with explicit expiry date
    add_item_simple("Chicken", quantity=2, unit="pcs", expiration_date="2025-11-12")
    add_item_simple("Chicken", quantity=4, unit="pcs")

    # Add frozen (no expiry)
    add_item_simple("Fish", quantity=3, unit="fillets", storage="freezer")

    add_item_by_image("pictures\\sushi.jpg", quantity= 12, storage="freezer")

    

    print("\nAll items:")
    for item in get_all_items():
        print(f"{item['food_name']:<12} | storage={item['storage']} | expires={item['expiration_date']} | status={item['status']}")

    print("\nExpiring within 3 days (fridge only):")
    for item in get_expiring_items(3):
        print(f"{item['food_name']:<12} → {item['expiration_date']} ({item['status']})")

    print("\nFreezer items (never marked expiring):")
    for item in get_freezer_items():
        print(f"{item['food_name']:<12} | status={item['status']}")

    clear_database()

if __name__ == "__main__":
    demo()

    # t0 = time()
    # print(classify_food("pictures\\sushi.jpg", visualize= False))
    # t1 = time()
    # print(classify_food("pictures\\Perfect-Pan-Seared-Ribeye-Steak.jpg", visualize= False))
    # t2 = time()
    # print("iteration 1 took", (t1 - t0), "iteration 2 took:", (t2 - t1))
