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

        self.model_text = "gemini-2.5-flash"
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

    def _store_message(self, db: Session, session: MonicaSession, role: str, content: str, stage: str = None, persona: str = None):
        msg = MonicaMessage(
            session_id=session.id,
            role=role,
            content=content,
            stage=stage or session.current_stage,
            persona=persona or session.current_persona,
        )
        db.add(msg)
        db.commit()

    # ---------- SETUP EXTRACTION ----------

    def _extract_setup_fields(self, session: MonicaSession, text: str, db: Session):
        t = text.lower()

        # Extract name - look for common names or ask user to provide
        if not session.user_name:
            if "pavan" in t:
                session.user_name = "Pavan"
            # Add more flexible name extraction
            words = text.split()
            for i, word in enumerate(words):
                if word.lower() in ["name", "i'm", "im", "i am", "this is"] and i + 1 < len(words):
                    potential_name = words[i + 1].strip(",.!?")
                    if potential_name and len(potential_name) > 1:
                        session.user_name = potential_name.capitalize()
                        break

        # Extract role
        if not session.user_role:
            if "bm" in t or "business manager" in t:
                session.user_role = "BM"
            elif "pl" in t or "product leader" in t:
                session.user_role = "PL"

        # Extract headquarter
        if not session.headquarter:
            if "india" in t:
                session.headquarter = "India"
            elif "hq" in t or "headquarter" in t or "head office" in t:
                # Try to extract location after "hq"
                words = t.split()
                for i, word in enumerate(words):
                    if word in ["hq", "headquarter"] and i + 1 < len(words):
                        session.headquarter = words[i + 1].capitalize()
                        break

        # Extract division - FIXED to include "stimulus"
        if not session.division:
            if "nucleus" in t:
                session.division = "Nucleus"
            elif "stimulus" in t:
                session.division = "Stimulus"
            elif "division" in t:
                # Try to extract division name
                words = t.split()
                for i, word in enumerate(words):
                    if word == "division" and i > 0:
                        session.division = words[i - 1].capitalize()
                        break

        db.commit()

    # ---------- TEXT MODE ----------

    async def get_reply(self, db: Session, session: MonicaSession, text: str) -> MonicaReply:
        if session.current_stage == "SETUP":
            self._extract_setup_fields(session, text, db)

        # Special handling for KNOWLEDGE stage - ask questions sequentially
        is_knowledge_stage = session.current_stage == "KNOWLEDGE"
        if is_knowledge_stage:
            knowledge_questions = [
                "What is IL-6?",
                "What is the relationship between IL-6 and pain?",
                "Name two other inflammatory mediators besides IL-6."
            ]
            
            # Count how many questions have been asked
            knowledge_messages = [m for m in session.messages if m.stage == "KNOWLEDGE"]
            questions_asked = sum(1 for m in knowledge_messages if m.role == "assistant" and any(q in m.content for q in knowledge_questions))
            
            # Store user's answer
            self._store_message(db, session, "user", text)
            
            # Decide on reply
            if questions_asked < len(knowledge_questions):
                next_question = knowledge_questions[questions_asked]
                reply_text = f"Thank you for your answer. Next question: {next_question}"
                self._store_message(db, session, "assistant", reply_text)
                # Keep current stage
                return MonicaReply(reply=reply_text, advance_stage=False, state_delta={})
            else:
                # All questions answered, set flag to advance
                reply_text = "Thank you for completing the knowledge assessment."
                self._store_message(db, session, "assistant", reply_text)
                # We will advance to END below
                text = "SYSTEM_FORCE_ADVANCE" # fake text to pass through
        else:
            system = self._system_for_stage(session.current_stage)
            prompt = f"{system}\n\nUser: {text}\n"

            try:
                response = self.text_client.models.generate_content(
                    model=self.model_text,
                    contents=prompt,
                )
                reply_text = (response.text or "").replace("`advance_stage`", "").strip()
            except Exception as e:
                print(f"Gemini API Error: {e}")
                reply_text = "I'm having a bit of trouble connecting to my brain right now. Could you please try again?"

            self._store_message(db, session, "user", text)
            
        r_text = locals().get('raw_reply', '')
        advance = bool(self._should_advance(session, text)) or ("advance_stage" in r_text)
        
        # Manual override for KNOWLEDGE completion
        if is_knowledge_stage and text == "SYSTEM_FORCE_ADVANCE":
            advance = True

        if not is_knowledge_stage: # Normal text mode
            self._store_message(db, session, "assistant", reply_text)

        if advance:
            old_stage = session.current_stage
            new_stage = self._next_stage(old_stage)

            session.current_stage = new_stage
            session.current_persona = self._persona(new_stage)
            db.commit()

            bridge_content = ""

            # SETUP → RCPA bridge
            if old_stage == "SETUP":
                bridge_content = (
                    f"Thank you, {session.user_name}. Your session is now configured for the "
                    f"{session.division} division and the product Dexel & Dexel ND.\n\n"
                    "You are now entering a Retail Chemist RCPA call. I will act as the chemist. "
                    "Begin by asking me about the doctor's prescribing behaviour."
                )

            # RCPA → INTELLIGENCE → DOCTOR
            elif new_stage == "INTELLIGENCE":
                bridge_content = (
                    "You collected the core information well. However, you missed one critical probe: "
                    "you did not ask about dosing frequency—whether the prescription is daily, weekly, "
                    "or monthly. This detail is essential because it shapes how you position Dexel to the doctor.\n\n"
                    "I will now be acting as Dr. Monica. "
                    "Before you begin your pitch, what questions will you ask to understand my treatment goals?"
                )
                session.current_stage = "DOCTOR"
                session.current_persona = "DOCTOR"
                db.commit()

            # DOCTOR → OBJECTION
            elif new_stage == "OBJECTION":
                bridge_content = (
                    "Now let's test your objection handling skills. "
                    "I'm going to raise a common concern that doctors have.\n\n"
                    "Look, I appreciate the information about Dexel, but honestly, "
                    "my current Vitamin D brand is working well for my patients and they're familiar with it. "
                    "Why should I switch to something new?"
                )

            # OBJECTION → KNOWLEDGE
            elif new_stage == "KNOWLEDGE":
                bridge_content = (
                    "Good work on handling that objection. Now let's assess your product knowledge. "
                    "I'm going to ask you three questions about the science behind Dexel.\n\n"
                    "First question: What is IL-6?"
                )

            # KNOWLEDGE → END
            elif new_stage == "END":
                bridge_content = (
                    "Excellent! You've completed all stages of the Agent Monica 007 training session.\n\n"
                    "Your performance summary:\n"
                    "✅ RCPA Intelligence Gathering\n"
                    "✅ Doctor Probing and Pitching\n"
                    "✅ Objection Handling\n"
                    "✅ Product Knowledge Assessment\n\n"
                    "Your trainer will receive a detailed assessment of your session. "
                    "Thank you for practicing with me today."
                )

            if bridge_content:
                reply_text += "\n\n" + bridge_content
                self._store_message(db, session, "assistant", bridge_content)

        return MonicaReply(
            reply=reply_text,
            advance_stage=advance,
            state_delta={},
        )


    def _should_advance(self, session: MonicaSession, text: str) -> bool:
        """
        Determine if the current stage should advance based on session state
        and conversation history.
        """
        stage = session.current_stage
        t = text.lower()

        if stage == "SETUP":
            details_complete = (
                session.user_name
                and session.user_role
                and session.headquarter
                and session.division
            )
            if not details_complete:
                return False
                
            # If details are complete, check if current text is a confirmation or readiness
            confirmations = ["yes", "correct", "yeah", "that's right", "yup", "ok", "proceed", "sure", "start", "ready", "begin"]
            return any(c in t for c in confirmations)

        if stage == "RCPA":
            # Check if user has signaled end of RCPA conversation
            end_signals = [
                "thank you",
                "thanks",
                "that's all",
                "that's it",
                "done",
                "no more questions",
                "that's all i needed",
                "move to doctor",
                "pitch to the doctor",
                "call the doctor"
            ]
            return any(signal in t for signal in end_signals)

        if stage == "DOCTOR":
            # Advance when user thanks doctor or signals end of pitch
            end_signals = [
                "thank you doctor",
                "thanks doctor",
                "that's all",
                "appreciate your time",
                "thank you for your time",
                "that covers everything"
            ]
            # Check if we have some interaction in messages
            doctor_stage_messages = [m for m in session.messages if m.stage == "DOCTOR"]
            has_enough_interaction = len(doctor_stage_messages) >= 3 # at least 1-2 exchanges
            
            return (any(signal in t for signal in end_signals) and 
                    has_enough_interaction)

        if stage == "OBJECTION":
            # Advance after user has responded to objection
            objection_messages = [m for m in session.messages if m.stage == "OBJECTION"]
            # Need at least 2 messages: Monica's objection + user's response
            if len(objection_messages) >= 2: 
                return True
            return False

        if stage == "KNOWLEDGE":
            # Flow is handled in get_reply itself, but we return True when force_advance is set
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
