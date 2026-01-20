from google import genai
from agents.base import StageResult
import os

PROMPT = """
You are Agent Monica (Coach).
Collect:
- Name
- Role (BM/PL)
- HQ
- Division

Confirm once collected.
"""

class SetupAgent:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = "gemini-2.0-flash-exp"

    async def handle(self, session, user_text):
        prompt = PROMPT + f"\nUser: {user_text}"
        resp = self.client.models.generate_content(model=self.model, contents=prompt)
        reply = resp.text or ""

        # Simple completion logic
        done = all(
            k in user_text.lower()
            for k in ["bm", "hq", "division"]
        ) or "correct" in user_text.lower() or "yeah" in user_text.lower()

        return StageResult(reply=reply, completed=done)
