"""Global knowledge base retriever — search cross-project patterns."""
from sqlmodel import Session, text
from app.rag.embeddings import embed_text


def retrieve_global(query: str, session: Session, top_k: int = 3, min_similarity: float = 0.6) -> list[dict]:
    """
    Search the global knowledge base for patterns similar to the query.
    Returns entries above min_similarity threshold, ordered by relevance.
    """
    query_vec = embed_text(query)
    vec_str = "[" + ",".join(str(v) for v in query_vec) + "]"

    sql = f"""
        SELECT id, category, severity, title, description, solution,
               confirmed, usage_count,
               1 - (embedding <=> '{vec_str}'::vector) AS similarity
        FROM global_knowledge
        ORDER BY embedding <=> '{vec_str}'::vector
        LIMIT :k
    """

    rows = list(session.exec(text(sql), params={"k": top_k * 2}))  # fetch extra, filter by threshold

    results = []
    for row in rows:
        sim = float(row[8])
        if sim < min_similarity:
            continue
        results.append({
            "id": row[0],
            "category": row[1],
            "severity": row[2],
            "title": row[3],
            "description": row[4],
            "solution": row[5],
            "confirmed": row[6],
            "usage_count": row[7],
            "similarity": sim,
        })
        if len(results) >= top_k:
            break

    return results


def get_global_stats(session: Session) -> dict:
    """Return stats about the global knowledge base."""
    sql = """
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE confirmed = true) as confirmed,
            COUNT(DISTINCT category) as categories
        FROM global_knowledge
    """
    rows = list(session.exec(text(sql)))
    if rows:
        return {"total": int(rows[0][0]), "confirmed": int(rows[0][1]), "categories": int(rows[0][2])}
    return {"total": 0, "confirmed": 0, "categories": 0}
