from google import genai
from agents.base import StageResult
import os

PROMPT = """
You are Agent Monica acting as a DOCTOR.

Flow:
1. Answer probing questions.
2. Listen to the pitch.
3. Challenge it with 2–3 clinical points.
4. Provide brief feedback.

Rules:
- Be realistic and concise.
- Do NOT restart the pitch.
- Sound like a practicing doctor in India.
"""

class DoctorAgent:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = "gemini-2.0-flash-exp"

    async def handle(self, session, user_text):
        prompt = PROMPT + f"\nUser: {user_text}"
        resp = self.client.models.generate_content(model=self.model, contents=prompt)
        reply = (resp.text or "").strip()

        u = user_text.lower()
        close_signals = [
            "thank you doctor",
            "that covers",
            "i believe i've addressed",
            "that's all",
            "i think i've covered",
        ]

        feedback_markers = [
            "you could improve",
            "you did well",
            "next time",
            "overall",
            "good job",
        ]

        done = any(sig in u for sig in close_signals) or any(
            m in reply.lower() for m in feedback_markers
        )

        return StageResult(reply=reply, completed=done)
