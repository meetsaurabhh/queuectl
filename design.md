# QueueCTL — Architecture & Design

## Purpose
QueueCTL is a lightweight CLI-based background job queue system built in Python.  
It supports durable job storage, multiple worker processes, exponential backoff retries, and a Dead Letter Queue (DLQ) for permanently failed jobs.

---

## High-Level Architecture
[CLI] <--> [SQLite DB (queue.db)] <--> [Worker Processes]
   ^                                       |
   |-- enqueue, list, status, dlq, stats --|

- CLI (`queuectl.py`) is the main interface.
- Persistent state stored in `queue.db` (SQLite).
- Workers (`worker.py`) claim jobs, execute them via `executor.py`, and update DB state.
- Logs and metrics stored in the `job_logs` table.

---

## Components

### queuectl.py
- CLI entrypoint using argparse.
- Commands: initdb, enqueue, list, status, worker start/stop, dlq list/retry, stats.
- Routes commands to corresponding handlers.

### db.py
- Handles all SQLite operations.
- Tables:
  - jobs(id, command, state, attempts, max_retries, run_after, created_at, updated_at, last_error)
  - config(key, value)
  - job_logs(id, job_id, attempt, exit_code, duration, stdout, stderr, created_at)
- Functions:
  - init_db, add_job, list_jobs, claim_job, mark_completed, schedule_retry, move_to_dead
  - list_dead, retry_dead, add_job_log, get_metrics
- claim_job() uses transactions with BEGIN IMMEDIATE for atomic job claiming.

### worker.py
- Manages multiple worker processes.
- Worker loop:
  1. Claim a pending job (run_after <= now)
  2. Execute command via executor.run_command()
  3. Record job log and duration
  4. Mark completed or schedule retry
  5. Move to DLQ if max retries exceeded
- Handles graceful shutdown with a shared stop flag and signal interrupts.

### executor.py
- Runs shell commands with subprocess.run(shell=True, capture_output=True, text=True)
- Returns (exit_code, stdout, stderr)

---

## Data Model (Jobs)

Example job record:
{
  "id": "uuid",
  "command": "echo hi",
  "state": "pending|processing|completed|failed|dead",
  "attempts": 0,
  "max_retries": 3,
  "run_after": 1699999999,
  "created_at": "2025-11-07T12:00:00Z",
  "updated_at": "2025-11-07T12:00:00Z",
  "last_error": "stderr text"
}

The job_logs table captures each execution attempt with duration, stdout, stderr, and timestamp.

---

## Concurrency & Correctness

- Atomic Claiming: claim_job() selects one pending job inside BEGIN IMMEDIATE, marks it as processing.
- Short Critical Section: Transaction only covers claiming; execution happens outside.
- Backoff Calculation: run_after = now + int(base ** attempts)
- Graceful Shutdown: Workers finish current job on Ctrl+C before exiting.

---

## Persistence & Durability

- SQLite ensures job persistence across restarts.
- Pending jobs are re-claimable after system restarts.
- If a worker crashes mid-job, the job may remain processing (manual reset needed).
- queue.db acts as the persistent message queue.

---

## Retry & DLQ Behavior

- On command failure:
  - attempts += 1
  - run_after updated using exponential backoff (2^attempts)
- If attempts > max_retries:
  - state set to dead
  - job moved to DLQ
- Users can retry dead jobs via:
  python queuectl.py dlq retry <job-id>

---

## Metrics & Logging

- job_logs table stores:
  - job_id, attempt, exit_code, stdout, stderr, duration, created_at
- stats command aggregates:
  - total_runs
  - avg_duration
  - failed_runs
  - dead_jobs

---

## Failure Modes

| Failure | Effect | Mitigation |
|----------|---------|-------------|
| DB locked | Temporary retry delay | Keep short transactions |
| Worker crash | Job stuck in processing | Manual reset or timeout policy |
| Invalid command | Job fails and retries | Exponential backoff, DLQ |
| Shell injection | Potential risk | Only trusted input allowed |

---

## Configuration

Stored in config table:
| Key | Value |
|-----|--------|
| max_retries | 3 |
| backoff_base | 2 |


---

## Extensibility (Future Enhancements)
- Job timeout using subprocess.run(timeout=N)
- Scheduled/delayed jobs (future run_at timestamps)
- Priority queues (add priority column)
- Web dashboard for monitoring jobs and metrics
- Requeue stale processing jobs after timeout
- PostgreSQL support for distributed use

---

## Testing & Verification
Core validation steps:
1. enqueue → worker → status
2. failing command → retry → DLQ
3. dlq retry → worker success
4. metrics and logs verified via stats and get_job_logs()

---

## Deployment Notes
- Designed for single-node environments.
- Run workers with process managers like tmux or systemd.
- For multi-node scale, migrate to PostgreSQL and externalize locking.

---

## Summary
QueueCTL provides:
- Simple and reliable background job execution
- Persistent SQLite-backed queue
- Automatic retries and DLQ
- CLI-based control and monitoring
- Extensible architecture suitable for further scaling
