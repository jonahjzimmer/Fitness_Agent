from typing import TypedDict, Optional
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    messages: list[BaseMessage]
    user_id: str
    current_plan: dict          # weekly workout + meal plan
    goal: dict                  # target weight, timeline, activity level
    daily_log: list             # today's meals and workouts
    weekly_summary: dict        # aggregated weekly progress
    workout_history: list        # past 30 days of daily logs [{date, workouts, calories, macros}]
    next_node: str              # routing decision
    response: Optional[str]     # final response to return to user
