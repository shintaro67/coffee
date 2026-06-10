import argparse
import math
import socket
import time


def main() -> None:
    parser = argparse.ArgumentParser(description="Send dummy telemetry to Streamlit UDP receiver")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5005)
    parser.add_argument("--seconds", type=int, default=20)
    parser.add_argument("--hz", type=float, default=10.0)
    parser.add_argument("--with-temp", action="store_true", help="Send temperature fields for future mode")
    args = parser.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dt = 1.0 / max(args.hz, 1.0)
    count = int(args.seconds * args.hz)

    for i in range(count):
        t = i * dt
        weight = max(0.0, min(280.0, t * 5.5 + 0.7 * math.sin(t * 2.2)))
        tk = 92.0 - 0.02 * t + 0.4 * math.sin(t * 0.7)
        td = 88.0 - 0.015 * t + 0.3 * math.sin(t * 0.5)

        if t < 2.0:
            state = "waiting"
        elif t < args.seconds - 2.0:
            state = "brewing"
        else:
            state = "finished"

        if args.with_temp:
            payload = f"{t:.3f},{weight:.2f},{tk:.2f},{td:.2f},{state}"
        else:
            payload = f"{t:.3f},{weight:.2f}"
        sock.sendto(payload.encode("utf-8"), (args.host, args.port))
        time.sleep(dt)

    sock.close()


if __name__ == "__main__":
    main()
