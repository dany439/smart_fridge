from datetime import date
from smart_fridge_db import (
    add_item_by_name,
    get_all_items,
    get_expiring_items,
)

def demo():
    # Add some types/items (Apple shelf life 20 days; Milk 7 days)
    add_item_by_name("Apple", quantity=4, unit="pcs", added_by="camera",
                     average_shelf_life_days=20, detection_label="Apple", confidence=0.98)

    add_item_by_name("Milk", quantity=1, unit="bottle", added_by="user",
                     average_shelf_life_days=7, detection_label="Milk 1L", confidence=0.95)

    # Show items with status
    print("\nAll items:")
    for row in get_all_items():
        print(row)

    print("\nExpiring within 2 days:")
    for row in get_expiring_items(2):
        print(row)

if __name__ == "__main__":
    demo()