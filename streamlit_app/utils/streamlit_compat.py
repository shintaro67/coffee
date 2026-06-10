import streamlit as st


def safe_rerun():
    """Attempt to rerun the Streamlit app in a way compatible across versions.

    Prefer `st.experimental_rerun()` when available. If not, set a session flag
    and stop execution which will cause the app to refresh on next interaction.
    """
    try:
        rerun = getattr(st, "experimental_rerun", None)
        if callable(rerun):
            rerun()
            return
    except Exception:
        pass

    # Fallback: mark for rerun and stop
    try:
        st.session_state["__needs_rerun"] = True
    except Exception:
        pass
    try:
        stop = getattr(st, "stop", None)
        if callable(stop):
            stop()
    except Exception:
        return
