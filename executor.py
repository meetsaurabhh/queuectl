import subprocess
from typing import Tuple

def run_command(command: str, timeout: int = None) -> Tuple[int, str, str]:
    """
    Execute shell command and return (exit_code, stdout, stderr).
    Uses shell=True so commands like "echo hi" or "sleep 1" work.
    """
    try:
        completed = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
        return completed.returncode, completed.stdout, completed.stderr
    except subprocess.TimeoutExpired as e:
        return 124, "", f"TimeoutExpired: {e}"
    except Exception as e:
        return 1, "", f"Exception: {e}"
