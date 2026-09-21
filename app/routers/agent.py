"""
Agent router — Chat and autonomous scan endpoints for the PaySense AI agent.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.agent.engine import PaySenseAgent
from app.database import fetch_all
from app.config import settings

router = APIRouter(prefix='/api/agent', tags=['agent'])

# Lazy-init agent (created on first request to ensure config is loaded)
_agent: PaySenseAgent | None = None


def get_agent() -> PaySenseAgent:
    global _agent
    if _agent is None:
        _agent = PaySenseAgent(api_key=settings.GEMINI_API_KEY or None)
    return _agent


class ChatRequest(BaseModel):
    message: str


@router.post('/chat')
async def chat_with_agent(req: ChatRequest) -> dict:
    """Send a message to the PaySense AI agent."""
    try:
        agent = get_agent()
        result = await agent.chat(req.message)
        return {
            "response": result.get("response", "No response generated"),
            "tools_used": result.get("tools_used", []),
            "reasoning": result.get("reasoning", "")
        }
    except Exception as e:
        return {
            "response": f"Agent error: {str(e)}. Please check your GEMINI_API_KEY.",
            "tools_used": [],
            "reasoning": ""
        }


@router.post('/scan')
async def autonomous_scan() -> dict:
    """Trigger an autonomous health scan by the agent."""
    try:
        agent = get_agent()
        result = await agent.autonomous_scan()
        return {
            "response": result.get("response", ""),
            "tools_used": result.get("tools_used", []),
            "report": result
        }
    except Exception as e:
        return {"response": f"Scan error: {str(e)}", "tools_used": [], "report": {}}


@router.get('/history')
async def get_history() -> list:
    """Get conversation history."""
    agent = get_agent()
    history = agent.get_conversation_history()
    # Serialize Content objects to simple dicts for JSON response
    serialized = []
    for content in history:
        role = content.role if hasattr(content, 'role') else 'unknown'
        text_parts = []
        for part in (content.parts or []):
            if hasattr(part, 'text') and part.text:
                text_parts.append(part.text)
        if text_parts:
            serialized.append({"role": role, "text": " ".join(text_parts)})
    return serialized


@router.delete('/history')
async def clear_history() -> dict:
    """Clear conversation history."""
    agent = get_agent()
    agent.clear_history()
    return {"status": "success", "message": "Conversation history cleared"}


@router.get('/decisions')
async def get_decisions() -> list:
    """Get the agent decision audit log."""
    return await fetch_all(
        "SELECT * FROM agent_decisions ORDER BY created_at DESC LIMIT 50"
    )
