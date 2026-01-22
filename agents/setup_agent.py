# agents/setup_agent.py

import os
from google import genai
from agents.base import StageResult

PROMPT = """
You are Agent Monica (Coach).

Your task:
- Collect the user's:
  1. Name
  2. Role (BM or PL)
  3. HQ
  4. Division

Rules:
- Ask only for missing fields.
- Once all four are known, summarize them clearly.
- Ask for confirmation in one line.
- Do NOT move forward until the user confirms (yes/yeah/correct).

Be concise and conversational.
"""

class SetupAgent:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = "gemini-2.0-flash-exp"

    async def handle(self, session, user_text: str) -> StageResult:
        # If user confirms, we finish setup
        u = user_text.lower()
        if any(x in u for x in ["yes", "yeah", "correct", "that's right"]):
            return StageResult(
                reply="Perfect. Your session is now set up. Let’s begin.",
                completed=True,
            )

        prompt = f"""{PROMPT}

Known so far:
- Name: {session.user_name or "unknown"}
- Role: {session.user_role or "unknown"}
- HQ: {session.headquarter or "unknown"}
- Division: {session.division or "unknown"}

User said: {user_text}

Respond as Monica.
"""

        resp = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )

        reply = (resp.text or "").strip()
        if not reply:
            reply = "Could you please share your name, role, HQ, and division?"

        return StageResult(
            reply=reply,
            completed=False,
        )
