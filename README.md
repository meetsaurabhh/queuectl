# QueueCTL - Background Job Queue CLI System

QueueCTL is a minimal, production-grade **CLI-based background job queue system** built in **Python**.  
It manages background jobs with worker processes, supports automatic retries using exponential backoff, and maintains a **Dead Letter Queue (DLQ)** for permanently failed jobs.  

---

## Usage Examples

### 1. Enqueue a new job
python queuectl.py enqueue --command "echo Hello World"

### 2. Start worker(s)
python queuectl.py worker start --count 2

### 3. Check job list or status
python queuectl.py list --state pending
python queuectl.py status

### 4. Handle Dead Letter Queue (DLQ)
python queuectl.py dlq list
python queuectl.py dlq retry <job-id>

### 5. View metrics
python queuectl.py stats

---

## Job Lifecycle

| State | Description |
|-------|-------------|
| pending | Waiting to be picked up by a worker |
| processing | Currently being executed |
| completed | Successfully executed |
| failed | Failed, but retryable |
| dead | Permanently failed (moved to DLQ) |

---

## Architecture Overview

### Components

| File | Responsibility |
|------|----------------|
| queuectl.py | CLI entrypoint & command routing |
| db.py | Database models and persistence layer |
| worker.py | Worker loop, job claiming & retry logic |
| executor.py | Executes shell commands safely |
| queue.db | Persistent SQLite storage for jobs & logs |

### Lifecycle Diagram
flowchart TD
  A[Enqueue Job] --> B[Job Stored in SQLite]
  B --> C[Worker Picks Pending Job]
  C --> D{Command Success?}
  D -->|Yes| E[Mark Completed]
  D -->|No| F[Retry with Backoff]
  F -->|Exceeded Max Retries| G[Move to Dead Letter Queue]

---

## System Features

✅ Persistent storage in SQLite  
✅ Multiple workers (parallel processing)  
✅ Exponential backoff retries  
✅ Dead Letter Queue (DLQ) management  
✅ Configurable retry limits and backoff base  
✅ Graceful worker shutdown  
✅ Job output logging (stdout/stderr per run)  
✅ Metrics and execution statistics  

---

## Metrics Command

You can monitor runtime statistics:
python queuectl.py stats

Example output:
Metrics:
  total_runs: 5
  avg_duration (s): 0.015
  failed_runs: 1
  dead_jobs: 0

---

## Job Logs

Every job attempt logs:
- stdout  
- stderr  
- exit_code  
- duration  
- timestamp  

Example (Python usage):
from db import get_job_logs
logs = get_job_logs("<job-id>")
for log in logs:
    print(log)

Sample output:
{'job_id': '123...', 'attempt': 1, 'exit_code': 0, 'stdout': 'Hello World\n', 'duration': 0.02, 'created_at': '2025-11-07T12:34:56Z'}

---

## Bonus Features Implemented

| Feature | Description |
|----------|-------------|
| Job Output Logging | Stores command output (stdout/stderr, duration, exit code) for every attempt |
| Metrics Command (stats) | Summarizes job performance statistics |
| Persistent Queue | Jobs and logs persist after restart |
| Graceful Worker Stop | Ensures current job finishes before exit |

---

## Testing Scenarios

| Test | Command | Expected Behavior |
|------|----------|------------------|
| Enqueue job | python queuectl.py enqueue --command "echo test" | Job added with pending state |
| Start worker | python queuectl.py worker start --count 2 | Workers pick up jobs & execute |
| Invalid command | python queuectl.py enqueue --command "bad_command" | Retries → DLQ after failure |
| Retry DLQ job | python queuectl.py dlq retry <job-id> | Job moves from dead → pending |
| Metrics | python queuectl.py stats | Displays total runs and averages |


---

## Configuration Management

You can adjust retry settings directly in the config table:
sqlite3 queue.db "UPDATE config SET value='5' WHERE key='max_retries';"

Default values:
| Key | Value |
|------|-------|
| max_retries | 3 |
| backoff_base | 2 |

---

## Quick End-to-End Test

python queuectl.py initdb
python queuectl.py enqueue --command "echo quick-test"
python queuectl.py worker start --count 1
python queuectl.py status
python queuectl.py stats

---

## Demo Video

Demo link:
[Watch demo on Google Drive](https://drive.google.com/file/d/1N01vMHcGAR0qbDbpaDUkqf4dSG_PElET/view?usp=sharing)

---

## Checklist

- [x] All required commands functional  
- [x] Persistent job storage  
- [x] Retry + exponential backoff  
- [x] DLQ operational  
- [x] Multiple workers supported  
- [x] Logging and metrics added  
- [x] Clean CLI with documentation  
- [x] Tested end-to-end  

---

### Author
**Saurabh Singh**  
GitHub: [@meetsaurabhh](https://github.com/meetsaurabhh)
