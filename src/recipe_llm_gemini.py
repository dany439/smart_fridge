# recipe_llm_gemini.py
import os
import json
from typing import List, Dict

import google.generativeai as genai
from config import GEMINI_API_KEY

# Configure global API key
genai.configure(api_key=GEMINI_API_KEY)

# Force JSON output so it's easy to parse
generation_config = genai.GenerationConfig(
    temperature=0.7,
    response_mime_type="application/json",  # return JSON as text
)

# This is exactly the model you asked for:
model = genai.GenerativeModel(
    "models/gemini-2.5-flash",
    generation_config=generation_config,
)

SYSTEM_PROMPT = """
You are a recipe generator for a smart fridge.

The input you receive will contain:
- FRIDGE_ITEMS: a JSON array of objects, each:
    { "name": string, "expires_in_days": integer }
- MAX_RECIPES: an integer.

Your tasks:
1. Generate up to MAX_RECIPES recipes that make good use of the ingredients in FRIDGE_ITEMS.
2. Prefer ingredients that are closer to expiring (smaller expires_in_days),
   but you MAY also use ingredients that are not in FRIDGE_ITEMS.
3. Do NOT remove a recipe just because some ingredients are not in FRIDGE_ITEMS.
4. Keep recipes realistic and simple.

Each recipe you output MUST have exactly these fields:
- title: string
- ingredients: array of strings (ingredient names)
- steps: array of short strings (cooking steps)

Important:
- Do NOT include any other fields.
- Do NOT include categories.
- Output ONLY valid JSON with this structure:

{
  "recipes": [
    {
      "title": "string",
      "ingredients": ["string", "..."],
      "steps": ["step 1", "step 2", "..."]
    }
  ]
}
"""


def _build_prompt(fridge_items: List[Dict], max_recipes: int) -> str:
    """
    Build a single text prompt that includes the system instructions + data.
    """
    return (
        SYSTEM_PROMPT
        + "\n\nFRIDGE_ITEMS:\n"
        + json.dumps(fridge_items, indent=2)
        + f"\n\nMAX_RECIPES: {max_recipes}\n"
        + "\nReturn ONLY the JSON object described above."
    )


def generate_recipes_with_gemini(
    fridge_items: List[Dict],
    max_recipes: int = 10,
) -> List[Dict]:
    """
    Call Gemini 2.5 Flash via GenerativeModel and get recipes.

    fridge_items: [{"name": str, "expires_in_days": int}, ...]
    Returns:
        [
          {
            "title": str,
            "ingredients": [str, ...],
            "steps": [str, ...]
          },
          ...
        ]
    """
    prompt = _build_prompt(fridge_items, max_recipes)

    # Single-turn text generation
    response = model.generate_content(prompt)

    # response.text should already be valid JSON (because of response_mime_type)
    try:
        data = json.loads(response.text)
    except json.JSONDecodeError:
        # Fallback if something went wrong
        return []

    recipes = data.get("recipes", [])
    if not isinstance(recipes, list):
        return []

    return recipes
