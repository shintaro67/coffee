import socket
import threading
import time
from collections import deque
from dataclasses import dataclass

from config import FLOW_RATE_WINDOW_SECONDS, UDP_LISTEN_HOST, UDP_LISTEN_PORT


@dataclass
class TelemetryPoint:
    elapsed: float
    weight: float
    temp_kettle: float
    temp_dripper: float
    state: str
    ts: float


class TelemetryBuffer:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.latest: TelemetryPoint | None = None
        # Use configured buffer limit to bound memory and copy cost
        from config import REALTIME_BUFFER_LIMIT
        self.points: deque[TelemetryPoint] = deque(maxlen=REALTIME_BUFFER_LIMIT)
        self.device_ip: str | None = None
        self.device_name: str | None = None

    def add(self, point: TelemetryPoint) -> None:
        with self.lock:
            self.latest = point
            self.points.append(point)

    def snapshot(self, max_points: int | None = None) -> tuple[TelemetryPoint | None, list[TelemetryPoint]]:
        """Return the latest point and a list of up to `max_points` most recent points.

        If `max_points` is None, return all buffered points. This avoids copying
        large buffers on each UI update when only a recent window is needed.
        """
        with self.lock:
            if max_points is None:
                return self.latest, list(self.points)
            # slice deque efficiently by converting only the needed tail
            if max_points >= len(self.points):
                return self.latest, list(self.points)
            # take last max_points
            tail = []
            it = reversed(self.points)
            for _ in range(max_points):
                try:
                    tail.append(next(it))
                except StopIteration:
                    break
            tail.reverse()
            return self.latest, tail

    def set_device_info(self, device_ip: str, device_name: str | None = None) -> None:
        with self.lock:
            self.device_ip = device_ip
            self.device_name = device_name


def parse_payload(payload: str) -> TelemetryPoint | None:
    # Supported formats:
    # - elapsed,weight
    # - elapsed,weight,state
    # - elapsed,weight,temp_kettle,temp_dripper,state
    parts = [p.strip() for p in payload.split(",")]
    if len(parts) < 2:
        return None

    try:
        elapsed = float(parts[0])
        weight = float(parts[1])

        temp_kettle = 0.0
        temp_dripper = 0.0
        state = "unknown"

        if len(parts) >= 5:
            temp_kettle = float(parts[2])
            temp_dripper = float(parts[3])
            state = parts[4]
        elif len(parts) == 3:
            state = parts[2]

        return TelemetryPoint(
            elapsed=elapsed,
            weight=weight,
            temp_kettle=temp_kettle,
            temp_dripper=temp_dripper,
            state=state,
            ts=time.time(),
        )
    except ValueError:
        return None


def parse_announcement(payload: str) -> tuple[str, str | None] | None:
    parts = [p.strip() for p in payload.split(",")]
    if len(parts) < 2 or parts[0] != "announce":
        return None
    device_ip = parts[1]
    device_name = parts[2] if len(parts) >= 3 and parts[2] else None
    return device_ip, device_name


def compute_flow_rate(points: list[TelemetryPoint], now_ts: float | None = None) -> float:
    if len(points) < 2:
        return 0.0

    ref_ts = now_ts if now_ts is not None else time.time()
    recent = [p for p in points if ref_ts - p.ts <= FLOW_RATE_WINDOW_SECONDS]
    if len(recent) < 2:
        recent = points[-2:]

    first = recent[0]
    last = recent[-1]
    dt = max(last.ts - first.ts, 1e-6)
    return (last.weight - first.weight) / dt


class UdpReceiver:
    def __init__(self, telemetry_buffer: TelemetryBuffer) -> None:
        self.telemetry_buffer = telemetry_buffer
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def _run(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.bind((UDP_LISTEN_HOST, UDP_LISTEN_PORT))
        except OSError:
            sock.close()
            return
        sock.settimeout(0.1)

        while not self._stop_event.is_set():
            try:
                data, _ = sock.recvfrom(1024)
            except socket.timeout:
                continue
            except OSError:
                break

            message = data.decode("utf-8", errors="ignore")
            announcement = parse_announcement(message)
            if announcement is not None:
                device_ip, device_name = announcement
                self.telemetry_buffer.set_device_info(device_ip, device_name)
                continue

            point = parse_payload(message)
            if point is not None:
                self.telemetry_buffer.add(point)

        sock.close()
