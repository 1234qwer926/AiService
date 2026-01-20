from google import genai
from agents.base import StageResult
import os

PROMPT = """
You are Agent Monica acting as a RETAIL CHEMIST.

Rules:
- Answer only what the Business Manager asks.
- Do not coach.
- Do not ask unnecessary questions.
- Be brief and realistic.

End the interaction when the user says things like:
"thank you", "that's it", "done", "no more questions".
"""

class RCPAgent:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = "gemini-2.0-flash-exp"

    async def handle(self, session, user_text):
        prompt = PROMPT + f"\nUser: {user_text}"
        resp = self.client.models.generate_content(model=self.model, contents=prompt)
        reply = resp.text or ""

        u = user_text.lower()
        done = any(x in u for x in ["thank", "that's it", "done", "no more"])

        return StageResult(reply=reply, completed=done)
