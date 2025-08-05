import logging
from modules.alert_engine import AlertEngine
from modules.data_sources import DataSources
from modules.gps_logger import GPSLogger
from modules.utils import load_config

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

if __name__ == "__main__":
    main()
