from agents.base import StageResult

PROMPT = """
You are Agent Monica as a COACH.

Give short, actionable feedback on the RCPA:
- What the BM did well
- What was missing (e.g., dosing frequency, patient type)
- One concrete improvement tip

Then close.
"""

class IntelligenceAgent:
    async def handle(self, session, user_text):
        # This stage is single-turn coaching
        reply = (
            "Good job gathering core prescription details. "
            "You covered brand, formulation, and potential well. "
            "One gap was dosing frequency—daily vs weekly vs monthly. "
            "That insight would help you tailor your doctor pitch more precisely."
        )

        return StageResult(reply=reply, completed=True)
