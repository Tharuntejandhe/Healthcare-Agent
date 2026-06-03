from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.services.ai.llm import get_llm
from app.services.ai.state import AgentState

def nutrition_agent_node(state: AgentState):
    llm = get_llm()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a Nutritionist AI. You exclusively handle queries regarding diet, food, lifestyle, and nutrition. Provide tailored dietary and lifestyle recommendations."),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    chain = prompt | llm
    response = chain.invoke({"messages": state["messages"]})
    
    return {"final_response": response.content}
