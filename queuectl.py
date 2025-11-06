#!/usr/bin/env python3
import argparse,sys
from db import *
from worker import start_workers

def cmd_hello(): print("queuectl ready.")
def cmd_initdb(): init_db();add_default_config()

def cmd_enqueue(a):
    i=a.id or gen_id()
    if not a.command: sys.exit("Missing --command")
    add_job(i,a.command,a.max_retries);print("Enqueued",i)

def cmd_list(a):
    r=list_jobs(a.state)
    if not r: print("No jobs.");return
    for x in r: print(f"{x['id']} | {x['state']} | {x['command']}")

def cmd_status(_):
    c=get_counts();[print(f"{k}: {v}") for k,v in c.items()]

def cmd_worker(a):
    if a.action=="start": start_workers(a.count)
    else: print("Stop with Ctrl+C")

def cmd_dlq(a):
    if a.action=="list":
        r=list_dead()
        if not r: print("No dead jobs.");return
        for x in r: print(f"{x['id']} | {x['last_error']}")
    elif a.action=="retry":
        ok=retry_dead(a.job_id)
        print("Retried" if ok else "Job not found or not dead.")

def main():
    p=argparse.ArgumentParser(prog='queuectl');sp=p.add_subparsers(dest='cmd')
    sp.add_parser('hello')
    sp.add_parser('initdb')

    e=sp.add_parser('enqueue');e.add_argument('--id');e.add_argument('--command');e.add_argument('--max-retries',type=int,default=3)
    l=sp.add_parser('list');l.add_argument('--state')
    sp.add_parser('status')
    w=sp.add_parser('worker');w.add_argument('action',choices=['start','stop']);w.add_argument('--count',type=int,default=1)
    d=sp.add_parser('dlq');d.add_argument('action',choices=['list','retry']);d.add_argument('job_id',nargs='?')

    a=p.parse_args()
    if   a.cmd=='hello':cmd_hello()
    elif a.cmd=='initdb':cmd_initdb()
    elif a.cmd=='enqueue':cmd_enqueue(a)
    elif a.cmd=='list':cmd_list(a)
    elif a.cmd=='status':cmd_status(a)
    elif a.cmd=='worker':cmd_worker(a)
    elif a.cmd=='dlq':cmd_dlq(a)
    else:p.print_help()

if __name__=="__main__": main()
