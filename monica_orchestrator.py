from agents.setup_agent import SetupAgent
from agents.rcpa_agent import RCPAgent
from agents.intelligence_agent import IntelligenceAgent
from agents.doctor_agent import DoctorAgent
from agents.objection_agent import ObjectionAgent
from agents.knowledge_agent import KnowledgeAgent

STAGE_ORDER = ["SETUP", "RCPA", "INTELLIGENCE", "DOCTOR", "OBJECTION", "KNOWLEDGE", "END"]

class MonicaOrchestrator:
    def __init__(self):
        self.agents = {
            "SETUP": SetupAgent(),
            "RCPA": RCPAgent(),
            "INTELLIGENCE": IntelligenceAgent(),
            "DOCTOR": DoctorAgent(),
            "OBJECTION": ObjectionAgent(),
            "KNOWLEDGE": KnowledgeAgent(),
        }

    def next_stage(self, current):
        idx = STAGE_ORDER.index(current)
        return STAGE_ORDER[min(idx + 1, len(STAGE_ORDER) - 1)]

    async def handle(self, session, user_text):
        agent = self.agents[session.current_stage]
        result = await agent.handle(session, user_text)

        if result.completed:
            session.current_stage = self.next_stage(session.current_stage)

        return result
