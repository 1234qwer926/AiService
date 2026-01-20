from agents.base import StageResult

QUESTIONS = [
    "What is IL-6?",
    "What is the relationship between IL-6 and pain?",
    "Name two other inflammatory mediators besides IL-6."
]

class KnowledgeAgent:
    def __init__(self):
        self.index = 0

    async def handle(self, session, user_text):
        if self.index < len(QUESTIONS):
            q = QUESTIONS[self.index]
            self.index += 1
            return StageResult(reply=q, completed=False)

        return StageResult(
            reply="Thank you. Your assessment is complete. Your trainer will receive your performance summary.",
            completed=True,
        )
