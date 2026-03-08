import sqlite3
import os
from datetime import datetime

DB_PATH = os.environ.get("MEMORY_DB_PATH", "./memory.db")

# How many past exchanges to store per user
MAX_EXCHANGES = 50

# How many to surface as context on session start
CONTEXT_TURNS = 10


class LongTermMemoryStore:
    def __init__(self):
        self._init_db()

    def _init_db(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS exchanges (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id     TEXT    NOT NULL,
                    user_msg    TEXT    NOT NULL,
                    agent_msg   TEXT    NOT NULL,
                    created_at  TEXT    NOT NULL
                )
            """)
            conn.commit()
            conn.close()
            self._available = True
            print("Long-term memory DB ready ")            
            
            
        except Exception as e:
            print(f"[Memory] DB unavailable: {e}")
            self._available = False
            
    
    
    def append(self, user_id: str, user_msg: str, agent_msg: str):
        if not self._available:
            return
        try:
            conn = sqlite3.connect(DB_PATH)

            # Save the new exchange
            conn.execute(
                """INSERT INTO exchanges
                   (user_id, user_msg, agent_msg, created_at)
                   VALUES (?, ?, ?, ?)""",
                (
                    user_id,
                    user_msg[:1000],    # cap length
                    agent_msg[:2000],
                    datetime.utcnow().isoformat()
                ),
            )

            
            # Keep only the latest
            conn.execute("""
                DELETE FROM exchanges
                WHERE user_id = ? AND id NOT IN (
                    SELECT id FROM exchanges
                    WHERE user_id = ?
                    ORDER BY id DESC
                    LIMIT ?
                )
            """, (user_id, user_id, MAX_EXCHANGES))

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"[Memory] append error: {e}")
            
            
    
    def get_summary(self, user_id: str) -> str:
        if not self._available:
            return ""
        try:
            conn = sqlite3.connect(DB_PATH)
            rows = conn.execute(
                """SELECT user_msg, agent_msg
                   FROM exchanges
                   WHERE user_id = ?
                   ORDER BY id DESC
                   LIMIT ?""",
                (user_id, CONTEXT_TURNS),
            ).fetchall()
            conn.close()

            if not rows:
                return ""

            # Reverse - natural reading order
            lines = []
            for user_msg, agent_msg in reversed(rows):
                lines.append(f"User: {user_msg}")
                lines.append(f"Vera: {agent_msg}")

            return "Previous session context:\n" + "\n".join(lines)

        except Exception as e:
            print(f"[Memory] get_summary error: {e}")
            return ""