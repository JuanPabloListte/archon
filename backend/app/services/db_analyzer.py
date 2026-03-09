from sqlmodel import Session
from app.models.db import DbTable
import sqlalchemy as sa

SENSITIVE_COLUMN_NAMES = {
    "password", "password_hash", "secret", "token", "api_key",
    "credit_card", "ssn", "phone", "email", "address", "dob",
    "date_of_birth", "social_security", "cvv", "pin",
}

def analyze_database(connection_string: str, project_id: str, session: Session):
    try:
        engine = sa.create_engine(connection_string, connect_args={"options": "-c statement_timeout=10000"})
        with engine.connect() as conn:
            tables = _get_tables(conn)
            for table_name in tables:
                columns = _get_columns(conn, table_name)
                indexes = _get_indexes(conn, table_name)
                foreign_keys = _get_foreign_keys(conn, table_name)
                row_count = _get_row_count(conn, table_name)

                db_table = DbTable(
                    project_id=project_id,
                    table_name=table_name,
                    row_count=row_count,
                    columns=columns,
                    indexes=indexes,
                    foreign_keys=foreign_keys,
                )
                session.add(db_table)
        session.commit()
    except Exception as e:
        raise RuntimeError(f"Database analysis failed: {e}")

def _get_tables(conn) -> list[str]:
    result = conn.execute(sa.text(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
    ))
    return [row[0] for row in result]

def _get_columns(conn, table_name: str) -> list[dict]:
    result = conn.execute(sa.text(
        "SELECT column_name, data_type, is_nullable, column_default "
        "FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = :t"
    ), {"t": table_name})
    return [{"name": r[0], "type": r[1], "nullable": r[2], "default": r[3]} for r in result]

def _get_indexes(conn, table_name: str) -> list[dict]:
    result = conn.execute(sa.text(
        "SELECT indexname, indexdef FROM pg_indexes WHERE schemaname = 'public' AND tablename = :t"
    ), {"t": table_name})
    return [{"name": r[0], "definition": r[1]} for r in result]

def _get_foreign_keys(conn, table_name: str) -> list[dict]:
    result = conn.execute(sa.text("""
        SELECT kcu.column_name, ccu.table_name AS foreign_table_name, ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = :t
    """), {"t": table_name})
    return [{"column": r[0], "references_table": r[1], "references_column": r[2]} for r in result]

def _get_row_count(conn, table_name: str) -> int:
    try:
        result = conn.execute(sa.text(f'SELECT COUNT(*) FROM "{table_name}"'))
        return result.scalar()
    except Exception:
        return 0
