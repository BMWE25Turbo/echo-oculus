# modules/sd_monitor.py
from __future__ import annotations
import shutil
import subprocess
import argparse
import logging
import json
import re
from typing import Optional, Dict, Any

from modules.utils import log_event


# -----------------------------
# Filesystem usage
# -----------------------------
def check_sd_usage(threshold_percent: int = 10, path: str = "/") -> Optional[Dict[str, Any]]:
    """
    Check filesystem usage for `path`, log a row, and warn if free% < threshold.
    Returns a dict with totals (GB) and percent_free, or None on error.
    """
    try:
        total, used, free = shutil.disk_usage(path)
        percent_free = (free / total) * 100 if total else 0.0
        payload = {
            "path": path,
            "total_gb": round(total / (1024 ** 3), 2),
            "used_gb": round(used / (1024 ** 3), 2),
            "free_gb": round(free / (1024 ** 3), 2),
            "percent_free": round(percent_free, 2),
        }

        # Informational row
        log_event("SD card check", payload)

        # Warning if under threshold
        if percent_free < threshold_percent:
            warn = dict(payload)
            warn["threshold_percent"] = threshold_percent
            log_event("⚠️ SD card low on space", warn, level="WARNING")

        return payload
    except Exception as e:
        log_event("SD card check failed", {"error": str(e), "path": path}, level="ERROR")
        return None


# -----------------------------
# SMART / NVMe health
# -----------------------------
def _run(cmd: list[str]) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return 1, str(e)


_NVME_TEMP_RE = re.compile(r"temperature\s*:\s*([0-9]+)")
_NVME_MEDIA_ERR_RE = re.compile(r"media_errors\s*:\s*([0-9]+)")
_SMART_TEMP_RE = re.compile(r"Temperature_Celsius.*?(\d+)\s*$", re.IGNORECASE | re.MULTILINE)
_SMART_ERR_RE = re.compile(r"Media and Data Integrity Errors:\s*([0-9]+)", re.IGNORECASE)


def _extract_nvme_fields(text: str) -> Dict[str, Any]:
    fields: Dict[str, Any] = {}
    m = _NVME_TEMP_RE.search(text)
    if m: fields["nvme_temp_c"] = int(m.group(1))
    m = _NVME_MEDIA_ERR_RE.search(text)
    if m: fields["nvme_media_errors"] = int(m.group(1))
    return fields


def _extract_smart_fields(text: str) -> Dict[str, Any]:
    fields: Dict[str, Any] = {}
    m = _SMART_TEMP_RE.search(text)
    if m: fields["smart_temp_c"] = int(m.group(1))
    m = _SMART_ERR_RE.search(text)
    if m: fields["smart_media_errors"] = int(m.group(1))
    return fields


def check_smart(
    device_hint_nvme: str = "/dev/nvme0",
    device_hint_smartctl: str = "/dev/nvme0n1",
) -> bool:
    """
    Try to gather NVMe/SMART health. Returns True if any tool worked.
    - nvme-cli:  nvme smart-log /dev/nvme0
    - smartctl:  smartctl -a /dev/nvme0n1
    Logs the full raw report, plus a few parsed fields (temp, media errors) if present.
    """
    # nvme-cli (preferred for NVMe devices)
    rc, out = _run(["nvme", "smart-log", device_hint_nvme])
    if rc == 0 and out.strip():
        fields = _extract_nvme_fields(out)
        log_event("NVMe smart-log", {"device": device_hint_nvme, **fields, "report": out.strip()})
        return True

    # smartctl fallback (works for SATA/NVMe if smartmontools supports it)
    rc, out = _run(["smartctl", "-a", device_hint_smartctl])
    if rc == 0 and out.strip():
        fields = _extract_smart_fields(out)
        log_event("SMART report", {"device": device_hint_smartctl, **fields, "report": out.strip()})
        return True

    # Neither tool worked
    log_event(
        "SMART check skipped",
        {
            "reason": "tools or device not available",
            "nvme_cmd": f"nvme smart-log {device_hint_nvme}",
            "smartctl_cmd": f"smartctl -a {device_hint_smartctl}",
        },
    )
    return False


# -----------------------------
# CLI entrypoint (systemd timer friendly)
# -----------------------------
def main():
    parser = argparse.ArgumentParser(description="Echo Oculus SD/SSD health check")
    parser.add_argument("--path", default="/", help="Filesystem path/mount to check (default: /)")
    parser.add_argument("--threshold", type=int, default=10, help="Warn if free %% < threshold (default: 10)")
    parser.add_argument("--full", action="store_true", help="Also run NVMe/SMART probes (safe no-op if unavailable)")
    parser.add_argument("--nvme", default="/dev/nvme0", help="nvme-cli device (default: /dev/nvme0)")
    parser.add_argument("--smartdev", default="/dev/nvme0n1", help="smartctl device (default: /dev/nvme0n1)")
    parser.add_argument("--json", action="store_true", help="Print a compact JSON summary to stdout")
    args = parser.parse_args()

    # Minimal console logger so standalone runs show output even before main logging config
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    log_event(
        "sd_monitor standalone start",
        {"path": args.path, "threshold": args.threshold, "full": args.full},
    )

    fs_payload = check_sd_usage(threshold_percent=args.threshold, path=args.path)
    smart_ok = False
    if args.full:
        smart_ok = check_smart(device_hint_nvme=args.nvme, device_hint_smartctl=args.smartdev)

    if args.json:
        print(json.dumps({"fs": fs_payload, "smart_checked": bool(args.full), "smart_ok": smart_ok}, separators=(",", ":")))


if __name__ == "__main__":
    main()
