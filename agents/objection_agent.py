# agents/objection_agent.py

import os
from google import genai
from agents.base import StageResult

PROMPT = """
You are Agent Monica acting as a practicing DOCTOR.

Your behavior:
- Raise a realistic objection based on common clinical thinking.
- Do NOT use placeholders like "Competitor X".
- Sound like a real doctor in India.
- Keep it natural and brief.

After the BM responds:
- Evaluate their answer in 2–3 lines.
- Point out one strength and one improvement area.
- Close this stage.
"""

class ObjectionAgent:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = "gemini-2.0-flash-exp"
        self.raised = False

    async def handle(self, session, user_text: str) -> StageResult:
        # First turn: raise a natural objection
        if not self.raised:
            self.raised = True

            prompt = """
You are a doctor seeing a medical representative for Vitamin D products.
Raise ONE realistic objection about switching from your current practice.
Do not mention brand placeholders.
Be concise and natural.
"""

            resp = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )

            objection = (resp.text or "").strip()
            if not objection:
                objection = "My current Vitamin D brand works well and is affordable. Why should I change it?"

            return StageResult(
                reply=objection,
                completed=False,
            )

        # Second turn: evaluate BM's handling
        prompt = f"""{PROMPT}

BM's response:
{user_text}

Now evaluate briefly and close.
"""

        resp = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )

        reply = (resp.text or "").strip()
        if not reply:
            reply = "You handled the objection well, but you could be more specific about patient outcomes."

        return StageResult(
            reply=reply,
            completed=True,
        )
