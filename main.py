import logging
import time
from datetime import datetime, timedelta
from modules.alert_engine import AlertEngine
from modules.data_sources import DataSources
from modules.gps_logger import GPSLogger
from modules.sd_monitor import check_sd_usage  # ✅ SD check
from modules.utils import load_config
from modules.audio_transcriber import transcribe_scanner_audio  # ✅ Audio test import

def main():
    config = load_config("config.yaml")
    logging.basicConfig(level=logging.INFO)
    
    gps_logger = GPSLogger(config)
    data_sources = DataSources(config)
    alert_engine = AlertEngine(config)

    last_sd_check = datetime.utcnow()  # ✅ Start SD check timer

    while True:
        location = gps_logger.get_location()
        reports = data_sources.get_all_reports(location)
        alert_engine.process(location, reports)

        # ✅ Check SD card usage every 30 minutes
        now = datetime.utcnow()
        if (now - last_sd_check) > timedelta(minutes=30):
            check_sd_usage(threshold_percent=10)
            last_sd_check = now

        time.sleep(10)  # Avoid slamming CPU

# ✅ Optional test route
if __name__ == "__main__":
    run_audio_test = False  # ← Flip to True to run scanner audio test only
    if run_audio_test:
        print("[TEST MODE] Running audio transcription scan...")
        audio_results = transcribe_scanner_audio()
        for match in audio_results:
            print(f"[MATCH] {match['match']} at {match['timestamp']} - {match['transcript'][:60]}...")
        print(f"[TEST DONE] Total matches: {len(audio_results)}\n")
    else:
        main()
