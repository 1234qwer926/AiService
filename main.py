from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from openai import OpenAI
from google import genai
import httpx
import os

from database import Base, engine, get_db
from models import Item, MonicaSession, MonicaMessage
from database_models import (
    ItemCreate, ItemResponse, AIRequest, AIResponse,
    MonicaChatRequest, MonicaSessionResponse, MonicaReply
)
from monica_service import MonicaAgent

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Monica Agent
monica_agent = MonicaAgent()

# Create database tables
Base.metadata.create_all(bind=engine)

# AI Service Clients Initialization
def get_openai_client():
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_gemini_client():
    return genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# -------- Monica Agent Routes --------
@app.post("/monica/session", response_model=MonicaSessionResponse)
def create_monica_session(db: Session = Depends(get_db)):
    session = MonicaSession()
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@app.post("/monica/chat", response_model=MonicaReply)
async def monica_chat(request: MonicaChatRequest, db: Session = Depends(get_db)):
    session = db.query(MonicaSession).filter(MonicaSession.id == request.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        reply = await monica_agent.get_reply(db, session, request.text)
        return reply
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/monica/session/{session_id}", response_model=MonicaSessionResponse)
def get_monica_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(MonicaSession).filter(MonicaSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

# -------- Database Routes --------
@app.post("/items", response_model=ItemResponse)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    db_item = Item(name=item.name, description=item.description)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.get("/items", response_model=list[ItemResponse])
def get_items(db: Session = Depends(get_db)):
    return db.query(Item).all()

# -------- OpenAI Route --------
@app.post("/ai/openai", response_model=AIResponse)
async def ask_openai(request: AIRequest):
    client = get_openai_client()
    model = request.model or "gpt-4o-mini"
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": request.text}]
        )
        return {
            "service": "OpenAI",
            "response": response.choices[0].message.content,
            "model_used": model
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------- Gemini Route --------
@app.post("/ai/gemini", response_model=AIResponse)
async def ask_gemini(request: AIRequest):
    client = get_gemini_client()
    model = request.model or "gemini-1.5-flash"
    try:
        response = await client.aio.models.generate_content(
            model=model,
            contents=request.text
        )
        return {
            "service": "Gemini",
            "response": response.text,
            "model_used": model
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------- Perplexity Route --------
@app.post("/ai/perplexity", response_model=AIResponse)
async def ask_perplexity(request: AIRequest):
    api_key = os.getenv("PERPLEXITY_API_KEY")
    model = request.model or "llama-3.1-sonar-small-128k-online"
    url = "https://api.perplexity.ai/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": request.text}]
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return {
                "service": "Perplexity",
                "response": data["choices"][0]["message"]["content"],
                "model_used": model
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
