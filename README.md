# queuectl

A minimal **background job queue CLI** built with Python — featuring persistent job storage, retry with exponential backoff, and a Dead Letter Queue (DLQ).

---

## 🧭 Overview

`queuectl` is a command-line tool that manages background jobs using worker processes.  
It allows you to enqueue shell commands, automatically retry failed ones, and track job states persistently using SQLite.

### **Core Features**
- Enqueue jobs with shell commands
- Multiple parallel workers
- Automatic retries with exponential backoff
- Configurable max retries and backoff base
- Persistent job storage across restarts (SQLite)
- Dead Letter Queue (DLQ) for permanently failed jobs
- DLQ retry mechanism
- Graceful worker shutdowns

---

## ⚙️ Setup

### **Clone & Setup Environment**

```bash
git clone https://github.com/meetsaurabhh/queuectl.git
cd queuectl
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
