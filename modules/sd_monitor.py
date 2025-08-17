# modules/sd_monitor.py
import shutil
import subprocess
import argparse
import logging
from datetime import datetime
from modules.utils import log_event


def check_sd_usage(threshold_percent: int = 10, path: str = "/"):
    """Check filesystem usage for `path` and log a warning if free % < threshold."""
    try:
        total, used, free = shutil.disk_usage(path)
        percent_free = (free / total) * 100 if total else 0.0

        log_event("SD card check", {
            "path": path,
            "total_gb": round(total / (1024 ** 3), 2),
            "used_gb": round(used / (1024 ** 3), 2),
            "free_gb": round(free / (1024 ** 3), 2),
            "percent_free": round(percent_free, 2),
        })

        if percent_free < threshold_percent:
            log_event("⚠️ SD card low on space", {
                "path": path,
                "percent_free": round(percent_free, 2),
                "threshold_percent": threshold_percent,
            }, level="WARNING")

        return percent_free
    except Exception as e:
        log_event("SD card check failed", {"error": str(e), "path": path}, level="ERROR")
        return None


# ---- Optional deeper health probes (safe no-ops if tools/dev missing) ----
def _run(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return 1, str(e)


def check_smart(device_hint_nvme: str = "/dev/nvme0", device_hint_smartctl: str = "/dev/nvme0n1"):
    """
    Try to gather NVMe/SMART health. Returns True if any tool worked.
    - nvme-cli:  nvme smart-log /dev/nvme0
    - smartctl:  smartctl -a /dev/nvme0n1
    """
    # nvme-cli (best for NVMe)
    rc, out = _run(["nvme", "smart-log", device_hint_nvme])
    if rc == 0 and out.strip():
        log_event("NVMe smart-log", {"device": device_hint_nvme, "report": out.strip()})
        return True

    # smartctl (fallback)
    rc, out = _run(["smartctl", "-a", device_hint_smartctl])
    if rc == 0 and out.strip():
        log_event("SMART report", {"device": device_hint_smartctl, "report": out.strip()})
        return True

    log_event("SMART check skipped", {
        "reason": "tools or device not available",
        "nvme_cmd": f"nvme smart-log {device_hint_nvme}",
        "smartctl_cmd": f"smartctl -a {device_hint_smartctl}",
    })
    return False


# ---- Standalone entrypoint for systemd timer/service ----
def main():
    parser = argparse.ArgumentParser(description="Echo Oculus SD/SSD health check")
    parser.add_argument("--path", default="/", help="Filesystem path or mount to check (default: /)")
    parser.add_argument("--threshold", type=int, default=10, help="Warn if free %% < threshold (default: 10)")
    parser.add_argument("--full", action="store_true", help="Also run NVMe/SMART probes (safe no-op if unavailable)")
    parser.add_argument("--nvme", default="/dev/nvme0", help="nvme-cli device (default: /dev/nvme0)")
    parser.add_argument("--smartdev", default="/dev/nvme0n1", help="smartctl device (default: /dev/nvme0n1)")
    args = parser.parse_args()

    # Minimal console logger so running standalone prints something even before main logging config
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    log_event("sd_monitor standalone start", {
        "path": args.path,
        "threshold": args.threshold,
        "full": args.full
    })

    check_sd_usage(threshold_percent=args.threshold, path=args.path)
    if args.full:
        check_smart(device_hint_nvme=args.nvme, device_hint_smartctl=args.smartdev)


if __name__ == "__main__":
    main()
