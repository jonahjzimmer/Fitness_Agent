import os
import json
from anthropic import Anthropic
from agent.state import AgentState

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

ONBOARDING_SYSTEM_PROMPT = """You are a friendly fitness coach onboarding a new user.
Your job is to collect the information needed to build a great personalized plan.

You will receive a JSON object with two keys:
- "user_message": what the user just said
- "already_known": fields you have already collected in prior turns (null means not yet known)

Your task:
1. Extract any new information from "user_message" and add it to the "collected" fields.
2. Determine which critical fields are still missing.
3. If any critical field is missing, ask exactly ONE focused, friendly follow-up question — the most important missing piece. Never ask two questions at once.
4. If all four critical fields are present, set "ready_to_plan" to true and do NOT ask any questions.

Critical fields (all four must be present before you are ready):
- fitness_goal: e.g. "lose weight", "build muscle", "improve general fitness", "train for a sport"
- experience_level: exactly one of "beginner", "intermediate", or "advanced"
- workouts_per_week: an integer between 1 and 7
- equipment: exactly one of "full gym", "home gym with weights", "bodyweight only", or "minimal equipment"

Optional fields (collect if the user mentions them, but never ask about them while critical fields are missing):
- current_weight_lbs, target_weight_lbs, injuries_or_limitations, timeline_weeks

Always respond with ONLY a JSON object in this exact format — no extra text:
{
  "collected": {
    "fitness_goal": "...",
    "experience_level": "...",
    "workouts_per_week": null,
    "equipment": "...",
    "current_weight_lbs": null,
    "target_weight_lbs": null,
    "injuries_or_limitations": null,
    "timeline_weeks": null
  },
  "ready_to_plan": false,
  "follow_up_question": "What is your main fitness goal — for example, lose weight, build muscle, or improve your general fitness?"
}

Rules:
- When ready_to_plan is true, follow_up_question must be null.
- When ready_to_plan is false, follow_up_question must be a non-null string.
- In "collected", include ALL fields — set to null if not yet known.
- Never include fields outside this schema.
"""

PLAN_GENERATION_SYSTEM_PROMPT = """You are a professional fitness and nutrition coach.
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
When making the plan or changing the plan keep workouts evenly spread across the week, unless the user has asked for a specific day plan that goes against this.
"""

CRITICAL_FIELDS = ("fitness_goal", "experience_level", "workouts_per_week", "equipment")


def _has_enough_info(goal: dict) -> bool:
    return all(goal.get(f) for f in CRITICAL_FIELDS)


def _run_onboarding(state: AgentState, last_message: str, existing_goal: dict) -> AgentState:
    known = {k: existing_goal.get(k) for k in (
        "fitness_goal", "experience_level", "workouts_per_week", "equipment",
        "current_weight_lbs", "target_weight_lbs", "injuries_or_limitations", "timeline_weeks"
    )}

    user_content = json.dumps({
        "user_message": last_message,
        "already_known": known,
    })

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=600,
        system=ONBOARDING_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )

    raw = response.content[0].text.strip()
    try:
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        # Graceful degradation — don't mutate state, ask a safe opener
        return {**state, "response": "Let's get you started! What is your main fitness goal — for example, lose weight, build muscle, or improve your general fitness?"}

    collected = parsed.get("collected", {})

    # Null-preserving merge: never overwrite a collected value with null
    updated_goal = {**existing_goal}
    for key, value in collected.items():
        if value is not None:
            updated_goal[key] = value

    ready = parsed.get("ready_to_plan", False) and _has_enough_info(updated_goal)

    if ready:
        updated_goal["onboarding_complete"] = True
        # Map onboarding keys to canonical goal schema keys
        updated_goal.setdefault("description", updated_goal.get("fitness_goal", ""))
        updated_goal.setdefault("workouts_per_week", updated_goal.get("workouts_per_week", 3))
        return _run_plan_generation(
            {**state, "goal": updated_goal},
            last_message,
            {},
            updated_goal,
        )

    follow_up = parsed.get("follow_up_question") or "Can you tell me a bit more about your fitness goals?"
    return {**state, "goal": updated_goal, "response": follow_up}


def _run_plan_generation(state: AgentState, last_message: str, existing_plan: dict, goal: dict) -> AgentState:
    context = f"User's current goal and profile: {json.dumps(goal)}\n" if goal else ""
    context += f"Existing plan: {json.dumps(existing_plan)}\n" if existing_plan else ""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=PLAN_GENERATION_SYSTEM_PROMPT,
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

    updated_state = {**state}
    if "goal" in parsed:
        # Merge generated goal fields into the existing goal (preserves onboarding fields)
        merged_goal = {**state.get("goal", {}), **parsed["goal"]}
        updated_state["goal"] = merged_goal
    if "workout_plan" in parsed or "meal_plan" in parsed:
        updated_state["current_plan"] = {
            "workout_plan": parsed.get("workout_plan", existing_plan.get("workout_plan", {})),
            "meal_plan": parsed.get("meal_plan", existing_plan.get("meal_plan", {})),
        }
    updated_state["response"] = parsed.get("response", "Your plan has been updated!")

    return updated_state


def run(state: AgentState) -> AgentState:
    last_message = state["messages"][-1].content if state["messages"] else ""
    existing_plan = state.get("current_plan", {})
    existing_goal = state.get("goal", {})

    is_onboarding = not existing_plan and not existing_goal.get("onboarding_complete")

    if is_onboarding:
        return _run_onboarding(state, last_message, existing_goal)
    else:
        return _run_plan_generation(state, last_message, existing_plan, existing_goal)
