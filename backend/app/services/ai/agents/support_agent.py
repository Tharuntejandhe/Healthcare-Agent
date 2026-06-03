from langchain_core.prompts import PromptTemplate
from app.services.ai.llm import get_llm
from app.services.ai.state import AgentState

# Pydantic is not strictly needed for basic JSON output from Llama3 if we prompt correctly,
# but using structured output is best. We'll use simple prompting for the router.
ROUTER_PROMPT = """You are the Support Agent for a MediHealth System.
Your job is to analyze the user's query and classify it into one of the following categories:

1. "senior_doctor": For complex cases, high-severity symptoms, highly abnormal lab results (like very high bilirubin), chronic illnesses, hospital recommendations, or cases requiring deep diagnosis. ALWAYS route abnormal lab values here.
2. "junior_doctor": ONLY for completely normal or low-severity issues (like a mild cold or general wellness check). Do NOT route severe symptoms or high lab values here.
3. "nutrition": For queries strictly related to diet, food, lifestyle, and nutrition.
4. "general": For non-medical questions, greetings, or general support queries.

User Query: {query}

Respond with exactly ONE word representing the category:
(junior_doctor, senior_doctor, nutrition, general)
"""

def support_agent_node(state: AgentState):
    llm = get_llm()
    prompt = PromptTemplate.from_template(ROUTER_PROMPT)
    
    # Get the latest user message
    user_query = state["messages"][-1].content
    
    chain = prompt | llm
    response = chain.invoke({"query": user_query})
    
    classification = response.content.strip().lower()
    
    # Handle unexpected outputs
    valid_categories = ["junior_doctor", "senior_doctor", "nutrition", "general"]
    if classification not in valid_categories:
        classification = "general"
        
    return {
        "classification": classification,
        "next_agent": classification
    }
