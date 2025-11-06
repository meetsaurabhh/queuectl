from db import claim_job, mark_completed, schedule_retry
from executor import run_command
import time

job = claim_job()
if not job:
    print("No job available to claim.")
    raise SystemExit(0)

print("Claimed job:", job['id'])
print("Command ->", job['command'])

code, out, err = run_command(job['command'])
print("Exit code:", code)
print("Stdout:", out.strip())
print("Stderr:", err.strip())

if code == 0:
    mark_completed(job['id'])
    print("Marked completed.")
else:
    schedule_retry(job['id'], last_error=(err or out).strip())
    print("Scheduled retry / moved to dead depending on attempts.")
