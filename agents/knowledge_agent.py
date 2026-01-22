from agents.base import StageResult

QUESTIONS = [
    "What is IL-6?",
    "What is the relationship between IL-6 and pain?",
    "Name two other inflammatory mediators besides IL-6."
]

class KnowledgeAgent:
    def __init__(self):
        self.index = 0
        self.waiting_for_answer = False

    async def handle(self, session, user_text):
        # If we were waiting for an answer, consume it and move forward
        if self.waiting_for_answer:
            self.waiting_for_answer = False

        # Ask next question
        if self.index < len(QUESTIONS):
            q = QUESTIONS[self.index]
            self.index += 1
            self.waiting_for_answer = True
            return StageResult(reply=q, completed=False)

        # All questions done
        return StageResult(
            reply="Thank you. Your assessment is complete. Your trainer will receive your performance summary.",
            completed=True,
        )
