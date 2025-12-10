# recipes_service.py
from typing import List, Dict

from src.smart_fridge_db import get_fridge_items_for_llm
from src.recipe_llm_gemini import generate_recipes_with_gemini
from src.recipe_rank import split_and_rank_recipes  # your local logic


def get_recipe_suggestions_for_user(
    user_id: int = None,
    max_recipes: int = 10,
) -> List[Dict]:
    """
    1) Read fridge items from DB.
    2) Ask Gemini (2.5 Flash) to generate recipes (title, ingredients, steps).
    3) Split into available/missing + compute expiry_score.
    4) Return recipes sorted by expiry_score.
    """
    fridge_items = get_fridge_items_for_llm(user_id)
    if not fridge_items:
        return []

    raw_recipes = generate_recipes_with_gemini(fridge_items, max_recipes)
    if not raw_recipes:
        return []

    ranked = split_and_rank_recipes(raw_recipes, fridge_items)
    return ranked
