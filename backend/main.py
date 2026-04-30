import os
import json
from typing import Dict, Any
from backend.database import InteractionRecord, SessionLocal
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import graph

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    state: Dict[str, Any]

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    initial_state = {
        "messages": [("user", req.message)],
        "form_data": req.state
    }
    final_state = graph.invoke(initial_state)
    return {
        "ai_message": final_state["messages"][-1].content,
        "updated_form": final_state["form_data"]
    }

# --- NEW: Save to Database Endpoint ---
@app.post("/save")
async def save_interaction(state: Dict[str, Any], db: Session = Depends(get_db)):
    try:
        new_record = InteractionRecord(
            hcp_name=state.get("hcp_name"),
            interaction_type=state.get("interaction_type"),
            date=state.get("date"),
            time=state.get("time"),
            attendees=state.get("attendees"),
            topics=state.get("topics"),
            materials=json.dumps(state.get("materials", [])),
            samples=json.dumps(state.get("samples", [])),
            sentiment=state.get("sentiment"),
            outcomes=state.get("outcomes"),
            follow_ups=state.get("follow_ups")
        )
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        return {"status": "success", "message": f"Interaction saved with ID {new_record.id}"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))