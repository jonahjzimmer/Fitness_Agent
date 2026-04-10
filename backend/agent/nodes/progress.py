import os
import json
from anthropic import Anthropic
from agent.state import AgentState

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are a fitness progress analyst. Given the user's goal, current plan, today's log,
and weekly summary, provide an honest and motivating progress assessment.

Be specific with numbers. Highlight wins, flag areas that need attention, and give one actionable tip.
Keep the response conversational and under 200 words.
"""


def run(state: AgentState) -> AgentState:
    last_message = state["messages"][-1].content if state["messages"] else ""
    goal = state.get("goal", {})
    daily_log = state.get("daily_log", [])
    weekly_summary = state.get("weekly_summary", {})
    current_plan = state.get("current_plan", {})

    # Compute today's totals
    meals_today = [e for e in daily_log if e.get("log_type") == "meal"]
    workouts_today = [e for e in daily_log if e.get("log_type") == "workout"]
    calories_today = sum(e.get("entry", {}).get("estimated_calories", 0) for e in meals_today)
    protein_today = sum(e.get("entry", {}).get("estimated_protein_g", 0) for e in meals_today)

    context = f"""Goal: {json.dumps(goal)}
Today's nutrition: {calories_today} calories, {protein_today}g protein
Meals logged today: {len(meals_today)}
Workouts logged today: {len(workouts_today)}
Weekly summary: {json.dumps(weekly_summary)}
User's question: {last_message}
"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=400,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": context}],
    )

    answer = response.content[0].text.strip()

    # Update weekly summary with fresh computed totals
    updated_summary = {
        **weekly_summary,
        "today_calories": calories_today,
        "today_protein_g": protein_today,
        "today_meals_logged": len(meals_today),
        "today_workouts_logged": len(workouts_today),
    }

    return {**state, "response": answer, "weekly_summary": updated_summary}
