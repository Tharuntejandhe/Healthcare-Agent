import base64
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def test_vision():
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    # Use a dummy small image or just check model availability
    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Can you see this?"},
                    ]
                }
            ],
        )
        print("Model Llama 3.2 Vision is available!")
        print(completion.choices[0].message.content)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_vision()
