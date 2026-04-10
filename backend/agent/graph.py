from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes import router, planning, progress, search
from agent.nodes import logging_node


graph = StateGraph(AgentState)

graph.add_node("router", router.run)
graph.add_node("planning", planning.run)
graph.add_node("logging", logging_node.run)
graph.add_node("progress", progress.run)
graph.add_node("search", search.run)

graph.set_entry_point("router")

graph.add_conditional_edges(
    "router",
    lambda s: s["next_node"],
    {
        "planning": "planning",
        "logging": "logging",
        "progress": "progress",
        "search": "search",
    },
)

graph.add_edge("planning", END)
graph.add_edge("logging", END)
graph.add_edge("progress", END)
graph.add_edge("search", END)

app = graph.compile()
