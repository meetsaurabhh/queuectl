import sqlite3, time, uuid
from datetime import datetime

DB_FILE = "queue.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE, timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn

def now_iso(): return datetime.utcnow().isoformat()+"Z"
def gen_id():  return str(uuid.uuid4())

def _ensure_tables():
    conn=get_connection();cur=conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,command TEXT,state TEXT,attempts INTEGER,max_retries INTEGER,run_after INTEGER,created_at TEXT,updated_at TEXT,last_error TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS config(key TEXT PRIMARY KEY,value TEXT)")
    cur.execute("""CREATE TABLE IF NOT EXISTS job_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT,
        attempt INTEGER,
        exit_code INTEGER,
        duration REAL,
        stdout TEXT,
        stderr TEXT,
        created_at TEXT
    )""")
    conn.commit();conn.close()

def init_db(): _ensure_tables();print("Database initialized.")
def add_default_config():
    conn=get_connection();cur=conn.cursor()
    for k,v in {"max_retries":"3","backoff_base":"2"}.items():
        cur.execute("INSERT OR IGNORE INTO config(key,value) VALUES(?,?)",(k,v))
    conn.commit();conn.close()

def get_config(key,default=None):
    conn=get_connection();cur=conn.cursor()
    cur.execute("SELECT value FROM config WHERE key=?",(key,))
    r=cur.fetchone();conn.close();return r["value"] if r else default

def add_job(id,cmd,max_retries=3):
    conn=get_connection();cur=conn.cursor();t=int(time.time());iso=now_iso()
    cur.execute("INSERT INTO jobs VALUES(?,?,?,?,?,?,?,? ,?)",
                (id,cmd,"pending",0,max_retries,t,iso,iso,None))
    conn.commit();conn.close();return id

def list_jobs(state=None,limit=100):
    conn=get_connection();cur=conn.cursor()
    if state: cur.execute("SELECT * FROM jobs WHERE state=? ORDER BY created_at LIMIT ?",(state,limit))
    else:     cur.execute("SELECT * FROM jobs ORDER BY created_at LIMIT ?",(limit,))
    r=cur.fetchall();conn.close();return [dict(x) for x in r]

def get_counts():
    conn=get_connection();cur=conn.cursor()
    cur.execute("SELECT state,COUNT(*) c FROM jobs GROUP BY state");r=cur.fetchall();conn.close()
    c={x['state']:x['c'] for x in r}
    for s in("pending","processing","completed","failed","dead"):c.setdefault(s,0)
    return c

def claim_job():
    now=int(time.time());conn=get_connection();cur=conn.cursor()
    try:
        cur.execute("BEGIN IMMEDIATE")
        cur.execute("SELECT * FROM jobs WHERE state='pending' AND run_after<=? ORDER BY created_at LIMIT 1",(now,))
        r=cur.fetchone()
        if not r: conn.commit();return None
        cur.execute("UPDATE jobs SET state='processing',updated_at=? WHERE id=? AND state='pending'",(now_iso(),r['id']))
        if cur.rowcount!=1: conn.rollback();return None
        conn.commit();return dict(r)
    except: conn.rollback();return None
    finally: conn.close()

def mark_completed(i):
    conn=get_connection();cur=conn.cursor()
    cur.execute("UPDATE jobs SET state='completed',updated_at=? WHERE id=?",(now_iso(),i))
    conn.commit();conn.close()

def move_to_dead(i,e=None):
    conn=get_connection();cur=conn.cursor()
    cur.execute("UPDATE jobs SET state='dead',last_error=?,updated_at=? WHERE id=?",(e,now_iso(),i))
    conn.commit();conn.close()

def schedule_retry(i, last_error=None):
    conn=get_connection();cur=conn.cursor()
    cur.execute("SELECT attempts,max_retries FROM jobs WHERE id=?",(i,));r=cur.fetchone()
    if not r:
        conn.close();return
    attempts = int(r['attempts']) + 1
    max_retries = int(r['max_retries'])
    try:
        backoff_base = float(get_config("backoff_base","2"))
    except:
        backoff_base = 2.0
    if attempts > max_retries:
        cur.execute("UPDATE jobs SET attempts=?,state='dead',last_error=?,updated_at=? WHERE id=?",(attempts,last_error,now_iso(),i))
    else:
        delay = int(backoff_base ** attempts)
        run_after = int(time.time()) + delay
        cur.execute("UPDATE jobs SET attempts=?,state='pending',run_after=?,last_error=?,updated_at=? WHERE id=?",(attempts,run_after,last_error,now_iso(),i))
    conn.commit();conn.close()

def list_dead(limit=50):
    conn=get_connection();cur=conn.cursor()
    cur.execute("SELECT * FROM jobs WHERE state='dead' ORDER BY updated_at DESC LIMIT ?",(limit,))
    r=cur.fetchall();conn.close();return [dict(x) for x in r]

def retry_dead(job_id):
    conn=get_connection();cur=conn.cursor()
    cur.execute("SELECT * FROM jobs WHERE id=? AND state='dead'",(job_id,))
    r=cur.fetchone()
    if not r: conn.close();return False
    cur.execute("UPDATE jobs SET state='pending',attempts=0,last_error=NULL,updated_at=? WHERE id=?",(now_iso(),job_id))
    conn.commit();conn.close();return True

# ---- Job logs ----
def add_job_log(job_id, attempt, exit_code, duration, stdout, stderr):
    conn=get_connection();cur=conn.cursor()
    cur.execute("INSERT INTO job_logs (job_id, attempt, exit_code, duration, stdout, stderr, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (job_id, attempt, exit_code, duration, stdout, stderr, now_iso()))
    conn.commit();conn.close()

def get_job_logs(job_id, limit=50):
    conn=get_connection();cur=conn.cursor()
    cur.execute("SELECT * FROM job_logs WHERE job_id=? ORDER BY id DESC LIMIT ?", (job_id, limit))
    r=cur.fetchall();conn.close();return [dict(x) for x in r]

def get_metrics():
    conn=get_connection();cur=conn.cursor()
    cur.execute("SELECT COUNT(*) as total_runs, AVG(duration) as avg_duration, SUM(CASE WHEN exit_code!=0 THEN 1 ELSE 0 END) as failed_runs FROM job_logs")
    r=cur.fetchone()
    total_runs = r['total_runs'] or 0
    avg_duration = float(r['avg_duration']) if r['avg_duration'] is not None else 0.0
    failed_runs = r['failed_runs'] or 0
    cur.execute("SELECT COUNT(*) as dead_count FROM jobs WHERE state='dead'")
    dead_count = cur.fetchone()['dead_count'] or 0
    conn.close()
    return {
        "total_runs": total_runs,
        "avg_duration": avg_duration,
        "failed_runs": failed_runs,
        "dead_count": dead_count
    }
