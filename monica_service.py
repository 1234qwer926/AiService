# monica_service.py
import os
import asyncio
from fastapi import WebSocket
from sqlalchemy.orm import Session
from google import genai

from models import MonicaSession, MonicaMessage
from database_models import MonicaReply

SYSTEM_PROMPT = """
You are **Agent Monica 007**, an AI-powered sales coach.

You guide Business Managers (BM) and Product Leaders (PL)
to master the pitch for **Dexel & Dexel ND**.

You operate in STAGES. Each stage has a PERSONA.

CRITICAL RULES:
1. Stay in Character for the current stage.
2. Be concise.
3. Do NOT jump stages yourself.
4. When the goal of a stage is met, CALL the tool `advance_stage`.
5. Wait for the user to finish before responding.

STAGES:

1. SETUP (COACH)
- Ask: Name, Role (BM/PL), HQ, Division.
- Confirm.
- Call `advance_stage`.

2. RCPA (CHEMIST)
- Act as retail chemist.
- Answer only what is asked.
- When user ends → `advance_stage`.

3. INTELLIGENCE (COACH)
- Give feedback on RCPA.
- Point missing probes (e.g., dosing frequency).
- Immediately `advance_stage`.

4. DOCTOR (DOCTOR)
- Answer probing questions.
- Listen to pitch.
- Give feedback.
- Then `advance_stage`.

5. OBJECTION (DOCTOR)
- Raise objection: "Competitor X is working well."
- Evaluate handling.
- When resolved → `advance_stage`.

6. KNOWLEDGE (COACH)
- Ask 3 questions:
  - What is IL6?
  - Relation between IL6 and pain?
  - Other inflammatory mediators?
- After 3rd → `advance_stage`.

7. END
- Say goodbye.
"""

STAGE_ORDER = ["SETUP", "RCPA", "INTELLIGENCE", "DOCTOR", "OBJECTION", "KNOWLEDGE", "END"]

PERSONA_BY_STAGE = {
    "SETUP": "COACH",
    "RCPA": "CHEMIST",
    "INTELLIGENCE": "COACH",
    "DOCTOR": "DOCTOR",
    "OBJECTION": "DOCTOR",
    "KNOWLEDGE": "COACH",
    "END": "COACH",
}


