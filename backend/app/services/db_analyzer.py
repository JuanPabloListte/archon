from sqlmodel import Session
from app.models.db import DbTable
import sqlalchemy as sa


def _get_dialect(connection_string: str) -> str:
    cs = connection_string.lower()
    if cs.startswith(("postgresql://", "postgres://")):
        return "postgresql"
    if cs.startswith(("mysql://", "mysql+pymysql://", "mariadb://", "mariadb+pymysql://")):
        return "mysql"
    if cs.startswith("sqlite://"):
        return "sqlite"
    raise RuntimeError(
        f"Unsupported database. Supported: postgresql://, mysql://, sqlite://. Got: {connection_string[:30]}..."
    )


def _make_engine(connection_string: str, dialect: str):
    if dialect == "postgresql":
        return sa.create_engine(
            connection_string,
            connect_args={"options": "-c statement_timeout=10000"},
        )
    if dialect == "mysql":
        # Rewrite mysql:// → mysql+pymysql:// if needed
        cs = connection_string
        if cs.startswith("mysql://"):
            cs = "mysql+pymysql://" + cs[len("mysql://"):]
        elif cs.startswith("mariadb://"):
            cs = "mysql+pymysql://" + cs[len("mariadb://"):]
        return sa.create_engine(cs)
    # sqlite
    return sa.create_engine(connection_string)


# ── Table introspection ────────────────────────────────────────────────────────

def _get_tables(conn, dialect: str) -> list[str]:
    if dialect == "sqlite":
        result = conn.execute(sa.text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ))
        return [row[0] for row in result]
    if dialect == "mysql":
        result = conn.execute(sa.text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = DATABASE() AND table_type = 'BASE TABLE'"
        ))
        return [row[0] for row in result]
    # postgresql
    result = conn.execute(sa.text(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
    ))
    return [row[0] for row in result]


def _get_columns(conn, table_name: str, dialect: str) -> list[dict]:
    if dialect == "sqlite":
        result = conn.execute(sa.text(f'PRAGMA table_info("{table_name}")'))
        # cid, name, type, notnull, dflt_value, pk
        return [
            {"name": r[1], "type": r[2], "nullable": "NO" if r[3] else "YES", "default": r[4]}
            for r in result
        ]
    if dialect == "mysql":
        result = conn.execute(sa.text(
            "SELECT column_name, data_type, is_nullable, column_default "
            "FROM information_schema.columns "
            "WHERE table_schema = DATABASE() AND table_name = :t "
            "ORDER BY ordinal_position"
        ), {"t": table_name})
    else:
        result = conn.execute(sa.text(
            "SELECT column_name, data_type, is_nullable, column_default "
            "FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = :t "
            "ORDER BY ordinal_position"
        ), {"t": table_name})
    return [{"name": r[0], "type": r[1], "nullable": r[2], "default": r[3]} for r in result]


def _get_indexes(conn, table_name: str, dialect: str) -> list[dict]:
    if dialect == "sqlite":
        idx_list = conn.execute(sa.text(f'PRAGMA index_list("{table_name}")')).fetchall()
        indexes = []
        for idx in idx_list:
            idx_name = idx[1]
            info = conn.execute(sa.text(f'PRAGMA index_info("{idx_name}")')).fetchall()
            cols = ", ".join(r[2] for r in info)
            indexes.append({"name": idx_name, "definition": f"INDEX {idx_name} ON {table_name}({cols})"})
        return indexes
    if dialect == "mysql":
        result = conn.execute(sa.text(
            "SELECT DISTINCT index_name, GROUP_CONCAT(column_name ORDER BY seq_in_index) as cols "
            "FROM information_schema.statistics "
            "WHERE table_schema = DATABASE() AND table_name = :t "
            "GROUP BY index_name"
        ), {"t": table_name})
        return [{"name": r[0], "definition": f"INDEX {r[0]} ON {table_name}({r[1]})"} for r in result]
    # postgresql
    result = conn.execute(sa.text(
        "SELECT indexname, indexdef FROM pg_indexes WHERE schemaname = 'public' AND tablename = :t"
    ), {"t": table_name})
    return [{"name": r[0], "definition": r[1]} for r in result]


def _get_foreign_keys(conn, table_name: str, dialect: str) -> list[dict]:
    if dialect == "sqlite":
        result = conn.execute(sa.text(f'PRAGMA foreign_key_list("{table_name}")')).fetchall()
        # id, seq, table, from, to, on_update, on_delete, match
        return [{"column": r[3], "references_table": r[2], "references_column": r[4]} for r in result]
    if dialect == "mysql":
        result = conn.execute(sa.text(
            "SELECT column_name, referenced_table_name, referenced_column_name "
            "FROM information_schema.key_column_usage "
            "WHERE table_schema = DATABASE() AND table_name = :t "
            "AND referenced_table_name IS NOT NULL"
        ), {"t": table_name})
        return [{"column": r[0], "references_table": r[1], "references_column": r[2]} for r in result]
    # postgresql
    result = conn.execute(sa.text("""
        SELECT kcu.column_name, ccu.table_name AS foreign_table_name, ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = :t
    """), {"t": table_name})
    return [{"column": r[0], "references_table": r[1], "references_column": r[2]} for r in result]


def _get_row_count(conn, table_name: str, dialect: str) -> int:
    try:
        quote = "`" if dialect == "mysql" else '"'
        result = conn.execute(sa.text(f"SELECT COUNT(*) FROM {quote}{table_name}{quote}"))
        return result.scalar()
    except Exception:
        return 0


# ── Public entry point ────────────────────────────────────────────────────────

def analyze_database(connection_string: str, project_id: str, session: Session):
    dialect = _get_dialect(connection_string)
    try:
        engine = _make_engine(connection_string, dialect)
        with engine.connect() as conn:
            tables = _get_tables(conn, dialect)
            for table_name in tables:
                columns = _get_columns(conn, table_name, dialect)
                indexes = _get_indexes(conn, table_name, dialect)
                foreign_keys = _get_foreign_keys(conn, table_name, dialect)
                row_count = _get_row_count(conn, table_name, dialect)

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
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Database analysis failed: {e}")
