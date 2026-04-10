import os
import json
from anthropic import Anthropic
from agent.state import AgentState

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are a fitness logging assistant. Parse the user's message and extract meal or workout information.

Respond with a JSON object in this exact format:
{
  "response": "Logged! Here's what I recorded...",
  "log_type": "meal" or "workout",
  "entry": {
    // For meals:
    "name": "food name",
    "estimated_calories": 350,
    "estimated_protein_g": 30,
    "estimated_carbs_g": 40,
    "estimated_fat_g": 10,
    "notes": ""
    // For workouts:
    // "type": "Push Day",
    // "exercises_completed": ["Bench Press", "Overhead Press"],
    // "duration_min": 60,
    // "notes": ""
  },
  "daily_totals": {
    "calories": 1200,
    "protein_g": 90,
    "carbs_g": 140,
    "fat_g": 35
  }
}

Estimate nutrition values based on typical serving sizes when exact amounts aren't given.
Add the new entry to the running daily totals from the context provided.
"""


def run(state: AgentState) -> AgentState:
    last_message = state["messages"][-1].content if state["messages"] else ""
    daily_log = state.get("daily_log", [])
    goal = state.get("goal", {})

    # Build running totals context
    total_cal = sum(
        e.get("estimated_calories", 0) for e in daily_log if e.get("log_type") == "meal"
    )
    total_protein = sum(
        e.get("entry", {}).get("estimated_protein_g", 0)
        for e in daily_log
        if e.get("log_type") == "meal"
    )

    context = (
        f"Daily calorie target: {goal.get('daily_calorie_target', 'not set')}\n"
        f"Protein target: {goal.get('daily_protein_target_g', 'not set')}g\n"
        f"Calories logged so far today: {total_cal}\n"
        f"Protein logged so far today: {total_protein}g\n"
        f"Entries so far: {json.dumps(daily_log[-5:])}\n"  # last 5 for context
    )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=600,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"{context}\nUser message: {last_message}"}],
    )

    raw = response.content[0].text.strip()
    try:
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {**state, "response": raw}

    new_entry = {
        "log_type": parsed.get("log_type", "meal"),
        "entry": parsed.get("entry", {}),
    }
    updated_log = daily_log + [new_entry]

    return {
        **state,
        "daily_log": updated_log,
        "response": parsed.get("response", "Logged!"),
    }