class MonicaAgent:
    def __init__(self):
        self.text_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.live_client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY"),
            http_options={"api_version": "v1alpha"},
        )

        self.model_text = "gemini-2.0-flash-exp"
        self.model_live = "models/gemini-2.0-flash-exp"

    # ---------- Helpers ----------

    def _next_stage(self, current: str) -> str:
        try:
            idx = STAGE_ORDER.index(current)
            return STAGE_ORDER[min(idx + 1, len(STAGE_ORDER) - 1)]
        except ValueError:
            return current

    def _persona(self, stage: str) -> str:
        return PERSONA_BY_STAGE.get(stage, "COACH")

    def _system_for_stage(self, stage: str) -> str:
        return SYSTEM_PROMPT + f"\n\nCURRENT STAGE: {stage}\nPERSONA: {self._persona(stage)}"

    def _store_message(self, db: Session, session: MonicaSession, role: str, content: str):
        msg = MonicaMessage(
            session_id=session.id,
            role=role,
            content=content,
            stage=session.current_stage,
            persona=session.current_persona,
        )
        db.add(msg)
        db.commit()

    # ---------- SETUP EXTRACTION ----------

    def _extract_setup_fields(self, session: MonicaSession, text: str, db: Session):
        t = text.lower()

        if not session.user_name and "pavan" in t:
            session.user_name = "Pavan"

        if not session.user_role and ("bm" in t or "business manager" in t):
            session.user_role = "BM"

        if not session.headquarter and ("india" in t or "head office" in t):
            session.headquarter = "India"

        if not session.division and ("nucleus" in t):
            session.division = "Nucleus"

        db.commit()

    # ---------- TEXT MODE ----------

    async def get_reply(self, db: Session, session: MonicaSession, text: str) -> MonicaReply:
        if session.current_stage == "SETUP":
            self._extract_setup_fields(session, text, db)

        system = self._system_for_stage(session.current_stage)

        prompt = f"""
{system}

User: {text}
"""

        response = self.text_client.models.generate_content(
            model=self.model_text,
            contents=prompt,
        )

        raw_reply = response.text or ""
        reply_text = raw_reply.replace("`advance_stage`", "").strip()

        self._store_message(db, session, "user", text)
        self._store_message(db, session, "assistant", reply_text)

        advance = bool(self._should_advance(session))

        if advance:
            old_stage = session.current_stage
            new_stage = self._next_stage(old_stage)

            session.current_stage = new_stage
            session.current_persona = self._persona(new_stage)
            db.commit()

            # SETUP → RCPA bridge
            if old_stage == "SETUP":
                scenario = (
                    f"Thank you, {session.user_name}. Your session is now configured for the "
                    f"{session.division} division and the product Dexel & Dexel ND.\n\n"
                    "You are now entering a Retail Chemist RCPA call. I will act as the chemist. "
                    "Begin by asking me about the doctor's prescribing behaviour."
                )
                self._store_message(db, session, "assistant", scenario)

            # RCPA → INTELLIGENCE → DOCTOR
            if new_stage == "INTELLIGENCE":
                coaching = (
                    "You collected the core information well. However, you missed one critical probe: "
                    "you did not ask about dosing frequency—whether the prescription is daily, weekly, "
                    "or monthly. This detail is essential because it shapes how you position Dexel to the doctor."
                )
                self._store_message(db, session, "assistant", coaching)

                session.current_stage = "DOCTOR"
                session.current_persona = "DOCTOR"
                db.commit()

                doctor_prompt = (
                    "I will now be acting as Dr. Monica. "
                    "Before you begin your pitch, what questions will you ask to understand my treatment goals?"
                )
                self._store_message(db, session, "assistant", doctor_prompt)

        return MonicaReply(
            reply=reply_text,
            advance_stage=advance,
            state_delta={},
        )

    def _should_advance(self, session: MonicaSession) -> bool:
        stage = session.current_stage

        if stage == "SETUP":
            return (
                session.user_name
                and session.user_role
                and session.headquarter
                and session.division
            )

        if stage == "RCPA":
            return True  # user signals end implicitly

        if stage == "DOCTOR":
            return False

        if stage == "OBJECTION":
            return False

        return False

    # ---------- VOICE MODE ----------

    def _live_config(self, stage: str):
        return {
            "response_modalities": ["AUDIO"],
            "speech_config": {
                "voice_config": {"prebuilt_voice_config": {"voice_name": "Puck"}}
            },
            "system_instruction": self._system_for_stage(stage),
            "tools": [
                {
                    "function_declarations": [
                        {
                            "name": "advance_stage",
                            "description": "Advance to next stage.",
                            "parameters": {"type": "OBJECT", "properties": {}},
                        }
                    ]
                }
            ],
        }

    async def connect_live_session(self, ws: WebSocket, db: Session, session_id: int):
        await ws.accept()

        monica = db.query(MonicaSession).filter(MonicaSession.id == session_id).first()
        if not monica:
            await ws.close(code=4004)
            return

        config = self._live_config(monica.current_stage)

        async with self.live_client.aio.live.connect(
            model=self.model_live, config=config
        ) as live:

            async def recv_client():
                try:
                    while True:
                        msg = await ws.receive()
                        if "bytes" in msg:
                            await live.send(
                                input={"data": msg["bytes"], "mime_type": "audio/pcm"},
                                end_of_turn=False,
                            )
                except Exception:
                    return

            async def send_client():
                async for resp in live.receive():
                    if resp.data:
                        await ws.send_bytes(resp.data)

                    if resp.server_content:
                        turn = resp.server_content.model_turn
                        if not turn:
                            continue

                        for part in turn.parts:
                            if part.function_call and part.function_call.name == "advance_stage":
                                new_stage = self._next_stage(monica.current_stage)
                                monica.current_stage = new_stage
                                monica.current_persona = self._persona(new_stage)
                                db.commit()

                                await ws.send_json({"type": "stage_update", "stage": new_stage})

            await asyncio.gather(recv_client(), send_client())
