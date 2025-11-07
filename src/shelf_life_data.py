# src/shelf_life_data.py
# Assumptions: refrigerated at ≤4°C (≤40°F), unopened unless noted, “days” are conservative safety windows.

SHELF_LIFE_DAYS = {
    "Milk": 7,
    "Yogurt": 14,
    "Cheese": 14,          # varies a lot; this is a conservative value for soft/semi-soft
    "Butter": 60,          # butter is fine 1–2 months refrigerated
    "Chicken": 2,          # raw
    "Beef": 5,             # raw steaks/roasts
    "Fish": 2,             # raw
    "Sausage": 7,          # fully-cooked sausage, opened
    "Ham": 5,              # cooked, sliced
    "Apple": 45,           # whole, refrigerated
    "Banana": 5,           # ripe bananas kept cold to slow spoilage
    "Strawberry": 5,       # whole, dry, unwashed until use
    "Orange": 28,          # whole
    "Grapes": 10,          # unwashed until use
    "Watermelon": 5,       # cut pieces
    "Tomato": 7,           # fully ripe, whole; cut is 3–4 days
    "Lettuce": 7,          # heads ~7–10d; loose/chopped is less
    "Cucumber": 7,         # whole
    "Carrot": 21,          # whole
    "Potato": 28,          # refrigeration not ideal, but ~3–4 weeks if you must
    "Onion": 30,           # dry onions; whole (best in pantry, but ~1 mo in fridge)
    "Juice": 10,           # opened, pasteurized
    "Soda": 3,             # opened; quality window
    "Eggs": 35,            # raw, in shell (3–5 weeks)
    "Ketchup": 180,        # opened
    "Mayonnaise": 60,      # opened, commercial
    "Cooked Rice": 4,
    "Leftovers": 4
}
