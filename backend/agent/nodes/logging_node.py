import os
import re
import json
from anthropic import Anthropic
from agent.state import AgentState

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are a fitness logging assistant. You MUST output ONLY a valid JSON object. No prose, no explanation, no markdown code fences, no text before or after the JSON. Your entire response must be parseable by json.loads().

Parse the user's message and extract meal or workout information. When the user refers to a scheduled workout (e.g. "Wednesday workout"), use the provided workout plan to fill in the exercises.

Output this exact JSON structure:
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

DAYS = {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}


def run(state: AgentState) -> AgentState:
    last_message = state["messages"][-1].content if state["messages"] else ""
    daily_log = state.get("daily_log", [])
    goal = state.get("goal", {})

    # Build running totals context
    total_cal = sum(
        e.get("entry", {}).get("estimated_calories", 0)
        for e in daily_log
        if e.get("log_type") == "meal"
    )
    total_protein = sum(
        e.get("entry", {}).get("estimated_protein_g", 0)
        for e in daily_log
        if e.get("log_type") == "meal"
    )

    # Build workout plan context so agent knows what each day's workout contains
    current_plan = state.get("current_plan", {})
    # Handle both flat (DB-loaded) and nested (in-session after planning node) shapes
    workout_days = current_plan.get("workout_plan", current_plan)
    workout_plan_context = ""
    plan_lines = []
    for day, day_data in workout_days.items():
        if day not in DAYS or not isinstance(day_data, dict):
            continue
        focus = day_data.get("focus", "")
        exercises = day_data.get("exercises", [])
        if not exercises and not focus:
            continue
        exercise_names = ", ".join(ex.get("name", "") for ex in exercises if ex.get("name"))
        line = f"  {day.capitalize()}: {focus}"
        if exercise_names:
            line += f" — {exercise_names}"
        plan_lines.append(line)
    if plan_lines:
        workout_plan_context = "Current weekly workout plan:\n" + "\n".join(plan_lines) + "\n"

    context = (
        f"{workout_plan_context}"
        f"Daily calorie target: {goal.get('daily_calorie_target', 'not set')}\n"
        f"Protein target: {goal.get('daily_protein_target_g', 'not set')}g\n"
        f"Calories logged so far today: {total_cal}\n"
        f"Protein logged so far today: {total_protein}g\n"
        f"Entries so far: {json.dumps(daily_log[-5:])}\n"
    )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=600,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"{context}\nUser message: {last_message}"}],
    )

    raw = response.content[0].text.strip()
    parsed = None

    # Tier 1: clean JSON (expected path after prompt fix)
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Tier 2: strip markdown fences
    if parsed is None:
        try:
            fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
            if fence_match:
                parsed = json.loads(fence_match.group(1))
        except json.JSONDecodeError:
            pass

    # Tier 3: extract any JSON object from mixed text
    if parsed is None:
        try:
            obj_match = re.search(r"\{.*\}", raw, re.DOTALL)
            if obj_match:
                parsed = json.loads(obj_match.group())
        except json.JSONDecodeError:
            pass

    if parsed is None:
        return {**state, "response": "I had trouble logging that. Could you rephrase?"}

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
