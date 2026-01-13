import os
import json
from typing import Dict, Any, List
from google import genai
from models import MonicaSession, MonicaMessage
from database_models import MonicaReply
from sqlalchemy.orm import Session

SYSTEM_PROMPT = """You are **Agent Monica 007**, an AI Sales Coach for the *Stimulus Division*.

Your mission is to train Business Managers (BM) and Product Leaders (PL) on **Dexel & Dexel ND** using a realistic, multi-stage simulation.

You are not a chatbot.  
You are a **structured coaching agent** that:
- Runs in defined stages  
- Switches personas (Coach, Chemist, Doctor)  
- Evaluates performance  
- Gives targeted feedback  
- Never breaks role  
- Never skips stages  
- Produces trainer-grade coaching  

## STAGES (FSM)
You must always operate in exactly one of these stages:
1. SETUP
2. RCPA
3. INTELLIGENCE
4. DOCTOR
5. OBJECTION
6. KNOWLEDGE
7. END

You may only advance when the current stage’s objective is completed.

## STAGE BEHAVIOR

### 1. SETUP – Persona: COACH
Goal: Collect user details.
You must ask for: Name, Role (BM or PL), Headquarter, Division.
Rules:
- Do not proceed until all 4 are collected.
- Confirm configuration once collected.
- Then introduce the scenario.
Advance when all fields are present.

### 2. RCPA – Persona: CHEMIST
You now act strictly as a **retail chemist**.
Rules:
- Answer only what is asked.
- Do NOT volunteer extra information.
- Keep responses short and realistic.
- Maintain a consistent scenario.
- Encourage probing by being neutral.
Remain in RCPA until the user signals completion (e.g., “Thank you” / “I’m done”).

### 3. INTELLIGENCE – Persona: COACH
Analyze the RCPA interaction.
You must Identify what the user collected and what was missed (Dosing frequency, Brand strength, Volume per Rx, Duration of therapy, Patient type).
Provide **specific coaching**.
Advance after delivering feedback.

### 4. DOCTOR – Persona: DOCTOR
You now act as a **doctor**.
Rules:
- Answer probing questions realistically.
- Wait for the user’s pitch.
- Do not guide them.
After the pitch, evaluate (Did they probe? Link needs? Personalize?) and give structured feedback.
Then transition to objection.

### 5. OBJECTION – Persona: DOCTOR
Raise a realistic objection (e.g., "Competitor X is effective").
Evaluate response (Acknowledge? Differentiate? Anchor to outcome? Use Dexel advantage?).
Give coaching.
Advance after objection handling is complete.

### 6. KNOWLEDGE – Persona: COACH
Ask these one by one:
1. What is IL6?
2. What is the relationship between IL6 and pain?
3. What are other inflammatory mediators besides IL6?
Evaluate accuracy and reinforce learning.
Advance to END.

### 7. END
Close with a summary message.

## GLOBAL RULES
- Never break persona.
- Never skip a stage.
- Always be realistic and professional.

## OUTPUT FORMAT
Every response must be valid JSON matching this schema:
{
  "reply": "Your spoken or textual response",
  "advance_stage": true | false,
  "state_delta": {
    "key": "value"
  }
}
"""

class MonicaAgent:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = "gemini-flash-latest"

    async def get_reply(self, db_session: Session, monica_session: MonicaSession, user_text: str) -> MonicaReply:
        # Construct history
        history = []
        for msg in monica_session.messages:
            history.append({
                "role": "user" if msg.role == "user" else "model",
                "parts": [{"text": msg.content}]
            })

        # Prepend System Prompt if history is empty or as context
        # Gemini does better with system instructions
        
        # Prepare context about current stage and state
        context = f"Current Stage: {monica_session.current_stage}\n"
        context += f"Current Persona: {monica_session.current_persona}\n"
        context += f"User Info: {monica_session.user_name}, {monica_session.user_role}, {monica_session.headquarter}, {monica_session.division}\n"
        context += f"State Delta: {json.dumps(monica_session.state_delta)}\n"
        
        # Call Gemini
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=history + [{"role": "user", "parts": [{"text": f"Context: {context}\nUser says: {user_text}"}]}],
                config={
                    "system_instruction": SYSTEM_PROMPT,
                    "response_mime_type": "application/json",
                }
            )
            
            result_json = json.loads(response.text)
            reply = MonicaReply(**result_json)
            
            # Record user message
            user_msg = MonicaMessage(
                session_id=monica_session.id,
                role="user",
                content=user_text,
                stage=monica_session.current_stage,
                persona=monica_session.current_persona
            )
            db_session.add(user_msg)
            
            # Update Session State
            current_stg = monica_session.current_stage
            
            # Record assistant message
            assistant_msg = MonicaMessage(
                session_id=monica_session.id,
                role="assistant",
                content=reply.reply,
                stage=current_stg,
                persona=monica_session.current_persona
            )
            db_session.add(assistant_msg)
            
            if reply.advance_stage:
                monica_session.current_stage = self._get_next_stage(monica_session.current_stage)
                monica_session.current_persona = self._get_persona_for_stage(monica_session.current_stage)
            
            # Merge state delta
            if reply.state_delta:
                new_state = monica_session.state_delta.copy()
                new_state.update(reply.state_delta)
                monica_session.state_delta = new_state
                
                # Specifically update user info if we WERE in SETUP
                if current_stg == "SETUP":
                    if "name" in reply.state_delta: monica_session.user_name = reply.state_delta["name"]
                    if "role" in reply.state_delta: monica_session.user_role = reply.state_delta["role"]
                    if "headquarter" in reply.state_delta: monica_session.headquarter = reply.state_delta["headquarter"]
                    if "division" in reply.state_delta: monica_session.division = reply.state_delta["division"]

            db_session.commit()
            return reply
            
        except Exception as e:
            print(f"Error calling Gemini: {e}")
            raise e

    def _get_next_stage(self, current_stage: str) -> str:
        stages = ["SETUP", "RCPA", "INTELLIGENCE", "DOCTOR", "OBJECTION", "KNOWLEDGE", "END"]
        try:
            idx = stages.index(current_stage)
            if idx < len(stages) - 1:
                return stages[idx + 1]
        except ValueError:
            pass
        return current_stage

    def _get_persona_for_stage(self, stage: str) -> str:
        mapping = {
            "SETUP": "COACH",
            "RCPA": "CHEMIST",
            "INTELLIGENCE": "COACH",
            "DOCTOR": "DOCTOR",
            "OBJECTION": "DOCTOR",
            "KNOWLEDGE": "COACH",
            "END": "COACH"
        }
        return mapping.get(stage, "COACH")
