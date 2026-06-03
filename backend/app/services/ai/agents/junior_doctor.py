from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.services.ai.llm import get_llm
from app.services.ai.state import AgentState
from app.services.ai.rag import retrieve_context

def junior_doctor_node(state: AgentState):
    llm = get_llm()
    
    # Get the latest user query for RAG retrieval
    user_query = state["messages"][-1].content
    context = retrieve_context(user_query, user_id=state["user_id"])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are a Junior Doctor AI for the MediHealth platform. 
        Your role is to evaluate patient symptoms, analyze medical data, and provide preliminary clinical insights.
        
        INSTRUCTIONS:
        1. Act as a helpful medical educator. Provide a clear, step-by-step explanation of what the user's symptoms or lab results may indicate — framed as educational information, not a diagnosis.
        2. Explain what the values mean in plain language and their general significance.
        3. Provide the full educational analysis first; for anything severe or urgent, clearly recommend seeing a qualified clinician (or emergency services for red-flag symptoms).
        4. Never claim to replace a doctor or give a definitive diagnosis. A standardized safety disclaimer is appended automatically.

        Relevant context from patient reports:
        {context}"""),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    chain = prompt | llm
    response = chain.invoke({"messages": state["messages"]})
    
    return {"final_response": response.content}
