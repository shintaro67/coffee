from pathlib import Path
import sys


APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import streamlit as st

from config import ESP32_BASE_URL_DEFAULT
from pages.bean_detail import render_bean_detail
from pages.beans import render_beans_page
from pages.brew import render_brew_page
from pages.history import render_history_page
from services.esp32_control import Esp32ControlClient, normalize_base_url
from services.esp32_status import Esp32Status
from services.state import init_state


PAGES = {
    "Brew": render_brew_page,
    "Beans": render_beans_page,
    "History": render_history_page,
    "BeanDetail": render_bean_detail,
}


def _get_cached_status(control_client: Esp32ControlClient, refresh_seconds: float = 2.0) -> tuple[bool, dict | str]:
    now = st.session_state.get("_status_last_fetch_at", 0.0)
    cached_at = st.session_state.get("_status_cached_at", 0.0)
    cached_payload = st.session_state.get("_status_cached_payload")

    import time

    current_time = time.time()
    if cached_payload is not None and (current_time - cached_at) < refresh_seconds:
        return bool(st.session_state.get("_status_cached_ok", False)), cached_payload

    ok, payload = control_client.status()
    st.session_state._status_last_fetch_at = current_time
    st.session_state._status_cached_at = current_time
    st.session_state._status_cached_ok = ok
    st.session_state._status_cached_payload = payload
    return ok, payload


def render_sidebar() -> None:
    page_names = list(PAGES.keys())
    current_page = st.session_state.get("page", "Brew")
    if current_page not in PAGES:
        current_page = "Brew"
        st.session_state.page = current_page

    latest_device_ip = getattr(st.session_state.telemetry_buffer, "device_ip", None)
    latest_device_name = getattr(st.session_state.telemetry_buffer, "device_name", None)
    if latest_device_ip:
        detected_url = f"http://{latest_device_ip}:8080"
        current_base_url = st.session_state.get("esp32_base_url", ESP32_BASE_URL_DEFAULT)
        if current_base_url == ESP32_BASE_URL_DEFAULT or ".local" in current_base_url:
            st.session_state.esp32_base_url = detected_url
            st.session_state.control_client = Esp32ControlClient(detected_url)

    st.header("Navigation")
    selected_page = st.radio("Page", options=page_names, index=page_names.index(current_page), label_visibility="collapsed")
    st.divider()
    st.subheader("ESP32 Control")
    esp32_base_url = st.text_input(
        "ESP32 Base URL",
        value=st.session_state.get("esp32_base_url", ESP32_BASE_URL_DEFAULT),
        help="The Streamlit app sends /tare and /start to this URL.",
    )
    normalized_base_url = normalize_base_url(esp32_base_url)
    if normalized_base_url != st.session_state.get("esp32_base_url"):
        st.session_state.esp32_base_url = normalized_base_url
        st.session_state.control_client = Esp32ControlClient(normalized_base_url)
    if latest_device_ip:
        if latest_device_name:
            st.caption(f"Detected ESP32: {latest_device_name} @ {latest_device_ip}")
        else:
            st.caption(f"Detected ESP32 IP: {latest_device_ip}")

    status_ok, status_payload = _get_cached_status(st.session_state.control_client)
    st.divider()
    st.subheader("Live Status")
    if status_ok and isinstance(status_payload, dict):
        status = Esp32Status.from_payload(status_payload)
        st.metric("State", status.state)
        st.metric("Weight (g)", f"{status.weight:.2f}")
        st.metric("Elapsed (s)", f"{status.elapsed_ms / 1000.0:.1f}")
        st.caption(f"Temp Kettle: {status.temp_kettle:.1f} / Temp Dripper: {status.temp_dripper:.1f}")
    else:
        st.warning(f"ESP32 status unavailable: {status_payload}")

    st.caption("Example: http://192.168.11.4:8080")

    if selected_page != current_page:
        st.session_state.page = selected_page
        st.rerun()

@st.fragment(run_every=0.10)
def render_main_content() -> None:
    current_page = st.session_state.get("page", "Brew")
    if current_page not in PAGES:
        current_page = "Brew"
        st.session_state.page = current_page

    PAGES[current_page]()


def main() -> None:
    st.set_page_config(page_title="Coffee Brew Logger", page_icon="☕", layout="wide")
    init_state()

    if st.session_state.pop("__needs_rerun", False):
        st.rerun()

    st.title("Coffee Brew Logger")
    st.caption("ESP32 telemetry, bean management, and brew history")

    with st.sidebar:
        render_sidebar()

    render_main_content()


if __name__ == "__main__":
    main()