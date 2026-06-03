import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_groq import ChatGroq

def test_groq():
    # Load .env from backend
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ Error: GROQ_API_KEY not found in .env")
        return

    print(f"Testing Groq API with key: {api_key[:10]}...")
    
    try:
        llm = ChatGroq(
            groq_api_key=api_key,
            model_name="llama-3.3-70b-versatile", # Using the versatile 70b model
            temperature=0.0
        )
        response = llm.invoke("Say hello!")
        print(f"✅ Success! Groq responded: {response.content}")
    except Exception as e:
        print(f"❌ Groq API failed: {e}")

if __name__ == "__main__":
    test_groq()
