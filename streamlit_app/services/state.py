import streamlit as st

from config import ESP32_BASE_URL
from services.esp32_control import Esp32ControlClient
from services.udp_receiver import TelemetryBuffer, UdpReceiver
from config import UDP_ENABLED


REQUIRED_KEYS = {
    "telemetry_buffer": None,
    "udp_receiver": None,
    "control_client": None,
    "esp32_base_url": ESP32_BASE_URL,
    "powder_weight": 0.0,
    "target_ratio": 15.0,
    "target_water": 0.0,
    "is_collecting": False,
    "brew_finished": False,
    "brew_final_elapsed": 0.0,
    "brew_final_weight": 0.0,
    "brew_points": [],
    "selected_log_id": None,
}


def init_state() -> None:
    for key, value in REQUIRED_KEYS.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if st.session_state.telemetry_buffer is None:
        st.session_state.telemetry_buffer = TelemetryBuffer()

    if st.session_state.udp_receiver is None:
        if UDP_ENABLED:
            try:
                st.session_state.udp_receiver = UdpReceiver(st.session_state.telemetry_buffer)
                st.session_state.udp_receiver.start()
            except Exception as e:
                # don't let UDP issues break the whole app
                st.session_state.udp_receiver = None
                st.session_state.telemetry_buffer.add_message(f"UDP receiver disabled: {e}")
        else:
            st.session_state.udp_receiver = None

    if st.session_state.control_client is None:
        st.session_state.control_client = Esp32ControlClient(ESP32_BASE_URL)
