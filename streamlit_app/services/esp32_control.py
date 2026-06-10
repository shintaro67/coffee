import requests
import time
from urllib.parse import urlparse


def normalize_base_url(base_url: str) -> str:
    raw = base_url.strip()
    if not raw:
        return raw

    if "://" not in raw:
        raw = f"http://{raw}"

    parsed = urlparse(raw)
    if not parsed.scheme or not parsed.netloc:
        return raw.rstrip("/")

    return f"{parsed.scheme}://{parsed.netloc}"


class Esp32ControlClient:
    def __init__(self, base_url: str, timeout_sec: float = 2.5, retries: int = 3, status_retries: int = 2) -> None:
        self.base_url = normalize_base_url(base_url)
        self.timeout_sec = timeout_sec
        self.retries = max(1, retries)
        self.status_retries = max(1, status_retries)

    def tare(self) -> tuple[bool, str]:
        return self._post("/tare")

    def start(self) -> tuple[bool, str]:
        return self._post("/start")

    def status(self) -> tuple[bool, dict | str]:
        url = f"{self.base_url}/status"
        last_error = ""

        for attempt in range(1, self.status_retries + 1):
            try:
                response = requests.get(url, timeout=self.timeout_sec)
                if response.ok:
                    try:
                        return True, response.json()
                    except ValueError:
                        return True, response.text
                return False, f"HTTP {response.status_code}: {response.text}"
            except requests.Timeout:
                last_error = f"Timeout after {self.timeout_sec:.1f}s when calling {url} (attempt {attempt}/{self.status_retries})"
            except requests.ConnectionError as ex:
                last_error = str(ex)
            except requests.RequestException as ex:
                last_error = str(ex)

            if attempt < self.status_retries:
                time.sleep(0.2)

        return False, last_error or f"Request failed when calling {url}"

    def _post(self, path: str) -> tuple[bool, str]:
        url = f"{self.base_url}{path}"
        last_error = ""

        for attempt in range(1, self.retries + 1):
            try:
                response = requests.post(url, timeout=self.timeout_sec)
                if response.ok:
                    return True, response.text
                return False, f"HTTP {response.status_code}: {response.text}"
            except requests.Timeout:
                last_error = f"Timeout after {self.timeout_sec:.1f}s when calling {url} (attempt {attempt}/{self.retries})"
            except requests.RequestException as ex:
                last_error = str(ex)

            if attempt < self.retries:
                time.sleep(0.25)

        return False, last_error or f"Request failed when calling {url}"
