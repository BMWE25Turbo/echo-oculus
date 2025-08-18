#!/usr/bin/env python3
import os, sys, time, gzip, shutil
from datetime import datetime, timedelta

ROOT = "/var/log/echo-oculus"
ARCH = os.path.join(ROOT, "archive")
RETENTION_DAYS = int(os.environ.get("EO_LOG_RETENTION_DAYS", "180"))

def purge():
    if not os.path.isdir(ARCH): return
    cutoff = datetime.utcnow() - timedelta(days=RETENTION_DAYS)
    for p in os.listdir(ARCH):
        full = os.path.join(ARCH, p)
        try:
            m = datetime.utcfromtimestamp(os.path.getmtime(full))
            if m < cutoff:
                os.remove(full)
        except Exception:
            pass

if __name__ == "__main__":
    purge()
