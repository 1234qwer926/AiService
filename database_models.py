# Database Models (database_models.py )
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

# Database Schemas
class ItemCreate(BaseModel):
    name: str
    description: str

class ItemResponse(ItemCreate):
    id: int

    class Config:
        from_attributes = True

# AI Service Schemas
class AIRequest(BaseModel):
    text: str
    model: Optional[str] = None

class AIResponse(BaseModel):
    service: str
    response: str
    model_used: str

# Monica Agent Schemas
class MonicaChatRequest(BaseModel):
    session_id: int
    text: str

class MonicaMessageResponse(BaseModel):
    role: str
    content: str
    stage: str
    persona: str
    timestamp: datetime

    class Config:
        from_attributes = True

class MonicaSessionResponse(BaseModel):
    id: int
    user_name: Optional[str]
    user_role: Optional[str]
    headquarter: Optional[str]
    division: Optional[str]
    current_stage: str
    current_persona: str
    state_delta: Dict[str, Any]
    metrics: Dict[str, Any]
    messages: List[MonicaMessageResponse]

    class Config:
        from_attributes = True

class MonicaReply(BaseModel):
    reply: str
    advance_stage: bool
    state_delta: Dict[str, Any]
