import os
import asyncio
from dotenv import load_dotenv
from monica_service import MonicaAgent

load_dotenv()

async def verify():
    print("Initializing MonicaAgent...")
    try:
        agent = MonicaAgent()
        print(f"Agent initialized with text model: {agent.model_text}")
        
        print("Testing text generation...")
        response = agent.text_client.models.generate_content(
            model=agent.model_text,
            contents="Say 'Hello, World!' if you can hear me."
        )
        print(f"Response received: {response.text}")
        print("VERIFICATION SUCCESSFUL")
    except Exception as e:
        print(f"VERIFICATION FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
