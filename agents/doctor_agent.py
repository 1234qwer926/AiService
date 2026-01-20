from google import genai
from agents.base import StageResult
import os

PROMPT = """
You are Agent Monica acting as a DOCTOR.

Flow:
1. Answer probing questions.
2. Listen to the pitch.
3. Challenge it with 2–3 clinical points.
4. When the user closes (e.g., "Thank you Doctor", "That covers my approach"),
   stop and let the system advance.

Do NOT restart the pitch.
"""

class DoctorAgent:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = "gemini-2.0-flash-exp"

    async def handle(self, session, user_text):
        prompt = PROMPT + f"\nUser: {user_text}"
        resp = self.client.models.generate_content(model=self.model, contents=prompt)
        reply = resp.text or ""

        u = user_text.lower()
        close_signals = [
            "thank you doctor",
            "that covers",
            "i believe i've addressed",
            "that's all",
            "i think i've covered",
        ]

        done = any(sig in u for sig in close_signals)

        return StageResult(reply=reply, completed=done)
