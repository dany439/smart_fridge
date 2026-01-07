from setup_db import ensure_schema
from shelf_life_data import SHELF_LIFE_DAYS
from food_categories import FOOD_CATEGORIES
from smart_fridge_db import *
from food_classifier import classify_food
from time import time
from recipe_service import get_recipe_suggestions_for_user
from pprint import pprint

def demo():
    ensure_schema()

    # # Add with auto expiry (uses shelf-life dictionary)
    # add_item_simple("Milk", quantity=1, unit="bottle")

    # #add_item_simple("Burger", quantity=2, unit = "pcs", expiration_date= "2025-12-11")

    # # Add with explicit expiry date
    # add_item_simple("Chicken", quantity=2, unit="pcs", expiration_date="2025-12-14")
    # add_item_simple("Beef", quantity=4, unit="pcs")
    # add_item_simple("Shrimp", quantity=4, unit="pcs")
    # add_item_simple("rice", quantity=4, unit="pcs")
    # add_item_simple("pork", quantity=4, unit="pcs")

    # # Add frozen (no expiry)
    # add_item_simple("Fish", quantity=3, unit="fillets", storage="freezer")

    # add_item_by_image("pictures\\the-best-spaghetti-bolognese-7e83155.jpg", quantity= 12)

    # #consume("Chicken", 2,3)


    # # print("\nAll items:")
    # # for item in get_all_items():
    # #     print(f"id={item['item_id']} | {item['food_name']:<12} | storage={item['storage']} | expires={item['expiration_date']} | status={item['status']}")

    # # print("\nExpiring within 3 days (fridge only):")
    # # for item in get_expiring_items(3):
    # #     print(f"id={item['item_id']} | {item['food_name']:<12} → {item['expiration_date']} ({item['status']})")

    # # print("\nFreezer items (never marked expiring):")
    # # for item in get_freezer_items():
    # #     print(f"id={item['item_id']} | {item['food_name']:<12} | status={item['status']}")
    # user_id = 1  # change if you want

    # print("\n=== Fetching recipe suggestions ===\n")
    # result = get_recipe_suggestions_for_user(user_id=user_id, max_recipes=5)

    # # Normalize: result might be a list OR {"recipes": [...]}
    # if isinstance(result, dict) and "recipes" in result:
    #     recipes = result["recipes"] or []
    # elif isinstance(result, list):
    #     recipes = result
    # else:
    #     recipes = []

    # if not recipes:
    #     print("No recipes returned. Check that you have items in the DB and that Gemini is configured correctly.")
    #     return

    # print(f"Got {len(recipes)} recipes:\n")

    # for i, r in enumerate(recipes, start=1):
    #     title = r.get("title", "Untitled")
    #     ingredients = r.get("ingredients", []) or []
    #     available = r.get("ingredients_available", []) or []
    #     missing = r.get("ingredients_missing", []) or []
    #     steps = r.get("steps", []) or []
    #     score = r.get("expiry_score", 0)

    #     print(f"==================== Recipe {i} ====================")
    #     print(f"Title: {title}")
    #     print(f"Urgency score (near-expiry usage): {score}")
    #     print()

    #     print("All ingredients suggested:")
    #     if ingredients:
    #         for ing in ingredients:
    #             print(f"  - {ing}")
    #     else:
    #         print("  (none)")
    #     print()

    #     print("Available in your fridge/freezer:")
    #     if available:
    #         for ing in available:
    #             print(f"  - {ing}")
    #     else:
    #         print("  (none)")
    #     print()

    #     print("Missing ingredients (you need to buy):")
    #     if missing:
    #         for ing in missing:
    #             print(f"  - {ing}")
    #     else:
    #         print("  (none)")
    #     print()

    #     print("Steps:")
    #     if steps:
    #         for idx, step in enumerate(steps, start=1):
    #             # Make sure step is a string
    #             step_str = str(step)
    #             print(f"  {idx}. {step_str}")
    #     else:
    #         print("  (no steps provided)")
    #     print("====================================================\n")



    clear_database()

if __name__ == "__main__":
    demo()

    # t0 = time()
    # print(classify_food("pictures\\sushi.jpg", visualize= False))
    # t1 = time()
    # print(classify_food("pictures\\the-best-spaghetti-bolognese-7e83155.jpg", visualize= False))
    # t2 = time()
    # print("iteration 1 took", (t1 - t0), "iteration 2 took:", (t2 - t1))



# import os
# from dotenv import load_dotenv
# import google.generativeai as genai

# load_dotenv()

# genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# # Use a model that EXISTS in your list
# model = genai.GenerativeModel("models/gemini-2.5-flash")

# response = model.generate_content("Hello Gemini, can you confirm the API works now?")

# print(response.text)

