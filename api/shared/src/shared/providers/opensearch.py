def sanitize_query(q: str) -> str | None:
    return q.replace("\\", "\\\\").replace('"', '\\"') if (q := q.strip()) else None
