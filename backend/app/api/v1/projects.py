from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from pydantic import BaseModel
from app.database import get_session
from app.models.db import User, Project
from app.api.deps import get_current_user

router = APIRouter()

class ProjectCreate(BaseModel):
    name: str
    description: str | None = None

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str | None
    owner_id: str
    created_at: str
    audit_system_prompt: str | None = None

    class Config:
        from_attributes = True

class ProjectSettings(BaseModel):
    audit_system_prompt: str | None = None

@router.get("", response_model=List[ProjectResponse])
def list_projects(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    projects = session.exec(select(Project).where(Project.owner_id == current_user.id)).all()
    return [ProjectResponse(id=p.id, name=p.name, description=p.description, owner_id=p.owner_id, created_at=str(p.created_at)) for p in projects]

@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(body: ProjectCreate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    project = Project(name=body.name, description=body.description, owner_id=current_user.id)
    session.add(project)
    session.commit()
    session.refresh(project)
    return ProjectResponse(id=project.id, name=project.name, description=project.description, owner_id=project.owner_id, created_at=str(project.created_at))

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    project = session.exec(select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse(id=project.id, name=project.name, description=project.description, owner_id=project.owner_id, created_at=str(project.created_at), audit_system_prompt=project.audit_system_prompt)

@router.patch("/{project_id}/settings", response_model=ProjectResponse)
def update_project_settings(
    project_id: str,
    body: ProjectSettings,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    project = session.exec(select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project.audit_system_prompt = body.audit_system_prompt  # None = reset to default
    session.add(project)
    session.commit()
    session.refresh(project)
    return ProjectResponse(id=project.id, name=project.name, description=project.description, owner_id=project.owner_id, created_at=str(project.created_at), audit_system_prompt=project.audit_system_prompt)

@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: str, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    project = session.exec(select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    session.delete(project)
    session.commit()
