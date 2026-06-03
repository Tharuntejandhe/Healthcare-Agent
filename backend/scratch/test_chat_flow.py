import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

# Add backend to sys.path
backend_path = Path(__file__).parent.parent
sys.path.append(str(backend_path))

from app.services.ai.graph import ai_app

def test_chat_flow():
    # Load .env
    load_dotenv(backend_path / ".env")
    
    query = "hi tell me the healthy food"
    print(f"Testing Prompt: '{query}'")
    
    try:
        initial_state = {
            "messages": [HumanMessage(content=query)],
            "classification": "",
            "next_agent": "",
            "final_response": ""
        }
        
        print("Invoking AI Graph...")
        result = ai_app.invoke(initial_state)
        
        print("\n--- AI Response ---")
        print(f"Classification: {result.get('classification')}")
        print(f"Response: {result.get('final_response')}")
        
    except Exception as e:
        print(f"\n❌ Error during AI flow:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chat_flow()
