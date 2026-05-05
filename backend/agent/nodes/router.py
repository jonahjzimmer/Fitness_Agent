import os
from anthropic import Anthropic
from agent.state import AgentState

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are a routing assistant for a fitness coaching app.
Your only job is to classify the user's message into exactly one of these categories:

- planning: User wants to set/update goals, create a workout or meal plan, or modify their existing plan
- logging: User is logging a meal they ate, a workout they completed, or their weight
- progress: User is asking about their progress, stats, goal tracking, or wants a summary
- search: User is asking for information about specific exercises, nutrition facts, or fitness concepts

Respond with ONLY the category name — no explanation, no punctuation, nothing else.
Examples:
"I want to lose 10 lbs" → planning
"I had oatmeal for breakfast" → logging
"How am I doing this week?" → progress
"What muscles does a Romanian deadlift work?" → search
"""


def run(state: AgentState) -> AgentState:
    # Short-circuit: new users in onboarding always go to planning
    is_onboarding = not state.get("current_plan") and not state.get("goal", {}).get("onboarding_complete")
    if is_onboarding:
        return {**state, "next_node": "planning"}

    last_message = state["messages"][-1].content if state["messages"] else ""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=10,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": last_message}],
    )

    intent = response.content[0].text.strip().lower()
    if intent not in ("planning", "logging", "progress", "search"):
        intent = "planning"  # safe default

    return {**state, "next_node": intent}
