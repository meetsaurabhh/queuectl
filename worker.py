import multiprocessing as mp
import signal
import time
from db import claim_job, mark_completed, schedule_retry, add_job_log
from executor import run_command


stop_flag = mp.Value('b', False)

def worker_loop(worker_id: int):
    print(f"Worker {worker_id} started.")
    while not stop_flag.value:
        job = claim_job()
        if not job:
            time.sleep(1)
            continue
        print(f"[Worker {worker_id}] Claimed job {job['id']} -> {job['command']}")
        start = time.time()
        code, out, err = run_command(job['command'])
        duration = time.time() - start
        attempt = int(job.get('attempts', 0)) + 1
        add_job_log(job['id'], attempt, code, duration, out, err)
        if code == 0:
            mark_completed(job['id'])
            print(f"[Worker {worker_id}] Completed {job['id']}")
        else:
            schedule_retry(job['id'], last_error=(err or out).strip())
            print(f"[Worker {worker_id}] Failed {job['id']} (code {code})")
    print(f"Worker {worker_id} exiting.")

def start_workers(count: int):
    processes = []
    for i in range(count):
        p = mp.Process(target=worker_loop, args=(i+1,))
        p.start()
        processes.append(p)

    def handle_sigterm(signum, frame):
        print("Stopping workers...")
        stop_flag.value = True

    signal.signal(signal.SIGINT, handle_sigterm)
    signal.signal(signal.SIGTERM, handle_sigterm)

    for p in processes:
        p.join()
    print("All workers stopped.")
