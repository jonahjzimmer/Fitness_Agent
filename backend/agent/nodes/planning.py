import os
import json
from anthropic import Anthropic
from agent.state import AgentState

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are a professional fitness and nutrition coach.
When the user describes their fitness goal, create a detailed weekly plan.

Always respond with a JSON object in this exact format:
{
  "response": "A friendly, motivating message to the user",
  "goal": {
    "description": "User's stated goal",
    "target_weight": null,
    "current_weight": null,
    "timeline_weeks": null,
    "workouts_per_week": 4,
    "daily_calorie_target": 2000,
    "daily_protein_target_g": 150
  },
  "workout_plan": {
    "monday": {"focus": "Push (Chest/Shoulders/Triceps)", "exercises": [{"name": "Bench Press", "sets": 4, "reps": "8-10"}, {"name": "Overhead Press", "sets": 3, "reps": "8-10"}, {"name": "Incline Dumbbell Press", "sets": 3, "reps": "10-12"}, {"name": "Lateral Raises", "sets": 3, "reps": "12-15"}, {"name": "Tricep Pushdowns", "sets": 3, "reps": "12-15"}]},
    "tuesday": {"focus": "Rest or Light Cardio", "exercises": []},
    "wednesday": {"focus": "Pull (Back/Biceps)", "exercises": [{"name": "Deadlift", "sets": 4, "reps": "5-6"}, {"name": "Pull-Ups", "sets": 3, "reps": "8-10"}, {"name": "Barbell Row", "sets": 3, "reps": "8-10"}, {"name": "Face Pulls", "sets": 3, "reps": "15"}, {"name": "Bicep Curls", "sets": 3, "reps": "12"}]},
    "thursday": {"focus": "Rest", "exercises": []},
    "friday": {"focus": "Legs", "exercises": [{"name": "Squat", "sets": 4, "reps": "8-10"}, {"name": "Romanian Deadlift", "sets": 3, "reps": "10-12"}, {"name": "Leg Press", "sets": 3, "reps": "12-15"}, {"name": "Walking Lunges", "sets": 3, "reps": "12 each"}, {"name": "Calf Raises", "sets": 4, "reps": "15"}]},
    "saturday": {"focus": "Rest or Active Recovery", "exercises": []},
    "sunday": {"focus": "Rest", "exercises": []}
  },
  "meal_plan": {
    "monday": {
      "breakfast": "Oatmeal with berries and protein shake (500 cal, 40g protein)",
      "lunch": "Grilled chicken breast with brown rice and vegetables (600 cal, 50g protein)",
      "dinner": "Salmon with sweet potato and broccoli (550 cal, 45g protein)",
      "snacks": "Greek yogurt + almonds (300 cal, 20g protein)"
    }
  }
}

Adapt the plan to the user's specific goals, fitness level, and preferences.
If updating an existing plan, preserve what's working and only change what the user asks.
"""


def run(state: AgentState) -> AgentState:
    last_message = state["messages"][-1].content if state["messages"] else ""
    existing_plan = state.get("current_plan", {})
    existing_goal = state.get("goal", {})

    context = f"User's current goal: {json.dumps(existing_goal)}\n" if existing_goal else ""
    context += f"Existing plan: {json.dumps(existing_plan)}\n" if existing_plan else ""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"{context}\nUser message: {last_message}"}],
    )

    raw = response.content[0].text.strip()
    try:
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {**state, "response": raw}

    updated_state = {**state}
    if "goal" in parsed:
        updated_state["goal"] = parsed["goal"]
    if "workout_plan" in parsed or "meal_plan" in parsed:
        updated_state["current_plan"] = {
            "workout_plan": parsed.get("workout_plan", existing_plan.get("workout_plan", {})),
            "meal_plan": parsed.get("meal_plan", existing_plan.get("meal_plan", {})),
        }
    updated_state["response"] = parsed.get("response", "Your plan has been updated!")

    return updated_state
