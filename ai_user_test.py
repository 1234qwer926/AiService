#!/usr/bin/env python3
import os
import time
import requests
from google import genai
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = "http://localhost:8000"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class BMUserAgent:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.persona = """
You are **Pavan**, a professional Business Manager (BM) from HQ India, Stimulus division.
You are participating in a sales coaching session with **Agent Monica 007**.
Your goal is to practice pitching **Dexel & Dexel ND** products.

BEHAVIOR RULES:
1. Act like a real human BM. Be professional but natural.
2. Follow Monica's instructions.
3. In RCPA stage, ask questions a sales person would ask a chemist (e.g., about prescribing habits, competitors).
4. In DOCTOR stage, try to understand the doctor's needs and then pitch Dexel.
5. In OBJECTION stage, try to handle the doctor's concerns professionally.
6. In KNOWLEDGE stage, answer the scientific questions to the best of your ability.
7. Keep your responses concise (1-3 sentences mostly).
8. When you feel a stage is complete (e.g., Monica gives feedback or says "good job"), acknowledge and move on.
9. To end the RCPA or DOCTOR conversation, say something like "Thank you, that's all for now" or "Thank you for your time, doctor."
"""

    def generate_response(self, monica_reply: str, current_stage: str) -> str:
        prompt = f"""
{self.persona}

CURRENT STAGE: {current_stage}
MONICA'S LAST MESSAGE: "{monica_reply}"

Based on the stage and Monica's message, what is your next response as Pavan?
Respond ONLY with the text of your message.
"""
        response = self.client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt
        )
        return response.text.strip()

def run_ai_test():
    print("=" * 80)
    print("        AGENT MONICA 007 - AI-DRIVEN INTERACTIVE TESTING        ")
    print("=" * 80)

    user_agent = BMUserAgent()
    
    # Create Session
    resp = requests.post(f"{BASE_URL}/monica/session")
    session = resp.json()
    session_id = session["id"]
    current_stage = session["current_stage"]
    
    # Initial Monica Message
    monica_reply = "Welcome to the pitching module. Please tell me your name, your role (BM or PL), your headquarter base, and your division."
    print(f"\n🤖 MONICA (SETUP): {monica_reply}")

    max_turns = 30
    turn = 0
    
    while turn < max_turns:
        turn += 1
        
        # 1. User Agent generates response
        user_text = user_agent.generate_response(monica_reply, current_stage)
        print(f"\n👤 PAVAN (BM): {user_text}")
        
        # Rate limit cooldown for Gemini
        time.sleep(6)
        
        # 2. Submit to Monica
        try:
            resp = requests.post(
                f"{BASE_URL}/monica/chat",
                json={"session_id": session_id, "text": user_text}
            )
            resp.raise_for_status()
            data = resp.json()
            
            monica_reply = data["reply"]
            new_stage = data.get("current_stage", current_stage) # We might need to fetch session again to be sure of stage
            
            # Fetch latest session state to track stage properly
            s_resp = requests.get(f"{BASE_URL}/monica/session/{session_id}")
            if s_resp.status_code == 200:
                stage_info = s_resp.json()
                current_stage = stage_info["current_stage"]
            
            print(f"\n🤖 MONICA ({current_stage}): {monica_reply}")
            
            if current_stage == "END":
                print("\n✅ Session completed successfully!")
                break
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
            break

    print("\n" + "=" * 80)
    print("                             TEST OVER                             ")
    print("=" * 80)

if __name__ == "__main__":
    run_ai_test()
