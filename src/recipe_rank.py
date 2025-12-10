# recipe_rank.py
from typing import List, Dict

EXPIRY_WINDOW_DAYS = 7  # tweak if you want


def split_and_rank_recipes(
    recipes: List[Dict],
    fridge_items: List[Dict],
) -> List[Dict]:
    """
    Enrich recipes with:
      - ingredients_available
      - ingredients_missing
      - expiry_score
    and sort by expiry_score desc.
    """
    name_to_days = {i["name"].lower(): i["expires_in_days"] for i in fridge_items}
    fridge_names = set(name_to_days.keys())

    enriched = []

    for r in recipes:
        all_ings = r.get("ingredients", []) or []

        available = []
        missing = []

        for ing in all_ings:
            key = ing.lower()
            if key in fridge_names:
                available.append(ing)
            else:
                missing.append(ing)

        score = 0
        for ing in available:
            d = name_to_days.get(ing.lower())
            if d is None:
                continue
            contribution = max(0, EXPIRY_WINDOW_DAYS - d)
            score += contribution

        enriched.append(
            {
                "title": r.get("title", ""),
                "ingredients": all_ings,
                "steps": r.get("steps", []),
                "ingredients_available": available,
                "ingredients_missing": missing,
                "expiry_score": score,
            }
        )

    enriched.sort(key=lambda r: r["expiry_score"], reverse=True)
    return enriched
