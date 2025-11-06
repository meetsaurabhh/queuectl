import sqlite3
from datetime import datetime
import time
import uuid

DB_FILE = "queue.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY,
        command TEXT NOT NULL,
        state TEXT NOT NULL CHECK(state IN ('pending','processing','completed','failed','dead')),
        attempts INTEGER NOT NULL DEFAULT 0,
        max_retries INTEGER NOT NULL DEFAULT 3,
        run_after INTEGER DEFAULT 0,
        created_at TEXT,
        updated_at TEXT,
        last_error TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS config (
        key TEXT PRIMARY KEY,
        value TEXT
    );
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully at queue.db")

def add_default_config():
    conn = get_connection()
    cur = conn.cursor()
    defaults = {
        "max_retries": "3",
        "backoff_base": "2"
    }
    for key, val in defaults.items():
        cur.execute("INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)", (key, val))
    conn.commit()
    conn.close()
    print("⚙️ Default configuration added.")

def now_iso():
    return datetime.utcnow().isoformat() + "Z"

def gen_id():
    return str(uuid.uuid4())

def add_job(id: str, command: str, max_retries: int = 3):
    """Insert a job into the database."""
    conn = get_connection()
    cur = conn.cursor()
    created = now_iso()
    run_after = int(time.time())  # eligible immediately
    try:
        cur.execute(
            "INSERT INTO jobs (id, command, state, attempts, max_retries, run_after, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (id, command, "pending", 0, max_retries, run_after, created, created)
        )
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.close()
        raise
    conn.close()
    return id

def list_jobs(state: str = None, limit: int = 100):
    conn = get_connection()
    cur = conn.cursor()
    if state:
        cur.execute("SELECT * FROM jobs WHERE state = ? ORDER BY created_at LIMIT ?", (state, limit))
    else:
        cur.execute("SELECT * FROM jobs ORDER BY created_at LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_counts():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT state, COUNT(*) as cnt FROM jobs GROUP BY state")
    rows = cur.fetchall()
    conn.close()
    counts = {r["state"]: r["cnt"] for r in rows}
    # ensure keys exist
    for s in ("pending","processing","completed","failed","dead"):
        counts.setdefault(s, 0)
    return counts
