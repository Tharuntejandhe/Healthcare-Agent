from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.services.ai.llm import get_llm
from app.services.ai.state import AgentState

def general_support_node(state: AgentState):
    llm = get_llm()
    
    # Use ChatPromptTemplate to include conversation history
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful general support assistant for a healthcare app. You can handle greetings, personal questions, and general app support."),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    chain = prompt | llm
    
    # We pass the entire list of messages to the LLM
    response = chain.invoke({"messages": state["messages"]})
    
    return {"final_response": response.content}
