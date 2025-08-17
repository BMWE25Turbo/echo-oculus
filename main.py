import logging
import time
import os
import gzip
import shutil
from glob import glob
from datetime import datetime, timedelta

from modules.alert_engine import AlertEngine
from modules.data_sources import DataSources
from modules.gps_logger import GPSLogger
from modules.sd_monitor import check_sd_usage  # ✅ SD check
from modules.utils import load_config

# ---- Optional: audio test (Phase 1.5 opt path) ----
from modules.audio_transcriber import transcribe_scanner_audio  # ✅ Audio test import


# ------------------------------
# Logging setup (Phase 1.5)
# ------------------------------
def _ensure_dir(p: str):
    if p and not os.path.isdir(p):
        os.makedirs(p, exist_ok=True)

def _configure_logging(cfg: dict):
    """
    Configure root logger with console + timed rotating file.
    Rotation: midnight; Archives: gzipped into archive_dir; Retention purge by days.
    """
    logger_cfg = (cfg.get("echo_oculus", {}) or {}).get("logger", {}) or {}
    fmt = logger_cfg.get("format", "verbose")
    console_on = bool(logger_cfg.get("console", True))

    root_dir = logger_cfg.get("root_dir", "/var/log/echo-oculus")
    archive_dir = logger_cfg.get("archive_dir", os.path.join(root_dir, "archive"))
    log_file = logger_cfg.get("file", "echo-oculus.log")
    rotate_when = logger_cfg.get("rotate_when", "midnight")
    backup_count = int(logger_cfg.get("rotate_backup_count", 14))
    compress_archives = bool(logger_cfg.get("compress_archives", True))
    retention_days = int(logger_cfg.get("log_retention_days", 180))

    _ensure_dir(root_dir)
    _ensure_dir(archive_dir)

    # Formatter
    if fmt == "json":
        try:
            from python_json_logger import jsonlogger
            formatter = jsonlogger.JsonFormatter(
                "%(asctime)s %(levelname)s %(name)s %(message)s"
            )
        except Exception:
            formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    elif fmt == "minimal":
        formatter = logging.Formatter("%(levelname)s: %(message)s")
    else:  # verbose (default)
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    # Root logger
    log = logging.getLogger()
    log.setLevel(logging.INFO)
    # Clear existing handlers if re-running in dev
    for h in list(log.handlers):
        log.removeHandler(h)

    # Console handler
    if console_on:
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        log.addHandler(ch)

    # Timed rotating file handler
    from logging.handlers import TimedRotatingFileHandler
    fh_path = os.path.join(root_dir, log_file)
    fh = TimedRotatingFileHandler(
        fh_path, when=rotate_when, backupCount=backup_count, encoding="utf-8", utc=True
    )
    fh.setFormatter(formatter)
    log.addHandler(fh)

    # Attach simple maintenance info to logger for later housekeeping
    log._eo_log = {
        "root_dir": root_dir,
        "archive_dir": archive_dir,
        "log_file": fh_path,
        "compress_archives": compress_archives,
        "retention_days": retention_days,
    }
    logging.getLogger(__name__).info(
        "Logging to %s, rotate=%s, keep=%d, archive=%s (compress=%s, retention=%dd)",
        fh_path, rotate_when, backup_count, archive_dir, compress_archives, retention_days
    )

def _log_maintenance():
    """
    Move previous rotations to archive/, gzip them (if enabled),
    and purge archives older than retention_days.
    Runs quickly; safe to call every ~10 minutes.
    """
    log = logging.getLogger()
    meta = getattr(log, "_eo_log", None)
    if not meta:
        return
    root_dir = meta["root_dir"]
    archive_dir = meta["archive_dir"]
    compress_archives = meta["compress_archives"]
    retention_days = meta["retention_days"]

    # Find rotated files in root: echo-oculus.log.YYYY-MM-DD or .YYYY-MM-DD_HH-MM-SS
    base = os.path.basename(meta["log_file"])
    pattern = os.path.join(root_dir, f"{base}.*")
    rotated = [p for p in glob(pattern) if os.path.isfile(p) and not p.endswith(".gz")]

    # Move + compress
    for p in rotated:
        try:
            dest = os.path.join(archive_dir, os.path.basename(p))
            if os.path.exists(dest):
                # if already in archive (race), remove original
                os.remove(p)
                continue
            shutil.move(p, dest)
            if compress_archives:
                gz_path = dest + ".gz"
                with open(dest, "rb") as fin, gzip.open(gz_path, "wb") as fout:
                    shutil.copyfileobj(fin, fout)
                os.remove(dest)
        except Exception as e:
            logging.getLogger(__name__).warning("Log maintenance move/compress failed: %s", e)

    # Purge old archives
    if retention_days > 0:
        cutoff = datetime.utcnow() - timedelta(days=retention_days)
        for ap in glob(os.path.join(archive_dir, "*")):
            try:
                mtime = datetime.utcfromtimestamp(os.path.getmtime(ap))
                if mtime < cutoff:
                    os.remove(ap)
            except Exception as e:
                logging.getLogger(__name__).warning("Log purge failed for %s: %s", ap, e)


# ------------------------------
# Main application
# ------------------------------
def main():
    config = load_config("config.yaml")
    _configure_logging(config)  # ✅ enable rotation + archives + retention

    logging.getLogger(__name__).info("Echo Oculus starting (Phase 1 + 1.5)…")

    gps_logger = GPSLogger(config)
    data_sources = DataSources(config)
    alert_engine = AlertEngine(config)

    last_sd_check = datetime.utcnow()
    last_log_maint = datetime.utcnow()

    try:
        while True:
            # ---- Core pipeline ----
            location = gps_logger.get_location()
            reports = data_sources.get_all_reports(location)
            alert_engine.process(location, reports)

            # ---- SD/Storage health every 30 minutes ----
            now = datetime.utcnow()
            if (now - last_sd_check) > timedelta(minutes=30):
                try:
                    check_sd_usage(threshold_percent=10)
                except Exception as e:
                    logging.getLogger(__name__).warning("SD check failed: %s", e)
                last_sd_check = now

            # ---- Log archive/retention maintenance every 10 minutes ----
            if (now - last_log_maint) > timedelta(minutes=10):
                _log_maintenance()
                last_log_maint = now

            # ---- Hooks for later phases (no-ops for now) ----
            # TODO Phase 2: push latest alerts/health into api.py (FastAPI) queue
            # TODO Phase 3: call WOT-RES scoring on recent segments
            # TODO Phase 3.5: hazard aging/expiry cron integration
            # TODO Phase 4: advanced audio classification dispatch
            # TODO Phase 5: curvature/grade pipeline enqueuing

            time.sleep(10)  # Avoid slamming CPU

    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Echo Oculus shutting down (KeyboardInterrupt)…")
    except Exception as e:
        logging.getLogger(__name__).exception("Fatal error in main loop: %s", e)


# ✅ Optional test route
if __name__ == "__main__":
    run_audio_test = False  # ← Flip to True to run scanner audio test only
    if run_audio_test:
        print("[TEST MODE] Running audio transcription scan...")
        try:
            audio_results = transcribe_scanner_audio()
            for match in audio_results:
                print(f"[MATCH] {match['match']} at {match['timestamp']} - {match['transcript'][:60]}...")
            print(f"[TEST DONE] Total matches: {len(audio_results)}\n")
        except Exception as e:
            print(f"[TEST ERROR] {e}")
    else:
        main()
