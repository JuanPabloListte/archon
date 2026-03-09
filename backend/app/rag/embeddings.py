from sentence_transformers import SentenceTransformer
from sqlmodel import Session, select
from app.models.db import ApiEndpoint, DbTable, AuditFinding, Embedding
from app.config import settings
import numpy as np

_model = None

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("nomic-ai/nomic-embed-text-v1", trust_remote_code=True)
    return _model

def embed_text(text: str) -> list[float]:
    model = get_model()
    vec = model.encode(text, normalize_embeddings=True)
    return vec.tolist()

def index_project(project_id: str, session: Session):
    # Clear old embeddings
    old = session.exec(select(Embedding).where(Embedding.project_id == project_id)).all()
    for e in old:
        session.delete(e)
    session.commit()

    endpoints = session.exec(select(ApiEndpoint).where(ApiEndpoint.project_id == project_id)).all()
    for ep in endpoints:
        text = f"API endpoint: {ep.method} {ep.path}. {ep.description or ''}. Auth required: {ep.auth_required}."
        _save_embedding(session, project_id, "endpoint", ep.id, text)

    tables = session.exec(select(DbTable).where(DbTable.project_id == project_id)).all()
    for t in tables:
        col_names = [c.get("name") for c in (t.columns or [])]
        text = f"Database table: {t.table_name}. Columns: {', '.join(col_names)}. Row count: {t.row_count}."
        _save_embedding(session, project_id, "table", t.id, text)

    findings = session.exec(select(AuditFinding).where(AuditFinding.project_id == project_id)).all()
    for f in findings:
        text = f"Audit finding [{f.severity}] {f.title}: {f.description}. Recommendation: {f.recommendation}"
        _save_embedding(session, project_id, "finding", f.id, text)

    session.commit()

def _save_embedding(session: Session, project_id: str, source_type: str, source_id: str, text: str):
    vec = embed_text(text)
    emb = Embedding(
        project_id=project_id,
        source_type=source_type,
        source_id=source_id,
        content=text,
        embedding=vec,
    )
    session.add(emb)
