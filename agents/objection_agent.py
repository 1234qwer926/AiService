from google import genai
from agents.base import StageResult
import os

PROMPT = """
You are Agent Monica as a DOCTOR.

Raise this objection:

"Competitor X is effective and my patients are familiar with it.
Why should I switch?"

After the BM responds once, evaluate briefly and close.
"""

class ObjectionAgent:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = "gemini-2.0-flash-exp"
        self.raised = False

    async def handle(self, session, user_text):
        if not self.raised:
            self.raised = True
            return StageResult(
                reply="Competitor X is effective and my patients are familiar with it. Why should I switch?",
                completed=False,
            )

        prompt = PROMPT + f"\nUser Response: {user_text}"
        resp = self.client.models.generate_content(model=self.model, contents=prompt)
        reply = resp.text or ""

        return StageResult(reply=reply, completed=True)
