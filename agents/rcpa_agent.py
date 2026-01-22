# agents/rcpa_agent.py

import os
from google import genai
from agents.base import StageResult

PROMPT = """
You are Agent Monica acting as a RETAIL CHEMIST.

Rules you MUST follow:
- Answer only what the Business Manager asks.
- Do NOT explain products.
- Do NOT pitch.
- Do NOT coach.
- Do NOT guide the user.
- Keep replies short, practical, and realistic.

You are in an RCPA call.

If the user says anything like:
"thank you", "that's it", "done", "no more", "that’s all I needed"

Then you must:
- Give a brief closing line as a chemist
- End your role immediately
"""

class RCPAAgent:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = "gemini-2.0-flash-exp"

    async def handle(self, session, user_text: str) -> StageResult:
        user_lower = user_text.lower()

        # Hard stop detection
        done_triggers = [
            "thank you",
            "thanks",
            "that's it",
            "that’s it",
            "done",
            "no more",
            "that's all",
            "that’s all",
            "all i needed",
        ]

        is_done = any(t in user_lower for t in done_triggers)

        if is_done:
            # Chemist-style close, no coaching, no transition language
            return StageResult(
                reply="You're welcome. Have a good day.",
                completed=True,
            )

        prompt = f"""{PROMPT}

User: {user_text}
Chemist:"""

        resp = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )

        reply = (resp.text or "").strip()

        # Safety fallback – never allow empty output
        if not reply:
            reply = "I'm not sure about that. Anything else you need?"

        return StageResult(
            reply=reply,
            completed=False,
        )
