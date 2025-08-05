import logging
from modules.alert_engine import AlertEngine
from modules.data_sources import DataSources
from modules.gps_logger import GPSLogger
from modules.utils import load_config
from modules.audio_transcriber import transcribe_scanner_audio  # ✅ NEW import

def main():
    config = load_config("config.yaml")
    logging.basicConfig(level=logging.INFO)
    
    gps_logger = GPSLogger(config)
    data_sources = DataSources(config)
    alert_engine = AlertEngine(config)

    while True:
        location = gps_logger.get_location()
        reports = data_sources.get_all_reports(location)
        alert_engine.process(location, reports)

# ✅ Optional test route
if __name__ == "__main__":
    run_audio_test = False  # ← Set this to True if you want to test once
    if run_audio_test:
        print("[TEST MODE] Running audio transcription scan...")
        audio_results = transcribe_scanner_audio()
        for match in audio_results:
            print(f"[MATCH] {match['match']} at {match['timestamp']} - {match['transcript'][:60]}...")
        print(f"[TEST DONE] Total matches: {len(audio_results)}\n")
    else:
        main()
