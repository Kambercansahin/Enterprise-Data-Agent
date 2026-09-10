import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from src.tools.sql_guardrails import validate_and_sanitize_sql
load_dotenv()

def get_connection():
    """Opens a connection to the PostgreSQL database running in Docker."""
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

def execute_sql_query(query: str, timeout_ms: int = 3000) -> list[dict]:
    # 1. Validate and sanitize the query using guardrails
    #    (forbidden keyword and multi-statement checks)
    sanitized_query = validate_and_sanitize_sql(query)

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 2. Resource protection: PostgreSQL cancels the query if it exceeds 3 seconds
            cur.execute(f"SET statement_timeout = '{timeout_ms}ms';")
            cur.execute("SET work_mem = '16MB';")

            # 3. Execute the sanitized query safely
            cur.execute(sanitized_query)
            return [dict(row) for row in cur.fetchall()]

if __name__ == "__main__":
    print("--- 1. FETCHING SCHEMA ---")
    schema = get_schema_summary()
    print(schema[:300] + "...\n")

    print("--- 2. SECURITY TEST (DROP QUERY) ---")
    try:
        execute_sql_query("DROP TABLE orders;")
        print("FAILED: Malicious query was executed!")
    except Exception as e:
        print(f"SUCCESS: Security filter was triggered -> {e}")

    print("\n--- 3. VALID SELECT QUERY TEST ---")
    try:
        data = execute_sql_query("SELECT order_id, order_status FROM orders LIMIT 2;")
        print("Returned Data:", data)
    except Exception as e:
        print(f"Error: {e}")