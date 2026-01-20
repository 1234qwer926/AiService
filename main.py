# main.py
import os
from fastapi import FastAPI, Depends, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import Item, MonicaSession
from database_models import (
    ItemCreate,
    ItemResponse,
    MonicaChatRequest,
    MonicaSessionResponse,
    MonicaReply,
)
from monica_service import MonicaAgent

# -------------------------------------------------
# App Setup
# -------------------------------------------------

app = FastAPI(title="Agent Monica 007")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables (safe with Postgres)
Base.metadata.create_all(bind=engine)

# Singleton Agent Brain
monica_agent = MonicaAgent()

# -------------------------------------------------
# Monica Routes
# -------------------------------------------------




@app.post("/monica/chat", response_model=MonicaReply)
async def monica_chat(
    request: MonicaChatRequest, db: Session = Depends(get_db)
):
    session = (
        db.query(MonicaSession)
        .filter(MonicaSession.id == request.session_id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        reply = await monica_agent.get_reply(db, session, request.text)
        return reply
    except Exception as e:
        import traceback
        traceback.print_exc()   # <-- ADD THIS
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/monica/session", response_model=MonicaSessionResponse)
def create_monica_session(db: Session = Depends(get_db)):
    session = MonicaSession()
    db.add(session)
    db.commit()
    db.refresh(session)

    # Seed first Monica message
    greeting = (
        "Welcome to the pitching module. "
        "Please tell me your name, your role (BM or PL), "
        "your headquarter base, and your division."
    )

    from models import MonicaMessage

    msg = MonicaMessage(
        session_id=session.id,
        role="assistant",
        content=greeting,
        stage="SETUP",
        persona="COACH",
    )
    db.add(msg)
    db.commit()

    return session



@app.websocket("/ws/monica/{session_id}")
async def monica_ws(websocket: WebSocket, session_id: int):
    """
    Dedicated WebSocket for Voice Mode.
    Each socket gets its own DB session.
    """
    db_gen = get_db()
    db = next(db_gen)

    try:
        await monica_agent.connect_live_session(websocket, db, session_id)
    except Exception as e:
        print("WS Error:", e)
        try:
            await websocket.close()
        except Exception:
            pass
    finally:
        try:
            db.close()
        except Exception:
            pass


# -------------------------------------------------
# Sample DB Routes (Keep or Remove)
# -------------------------------------------------

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
