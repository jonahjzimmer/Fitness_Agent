import os
import json
from anthropic import Anthropic
from agent.state import AgentState
from agent.tools import lookup_nutrition, search_exercise_info

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

TOOLS = [
    {
        "name": "lookup_nutrition",
        "description": "Look up nutritional info for a food item (calories, protein, carbs, fat per 100g).",
        "input_schema": {
            "type": "object",
            "properties": {"food_name": {"type": "string", "description": "Name of the food to look up"}},
            "required": ["food_name"],
        },
    },
    {
        "name": "search_exercise_info",
        "description": "Get information about exercises, muscle groups targeted, or find exercise alternatives.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Exercise or fitness question"}},
            "required": ["query"],
        },
    },
]

TOOL_FN_MAP = {
    "lookup_nutrition": lambda inp: lookup_nutrition.invoke(inp),
    "search_exercise_info": lambda inp: search_exercise_info.invoke(inp),
}

SYSTEM_PROMPT = """You are a knowledgeable fitness and nutrition assistant.
Answer the user's question using the available tools when helpful.
Be concise, accurate, and practical. Under 150 words.
"""


def run(state: AgentState) -> AgentState:
    last_message = state["messages"][-1].content if state["messages"] else ""

    messages = [{"role": "user", "content": last_message}]

    # Agentic tool-use loop (max 3 turns)
    for _ in range(3):
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=600,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            answer = next(
                (b.text for b in response.content if hasattr(b, "text")), ""
            )
            return {**state, "response": answer}

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    fn = TOOL_FN_MAP.get(block.name)
                    result = fn(block.input) if fn else {"error": "unknown tool"}
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

    # Fallback if loop exhausted
    return {**state, "response": "I found some information but couldn't compile a full answer. Please try rephrasing."}
