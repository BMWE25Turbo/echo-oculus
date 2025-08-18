# watchdog.py
from __future__ import annotations
import subprocess
import time
from datetime import datetime
from typing import Iterable

try:
    import psutil  # optional; we also have a pgrep fallback
except Exception:
    psutil = None  # type: ignore

from modules.utils import log_event

# You can monitor the systemd service **or** fallback to scripts.
MONITORED_SERVICES: list[str] = ["echo-oculus.service"]  # set empty [] if you don’t use systemd
MONITORED_SCRIPTS:  list[str] = ["main.py"]              # used only if services list is empty

CHECK_INTERVAL_S = 30

def _service_is_active(unit: str) -> bool:
    try:
        r = subprocess.run(["systemctl", "is-active", "--quiet", unit])
        return r.returncode == 0
    except Exception:
        return False

def _restart_service(unit: str) -> None:
    try:
        subprocess.run(["systemctl", "restart", unit], check=False)
        log_event("🔁 Restarted service", {"service": unit})
    except Exception as e:
        log_event("❌ Failed to restart service", {"service": unit, "error": str(e)}, level="ERROR")

def _script_is_running(name: str) -> bool:
    # Prefer psutil, fallback to pgrep
    if psutil:
        for p in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                cmd = " ".join(p.info.get("cmdline") or [])
                if name in cmd:
                    return True
            except Exception:
                continue
        return False
    # pgrep fallback
    try:
        r = subprocess.run(["pgrep", "-f", name], stdout=subprocess.DEVNULL)
        return r.returncode == 0
    except Exception:
        return False

def _restart_script(name: str) -> None:
    try:
        subprocess.Popen(["python3", name])
        log_event("🔁 Restarted script", {"script": name})
    except Exception as e:
        log_event("❌ Failed to restart script", {"script": name, "error": str(e)}, level="ERROR")

def _check_services(units: Iterable[str]) -> None:
    for u in units:
        if not _service_is_active(u):
            log_event("❗Service not active, restarting", {"service": u}, level="WARNING")
            _restart_service(u)

def _check_scripts(names: Iterable[str]) -> None:
    for s in names:
        if not _script_is_running(s):
            log_event("❗Script not running, restarting", {"script": s}, level="WARNING")
            _restart_script(s)

def run_watchdog(interval_seconds: int = CHECK_INTERVAL_S) -> None:
    log_event("Watchdog started", {
        "services": MONITORED_SERVICES,
        "scripts": MONITORED_SCRIPTS if not MONITORED_SERVICES else [],
        "interval_s": interval_seconds
    })
    while True:
        if MONITORED_SERVICES:
            _check_services(MONITORED_SERVICES)
        else:
            _check_scripts(MONITORED_SCRIPTS)
        time.sleep(interval_seconds)

if __name__ == "__main__":
    run_watchdog()
