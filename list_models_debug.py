import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

try:
    print("Listing models...")
    # List a few models to see what's available
    for m in client.models.list(config={"page_size": 20}):
        print(f"Name: {m.name}")
        # print(f"Attributes: {dir(m)}") # excessive output, simplified below
    
    print("\nTrying to get specific models:")
    candidates = [
        "gemini-1.5-flash",
        "gemini-1.5-flash-001",
        "gemini-1.5-flash-latest",
        "gemini-1.5-pro",
        "gemini-2.0-flash-exp"
    ]
    
    for name in candidates:
        try:
            m = client.models.get(model=name)
            print(f"[FOUND] {name} -> {m.name}")
        except Exception as e:
            print(f"[MISSING] {name}: {e}")

except Exception as e:
    print(f"Global Error: {e}")
