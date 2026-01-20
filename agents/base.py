from pydantic import BaseModel

class StageResult(BaseModel):
    reply: str
    completed: bool
    state_delta: dict = {}
