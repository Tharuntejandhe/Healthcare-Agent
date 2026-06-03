from langgraph.graph import StateGraph, END
from app.services.ai.state import AgentState
from app.services.ai.agents.support_agent import support_agent_node
from app.services.ai.agents.junior_doctor import junior_doctor_node
from app.services.ai.agents.senior_doctor import senior_doctor_node
from app.services.ai.agents.nutrition_agent import nutrition_agent_node
from app.services.ai.agents.general_support import general_support_node

def route_query(state: AgentState):
    """
    Routing function that determines which node to call next based on 
    the classification from the support agent.
    """
    route = state.get("next_agent", "general")
    return route

# Define a new graph
workflow = StateGraph(AgentState)

# Define the nodes
workflow.add_node("support_agent", support_agent_node)
workflow.add_node("junior_doctor", junior_doctor_node)
workflow.add_node("senior_doctor", senior_doctor_node)
workflow.add_node("nutrition", nutrition_agent_node)
workflow.add_node("general", general_support_node)

# Set the entry point
workflow.set_entry_point("support_agent")

# Add conditional edges from the support agent to the specialized agents
workflow.add_conditional_edges(
    "support_agent",
    route_query,
    {
        "junior_doctor": "junior_doctor",
        "senior_doctor": "senior_doctor",
        "nutrition": "nutrition",
        "general": "general"
    }
)

# Add edges from specialized agents to END
workflow.add_edge("junior_doctor", END)
workflow.add_edge("senior_doctor", END)
workflow.add_edge("nutrition", END)
workflow.add_edge("general", END)

from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

# Initialize memory checkpointer
# In this version of langgraph, JsonPlusSerializer does not take allowed_objects in __init__
memory = MemorySaver(serde=JsonPlusSerializer())

# Compile the graph with memory
ai_app = workflow.compile(checkpointer=memory)
