import sqlite3
from datetime import datetime

DB_FILE = "queries.db"


class QueryLogger:
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        self._create_table()

    def _create_table(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            username TEXT,
            role TEXT,
            query TEXT,
            route TEXT,
            answer TEXT,
            sources TEXT,
            guardrail INTEGER
        )
        """)
        self.conn.commit()

    def log(self, username, role, query, route, answer, sources, guardrail):
        self.conn.execute("""
        INSERT INTO queries (timestamp, username, role, query, route, answer, sources, guardrail)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.utcnow().isoformat(),
            username,
            role,
            query,
            route,
            answer,
            ",".join(sources),
            int(bool(guardrail))
        ))
        self.conn.commit()