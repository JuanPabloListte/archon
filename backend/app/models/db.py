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
    context_json: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    audit_system_prompt: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
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
    status: str = Field(default="open")  # "open" | "fixed" | "ignored"
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


class GlobalKnowledge(SQLModel, table=True):
    """Cross-project knowledge base — patterns learned from all audits."""
    __tablename__ = "global_knowledge"
    id: str = Field(default_factory=gen_uuid, primary_key=True)
    category: str          # api | database | security | performance
    severity: str          # critical | high | medium | low | info
    title: str
    description: str = Field(sa_column=Column(Text))
    solution: str = Field(sa_column=Column(Text))
    confirmed: bool = False   # True when a user marked the finding as "fixed"
    usage_count: int = Field(default=1)
    embedding: List[float] = Field(sa_column=Column(Vector(768)))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AuditRun(SQLModel, table=True):
    __tablename__ = "audit_runs"
    id: str = Field(default_factory=gen_uuid, primary_key=True)
    project_id: str = Field(foreign_key="projects.id", index=True)
    health_score: float = 0.0
    total_findings: int = 0
    summary: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ApiKey(SQLModel, table=True):
    __tablename__ = "api_keys"
    id: str = Field(default_factory=gen_uuid, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    name: str
    key_hash: str = Field(unique=True, index=True)
    key_prefix: str           # first 12 chars of raw token, safe to display
    is_active: bool = True
    last_used_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AuditSchedule(SQLModel, table=True):
    __tablename__ = "audit_schedules"
    id: str = Field(default_factory=gen_uuid, primary_key=True)
    project_id: str = Field(foreign_key="projects.id", index=True)
    is_active: bool = True
    frequency: str = "weekly"            # daily | weekly | custom
    cron_expression: Optional[str] = None  # only for frequency=custom
    hour_utc: int = 9                    # UTC hour for daily/weekly
    day_of_week: Optional[int] = None    # 0=Mon..6=Sun, only for weekly
    alert_email: Optional[str] = None
    alert_webhook_url: Optional[str] = None
    health_score_threshold: float = 70.0
    alert_on_critical: bool = True
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AlertEvent(SQLModel, table=True):
    __tablename__ = "alert_events"
    id: str = Field(default_factory=gen_uuid, primary_key=True)
    project_id: str = Field(foreign_key="projects.id", index=True)
    schedule_id: str = Field(foreign_key="audit_schedules.id", index=True)
    trigger_type: str                 # health_score_drop | critical_findings | both
    health_score: float
    critical_count: int = 0
    notification_sent: str = "none"   # none | email | webhook | both
    success: bool = True
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CustomRule(SQLModel, table=True):
    __tablename__ = "custom_rules"
    id: str = Field(default_factory=gen_uuid, primary_key=True)
    project_id: str = Field(foreign_key="projects.id", index=True)
    name: str
    description: Optional[str] = None
    category: str = "security"         # api | database | security | performance
    severity: str = "medium"           # critical | high | medium | low | info
    target: str = "endpoints"          # endpoints | tables
    rule_yaml: str = Field(sa_column=Column(Text))
    rule_json: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
