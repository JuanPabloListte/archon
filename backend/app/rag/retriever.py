from sqlmodel import Session, text
from app.models.db import Embedding
from app.rag.embeddings import embed_text

def retrieve(query: str, project_id: str, session: Session, top_k: int = 5) -> list[dict]:
    query_vec = embed_text(query)
    vec_str = "[" + ",".join(str(v) for v in query_vec) + "]"

    sql = f"""
        SELECT id, source_type, source_id, content,
               1 - (embedding <=> '{vec_str}'::vector) AS similarity
        FROM embeddings
        WHERE project_id = :pid
        ORDER BY embedding <=> '{vec_str}'::vector
        LIMIT :k
    """

    result = session.exec(text(sql), params={"pid": project_id, "k": top_k})

    return [
        {"source_type": row[1], "source_id": row[2], "content": row[3], "similarity": float(row[4])}
        for row in result
    ]
