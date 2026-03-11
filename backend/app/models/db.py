from sqlmodel import SQLModel, Field, Column, Relationship
from sqlalchemy import JSON, Text
from pgvector.sqlalchemy import Vector
from typing import Optional, List
from datetime import datetime
import uuid

def gen_uuid():
    return str(uuid.uuid4())

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: str = Field(default_factory=gen_uuid, primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: Optional[str] = None
    google_id: Optional[str] = Field(default=None, index=True)
    avatar_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    projects: List["Project"] = Relationship(back_populates="owner")

class Project(SQLModel, table=True):
    __tablename__ = "projects"
    id: str = Field(default_factory=gen_uuid, primary_key=True)
    name: str
    description: Optional[str] = None
    owner_id: str = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    owner: Optional[User] = Relationship(back_populates="projects")
    connections: List["ProjectConnection"] = Relationship(back_populates="project")
    endpoints: List["ApiEndpoint"] = Relationship(back_populates="project")
    db_tables: List["DbTable"] = Relationship(back_populates="project")
    findings: List["AuditFinding"] = Relationship(back_populates="project")
    reports: List["Report"] = Relationship(back_populates="project")

class ProjectConnection(SQLModel, table=True):
    __tablename__ = "project_connections"
    id: str = Field(default_factory=gen_uuid, primary_key=True)
    project_id: str = Field(foreign_key="projects.id", index=True)
    type: str  # openapi | database | logs
    config_json: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    project: Optional[Project] = Relationship(back_populates="connections")

class ApiEndpoint(SQLModel, table=True):
    __tablename__ = "api_endpoints"
    id: str = Field(default_factory=gen_uuid, primary_key=True)
    project_id: str = Field(foreign_key="projects.id", index=True)
    path: str
    method: str
    auth_required: bool = False
    description: Optional[str] = None
    parameters: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    responses: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    tags: Optional[list] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    project: Optional[Project] = Relationship(back_populates="endpoints")

class DbTable(SQLModel, table=True):
    __tablename__ = "db_tables"
    id: str = Field(default_factory=gen_uuid, primary_key=True)
    project_id: str = Field(foreign_key="projects.id", index=True)
    table_name: str
    row_count: Optional[int] = None
    columns: Optional[list] = Field(default=None, sa_column=Column(JSON))
    indexes: Optional[list] = Field(default=None, sa_column=Column(JSON))
    foreign_keys: Optional[list] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    project: Optional[Project] = Relationship(back_populates="db_tables")

class AuditFinding(SQLModel, table=True):
    __tablename__ = "audit_findings"
    id: str = Field(default_factory=gen_uuid, primary_key=True)
    project_id: str = Field(foreign_key="projects.id", index=True)
    severity: str  # critical | high | medium | low | info
    category: str  # api | database | security | performance
    title: str
    description: str
    recommendation: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    source: str = Field(default="rule")  # "rule" | "ai"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    project: Optional[Project] = Relationship(back_populates="findings")

class Embedding(SQLModel, table=True):
    __tablename__ = "embeddings"
    id: str = Field(default_factory=gen_uuid, primary_key=True)
    project_id: str = Field(foreign_key="projects.id", index=True)
    source_type: str  # endpoint | table | finding | report
    source_id: str
    content: str = Field(sa_column=Column(Text))
    embedding: List[float] = Field(sa_column=Column(Vector(768)))

class UserCredential(SQLModel, table=True):
    __tablename__ = "user_credentials"
    id: str = Field(default_factory=gen_uuid, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    provider: str  # anthropic | openai | gemini | groq | mistral | ollama | custom
    label: Optional[str] = None
    api_key_encrypted: Optional[str] = None
    model: str
    base_url: Optional[str] = None
    is_active: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Report(SQLModel, table=True):
    __tablename__ = "reports"
    id: str = Field(default_factory=gen_uuid, primary_key=True)
    project_id: str = Field(foreign_key="projects.id", index=True)
    health_score: float
    summary: Optional[str] = None
    report_json: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    project: Optional[Project] = Relationship(back_populates="reports")
