# models.py
from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import datetime
from database import Base

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)

class MonicaSession(Base):
    __tablename__ = "monica_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String, index=True, nullable=True)
    user_role = Column(String, nullable=True)
    headquarter = Column(String, nullable=True)
    division = Column(String, nullable=True)
    current_stage = Column(String, default="SETUP")
    current_persona = Column(String, default="COACH")
    state_delta = Column(JSON, default={})
    metrics = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    messages = relationship("MonicaMessage", back_populates="session")

class MonicaMessage(Base):
    __tablename__ = "monica_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("monica_sessions.id"))
    role = Column(String)  # 'user' or 'assistant'
    content = Column(String)
    stage = Column(String)
    persona = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    session = relationship("MonicaSession", back_populates="messages")
