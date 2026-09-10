import re

FORBIDDEN_KEYWORDS = [
    r"\bDROP\b",
    r"\bDELETE\b",
    r"\bUPDATE\b",
    r"\bINSERT\b",
    r"\bALTER\b",
    r"\bTRUNCATE\b",
    r"\bCREATE\b",
    r"\bGRANT\b",
    r"\bREVOKE\b"
]

class SQLSecurityError(Exception):
    pass

def validate_and_sanitize_sql(query: str) -> str:
    if not query:
        raise SQLSecurityError("Empty SQL query cannot be executed.")

    clean_sql = query.replace("```sql", "").replace("```", "").strip()


    statements = [s.strip() for s in clean_sql.split(";") if s.strip()]
    if len(statements) > 1:
        raise SQLSecurityError("Security violation: Multiple SQL statements (multi-statement) are not allowed.")

    single_query = statements[0]

    # Only SELECT statements are allowed, including WITH queries containing CTEs
    normalized_query = single_query.strip().upper()
    if not (normalized_query.startswith("SELECT") or normalized_query.startswith("WITH")):
        raise SQLSecurityError("Security violation: Only SELECT or WITH (CTE) queries are allowed.")

    #  (Case-insensitive regex)
    for pattern in FORBIDDEN_KEYWORDS:
        if re.search(pattern, single_query, re.IGNORECASE):
            raise SQLSecurityError(f"Security violation: Forbidden keyword detected -> {pattern}")

    return single_query