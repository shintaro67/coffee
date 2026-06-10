from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_DIR = Path.home() / ".coffee_brew_logger"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "coffee.db"

UDP_LISTEN_HOST = "0.0.0.0"
UDP_LISTEN_PORT = 5005
UDP_ENABLED = True

ESP32_BASE_URL = "http://192.168.11.4:8080"
ESP32_BASE_URL_DEFAULT = ESP32_BASE_URL

FLOW_RATE_WINDOW_SECONDS = 1.5
REALTIME_BUFFER_LIMIT = 5000
