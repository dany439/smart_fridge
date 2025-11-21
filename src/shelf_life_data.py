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
    'Caesar Salad': 3,              # dressed greens; quality drops sooner
    'Chicken Wings': 4,             # cooked poultry
    'French Fries': 4,              # cooked potatoes/veg
    'Fried Rice': 4,                # cooked rice
    'Hamburger': 4,                 # cooked ground beef patty
    'Ice Cream': 0,                 # keep FROZEN (not a fridge item)
    'Pizza': 4,
    'Spaghetti Bolognese': 4,       # cooked meat/pasta dish
    'Steak': 4,                     # cooked beef
    'Sushi': 1,                     # assume raw fish sushi; eat within 24h
    "Leftovers": 4
}
