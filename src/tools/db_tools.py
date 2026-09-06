import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    """Docker'daki PostgreSQL'e bağlantı açar."""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5433"),
        dbname=os.getenv("POSTGRES_DB", "enterprise_db"),
        user=os.getenv("POSTGRES_USER", "admin"),
        password=os.getenv("POSTGRES_PASSWORD", "password123")
    )

def get_schema_summary() -> str:
    query = """
    SELECT table_name, column_name, data_type
    FROM information_schema.columns
    WHERE table_schema = 'public'
    ORDER BY table_name, ordinal_position;
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            rows = cur.fetchall()

    schema_map = {}
    for r in rows:
        tbl = r["table_name"]
        schema_map.setdefault(tbl, []).append(f"{r['column_name']} ({r['data_type']})")

    lines = []
    for tbl, cols in schema_map.items():
        lines.append(f"Tablo: {tbl}\nKolonlar: {', '.join(cols)}")
    return "\n\n".join(lines)


def execute_sql_query(query: str) -> list[dict]:
    """Üretilen SQL SELECT sorgusunu veritabanında çalıştırıp satırları döndürür."""
    cleaned_query = query.strip().rstrip(";")

    # Güvenlik Kontrolü: Yalnızca SELECT izinli
    if not cleaned_query.upper().startswith("SELECT"):
        raise ValueError("Güvenlik ihlali: Sadece SELECT sorguları çalıştırılabilir.")

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(cleaned_query)
            return [dict(row) for row in cur.fetchall()]


if __name__ == "__main__":
    print("--- POSTGRESQL ŞEMASI ÇEKİLİYOR ---")
    sema = get_schema_summary()
    print(sema)