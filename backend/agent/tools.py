import httpx
from langchain_core.tools import tool


@tool
def lookup_nutrition(food_name: str) -> dict:
    """Look up nutritional info for a food item using Open Food Facts API.
    Returns calories, protein, carbs, and fat per 100g serving."""
    url = "https://world.openfoodfacts.org/cgi/search.pl"
    params = {
        "search_terms": food_name,
        "json": 1,
        "page_size": 3,
        "fields": "product_name,nutriments",
    }
    try:
        resp = httpx.get(url, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        products = data.get("products", [])
        if not products:
            return {"error": f"No nutrition data found for '{food_name}'"}

        product = products[0]
        nutriments = product.get("nutriments", {})
        return {
            "name": product.get("product_name", food_name),
            "calories_per_100g": nutriments.get("energy-kcal_100g", 0),
            "protein_per_100g": nutriments.get("proteins_100g", 0),
            "carbs_per_100g": nutriments.get("carbohydrates_100g", 0),
            "fat_per_100g": nutriments.get("fat_100g", 0),
        }
    except Exception as e:
        return {"error": str(e)}


@tool
def search_exercise_info(query: str) -> str:
    """Search for exercise information, alternatives, or fitness advice.
    Use this when the user asks about specific exercises or needs alternatives."""
    # Lightweight stub — in production, wire to a search API or fitness DB
    return (
        f"Exercise info for '{query}': "
        "Use proper form, warm up before exercise, and consult a trainer for complex movements. "
        "For alternatives to common exercises: squats → leg press/lunges, "
        "bench press → dumbbell press/push-ups, deadlifts → Romanian deadlifts/hip hinges."
    )
