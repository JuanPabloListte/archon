"""Global knowledge base indexer — learns patterns across all projects."""
import logging
from sqlmodel import Session, text
from app.models.db import AuditFinding, GlobalKnowledge
from app.rag.embeddings import embed_text

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.93  # entries more similar than this are considered duplicates


def _find_similar(session: Session, vec: list[float]) -> GlobalKnowledge | None:
    """Return an existing entry if one is very similar (deduplication)."""
    vec_str = "[" + ",".join(str(v) for v in vec) + "]"
    sql = f"""
        SELECT id, 1 - (embedding <=> '{vec_str}'::vector) AS similarity
        FROM global_knowledge
        ORDER BY embedding <=> '{vec_str}'::vector
        LIMIT 1
    """
    rows = list(session.exec(text(sql)))
    if rows and float(rows[0][1]) >= SIMILARITY_THRESHOLD:
        return session.get(GlobalKnowledge, rows[0][0])
    return None


def index_findings(findings: list[AuditFinding], session: Session, confirmed: bool = False):
    """
    Index a list of findings into the global knowledge base.
    - Deduplicates by embedding similarity.
    - If confirmed=True (user marked as Fixed), marks the entry as confirmed.
    """
    indexed = 0
    for f in findings:
        try:
            text_to_embed = f"{f.title}. {f.description}. Solution: {f.recommendation}"
            vec = embed_text(text_to_embed)

            existing = _find_similar(session, vec)
            if existing:
                existing.usage_count += 1
                if confirmed:
                    existing.confirmed = True
                session.add(existing)
                logger.debug(f"Global KB: incremented usage for '{existing.title}' ({existing.usage_count}x)")
            else:
                entry = GlobalKnowledge(
                    category=f.category,
                    severity=f.severity,
                    title=f.title,
                    description=f.description,
                    solution=f.recommendation,
                    confirmed=confirmed,
                    embedding=vec,
                )
                session.add(entry)
                indexed += 1
                logger.debug(f"Global KB: indexed new pattern '{f.title}'")
        except Exception as e:
            logger.warning(f"Global KB: failed to index '{f.title}': {e}")

    session.commit()
    if indexed:
        logger.info(f"Global KB: added {indexed} new pattern(s)")
