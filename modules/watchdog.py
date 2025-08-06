# watchdog.py

import subprocess
import time
import psutil
from datetime import datetime
from modules.utils import log_event

# List of processes to monitor (use script names)
MONITORED_SCRIPTS = ["main.py", "data_sources.py"]

def is_running(script_name):
    """Returns True if script is running."""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if any(script_name in part for part in proc.info['cmdline']):
            return True
    return False

def restart_script(script_name):
    """Attempts to restart a script."""
    try:
        subprocess.Popen(["python3", script_name])
        log_event("🔁 Restarted script", {"script": script_name})
    except Exception as e:
        log_event("❌ Failed to restart script", {"script": script_name, "error": str(e)})

def run_watchdog(interval_seconds=60):
    while True:
        for script in MONITORED_SCRIPTS:
            if not is_running(script):
                log_event("❗Script not running, restarting", {"script": script})
                restart_script(script)
        time.sleep(interval_seconds)

if __name__ == "__main__":
    run_watchdog()
