from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from app.database import get_session
from app.models.db import User, Project
from app.api.deps import get_current_user
from app.agents.query_agent import QueryAgent

router = APIRouter()

class ChatRequest(BaseModel):
    project_id: str
    question: str

class ChatResponse(BaseModel):
    answer: str
    sources: list = []

@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    project = session.exec(select(Project).where(Project.id == body.project_id, Project.owner_id == current_user.id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    agent = QueryAgent(project_id=body.project_id, session=session)
    result = await agent.answer(body.question)
    return ChatResponse(answer=result["answer"], sources=result.get("sources", []))
