import os
import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from dotenv import load_dotenv
load_dotenv()

from agent import VeriteAgent
from memory_store import LongTermMemoryStore

app = FastAPI(title="Verité Chatbot API", version="1.0.0")



# Middleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=
    [
        "http://localhost:3000",
        "https://verite-research-assistant.vercel.app/"
    ], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Session storing and Memory

active_sessions: dict[str, VeriteAgent] = {}

long_term_store = LongTermMemoryStore()



# Models

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    user_id: Optional[str] = "anonymous"

class ChatResponse(BaseModel):
    session_id: str
    reply: str
    sources: list[dict]
    search_used: bool
    
    
    
@app.get("/health")
def health():
    return {"status": "ok"}



# Main Chat EndPoint

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):


    # Use provided session_id or create a new one
    session_id = req.session_id or str(uuid.uuid4())


    # Get or create agent for this session
    if session_id not in active_sessions:
        
        
        # Load long-term memory for this user
        lt_context = long_term_store.get_summary(req.user_id)

        active_sessions[session_id] = VeriteAgent(
            user_id=req.user_id,
            long_term_context=lt_context,
        )

    agent = active_sessions[session_id]
    
    

    # Run the agent
    try:
        result = await agent.chat(req.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

    # Persist exchange for long-term memory
    long_term_store.append(
        req.user_id,
        req.message,
        result["reply"]
    )

    return ChatResponse(
        session_id=session_id,
        reply=result["reply"],
        sources=result.get("sources", []),
        search_used=result.get("search_used", False),
    )
    
    
    
# Session Clean

@app.delete("/session/{session_id}")
def end_session(session_id: str):
    active_sessions.pop(session_id, None)
    return {"ended": session_id}


