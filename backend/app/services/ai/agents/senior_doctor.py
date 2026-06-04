import asyncio
import logging
import os
import sys

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_mcp_adapters.client import MultiServerMCPClient

from app.core.config import settings
from app.services.ai.llm import get_llm
from app.services.ai.state import AgentState

logger = logging.getLogger("app.ai.senior_doctor")


def senior_doctor_node(state: AgentState):
    llm = get_llm()

    # 1. Load Standard Tools (Resiliently)
    tools = []
    tavily_key = (settings.TAVILY_API_KEY or "").strip()
    # Treat empty OR the .env placeholder ("your_tavily_api_key...") as "not set".
    if tavily_key and not tavily_key.lower().startswith("your_"):
        try:
            # Pass the key explicitly: it's loaded via pydantic from .env and may
            # not be present in os.environ where langchain's tool looks for it.
            tools.append(TavilySearchResults(max_results=3, tavily_api_key=tavily_key))
        except Exception as exc:
            logger.warning("Tavily web-search tool unavailable; continuing without it: %s", exc)
    else:
        logger.info("TAVILY_API_KEY missing/placeholder; skipping web search tool.")

    # 2. Load MCP Tools (Model Context Protocol) from our local Medical MCP server.
    #    Skipped in production: the subprocess stdio transport is too slow for
    #    resource-constrained hosting (Render free tier's 30s request timeout).
    if not settings.is_production:
        mcp_server_path = os.path.join(os.path.dirname(__file__), "..", "mcp_server.py")
        try:
            child_env = {
                "PATH": os.environ.get("PATH", ""),
                "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
                "GROQ_API_KEY": settings.GROQ_API_KEY,
                "TAVILY_API_KEY": settings.TAVILY_API_KEY,
            }
            mcp_client = MultiServerMCPClient(
                {
                    "medical": {
                        "transport": "stdio",
                        "command": sys.executable,
                        "args": [mcp_server_path],
                        "env": child_env,
                    }
                }
            )
            mcp_tools = asyncio.run(mcp_client.get_tools())
            tools.extend(mcp_tools)
        except Exception as e:
            logger.warning("Failed to load MCP tools (continuing without them): %s", e)
    else:
        logger.info("Skipping MCP tools in production (subprocess too slow for hosting timeout)")
    
    # Bind all tools (Standard + MCP) to LLM
    llm_with_tools = llm.bind_tools(tools)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Senior Doctor AI with advanced diagnostic capabilities.
        
        You have access to:
        1. **Real-time Search**: For the latest medical literature and finding top hospitals/specialists for specific conditions.
        2. **MCP Medical Tools**: Specialized calculators and interaction checkers (Model Context Protocol).
        
        Rules:
        - Act as a knowledgeable senior medical educator. Provide clear, comprehensive, evidence-based information — but frame it as educational information, NOT a definitive diagnosis.
        - Use `check_drug_interaction` if the user mentions multiple medications.
        - Use `calculate_cardiac_risk` for heart-related concerns if metrics are available.
        - If the user asks for top hospitals or specialists for a health condition, use the search tool to suggest reputable options.
        - Explain what lab values or symptoms may indicate and their general significance, but always recommend that a qualified clinician confirm any diagnosis.
        - For urgent or severe findings (e.g. very high bilirubin), clearly advise the user to seek prompt in-person medical care or emergency services.
        - Never claim to replace a doctor. A standardized safety disclaimer is appended automatically. """),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    try:
        chain = prompt | llm_with_tools
        response = chain.invoke({"messages": state["messages"]})
        content = response.content
    except Exception as exc:
        # Never let a tool/binding hiccup take down the whole consultation —
        # fall back to a plain (tool-less) answer.
        logger.warning("senior_doctor tool path failed (%s); retrying without tools", exc)
        response = (prompt | llm).invoke({"messages": state["messages"]})
        content = response.content

    return {"final_response": content}
