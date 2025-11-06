#!/usr/bin/env python3
import argparse
import sys
from db import (
    init_db,
    add_default_config,
    add_job,
    gen_id,
    list_jobs,
    get_counts,
    list_dead,
    retry_dead,
    get_metrics,
)
from worker import start_workers

def cmd_initdb():
    init_db()
    add_default_config()

def cmd_enqueue(a):
    job_id = a.id or gen_id()
    if not a.command:
        sys.exit("Missing --command")
    add_job(job_id, a.command, a.max_retries)
    print(job_id)

def cmd_list(a):
    rows = list_jobs(a.state)
    if not rows:
        print("No jobs.")
        return
    for r in rows:
        print(f"{r['id']} | {r['state']} | {r['command']}")

def cmd_status(_):
    counts = get_counts()
    for k in ("pending","processing","completed","failed","dead"):
        print(f"{k}: {counts.get(k,0)}")

def cmd_worker(a):
    if a.action == "start":
        print(f"Starting {a.count} workers...")
        start_workers(a.count)
    else:
        print("Stop workers with Ctrl+C")

def cmd_dlq(a):
    if a.action == "list":
        rows = list_dead()
        if not rows:
            print("No dead jobs.")
            return
        for r in rows:
            print(f"{r['id']} | {r.get('last_error')}")
    elif a.action == "retry":
        if not a.job_id:
            print("Provide a job id to retry.")
            return
        ok = retry_dead(a.job_id)
        print("Retried" if ok else "Job not found or not dead.")

def cmd_stats(_):
    m = get_metrics()
    print("Metrics:")
    print(f"  total_runs: {m['total_runs']}")
    print(f"  avg_duration (s): {m['avg_duration']:.3f}")
    print(f"  failed_runs: {m['failed_runs']}")
    print(f"  dead_jobs: {m['dead_count']}")

def main():
    p = argparse.ArgumentParser(prog='queuectl')
    sp = p.add_subparsers(dest='cmd')

    sp.add_parser('initdb')

    e = sp.add_parser('enqueue'); e.add_argument('--id'); e.add_argument('--command'); e.add_argument('--max-retries', type=int, default=3)
    l = sp.add_parser('list'); l.add_argument('--state')
    sp.add_parser('status')
    w = sp.add_parser('worker'); w.add_argument('action', choices=['start','stop']); w.add_argument('--count', type=int, default=1)
    d = sp.add_parser('dlq'); d.add_argument('action', choices=['list','retry']); d.add_argument('job_id', nargs='?')
    sp.add_parser('stats')

    a = p.parse_args()
    if a.cmd == 'initdb': cmd_initdb()
    elif a.cmd == 'enqueue': cmd_enqueue(a)
    elif a.cmd == 'list': cmd_list(a)
    elif a.cmd == 'status': cmd_status(a)
    elif a.cmd == 'worker': cmd_worker(a)
    elif a.cmd == 'dlq': cmd_dlq(a)
    elif a.cmd == 'stats': cmd_stats(a)
    else: p.print_help()

if __name__ == "__main__":
    main()
