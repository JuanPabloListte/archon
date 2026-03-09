from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from typing import List
from pydantic import BaseModel
from app.database import get_session
from app.models.db import User, Project, ProjectConnection
from app.api.deps import get_current_user

router = APIRouter()

class ConnectionCreate(BaseModel):
    project_id: str
    type: str  # openapi | database | logs
    config: dict

class ConnectionResponse(BaseModel):
    id: str
    project_id: str
    type: str
    created_at: str

def _check_project_access(project_id: str, user: User, session: Session) -> Project:
    project = session.exec(select(Project).where(Project.id == project_id, Project.owner_id == user.id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.post("", response_model=ConnectionResponse, status_code=201)
def create_connection(
    body: ConnectionCreate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    _check_project_access(body.project_id, current_user, session)
    conn = ProjectConnection(project_id=body.project_id, type=body.type, config_json=body.config)
    session.add(conn)
    session.commit()
    session.refresh(conn)

    # Trigger ingestion in background
    background_tasks.add_task(ingest_connection_sync, conn.id)

    return ConnectionResponse(id=conn.id, project_id=conn.project_id, type=conn.type, created_at=str(conn.created_at))

def ingest_connection_sync(connection_id: str):
    from app.workers.tasks import run_ingestion
    run_ingestion(connection_id)

@router.get("/project/{project_id}", response_model=List[ConnectionResponse])
def list_connections(project_id: str, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    _check_project_access(project_id, current_user, session)
    conns = session.exec(select(ProjectConnection).where(ProjectConnection.project_id == project_id)).all()
    return [ConnectionResponse(id=c.id, project_id=c.project_id, type=c.type, created_at=str(c.created_at)) for c in conns]
