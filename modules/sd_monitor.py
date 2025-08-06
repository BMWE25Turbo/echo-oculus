# modules/sd_monitor.py

import shutil
import os
from datetime import datetime
from modules.utils import log_event

def check_sd_usage(threshold_percent=10):
    """Checks SD card usage and logs warning if space is low."""
    try:
        total, used, free = shutil.disk_usage("/")
        percent_free = (free / total) * 100

        log_event("SD card check", {
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
            "percent_free": round(percent_free, 2)
        })

        if percent_free < threshold_percent:
            log_event("⚠️ SD card low on space", {
                "percent_free": round(percent_free, 2)
            })

    except Exception as e:
        log_event("SD card check failed", {"error": str(e)})
