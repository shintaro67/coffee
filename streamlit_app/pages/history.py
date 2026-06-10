import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from db.repository import get_bean_map, list_beans, list_brew_logs


def _build_figure(series: list[dict]) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    x = [p.get("elapsed", 0.0) for p in series]
    weight = [p.get("weight", 0.0) for p in series]
    tk = [p.get("temp_kettle", 0.0) for p in series]
    td = [p.get("temp_dripper", 0.0) for p in series]
    flow = [p.get("flow_rate", 0.0) for p in series]

    fig.add_trace(go.Scatter(x=x, y=weight, name="Weight(g)", line=dict(color="#2f6690", width=2)), secondary_y=False)
    has_temp = any(abs(value) > 1e-9 for value in tk) or any(abs(value) > 1e-9 for value in td)
    if has_temp:
        fig.add_trace(go.Scatter(x=x, y=tk, name="Kettle(C)", line=dict(color="#c1121f", width=2)), secondary_y=False)
        fig.add_trace(go.Scatter(x=x, y=td, name="Dripper(C)", line=dict(color="#f77f00", width=2)), secondary_y=False)
    fig.add_trace(go.Bar(x=x, y=flow, name="Flow(g/s)", marker_color="#1d4ed8", opacity=0.4), secondary_y=True)

    fig.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h"))
    fig.update_xaxes(title_text="Elapsed (s)")
    fig.update_yaxes(title_text="Weight / Temp")
    fig.update_yaxes(title_text="Flow (g/s)", secondary_y=True)
    return fig


def render_history_page() -> None:
    st.subheader("History")

    beans = list_beans(include_archived=True)
    bean_map = get_bean_map()

    bean_options = {"All": None}
    for bean in beans:
        bean_options[f"{bean.id}: {bean.name}"] = bean.id

    c1, c2 = st.columns(2)
    selected_bean_label = c1.selectbox("Filter by Bean", options=list(bean_options.keys()))
    selected_bean_id = bean_options[selected_bean_label]

    rating_option = c2.selectbox("Filter by Rating", options=["All", 1, 2, 3, 4, 5], index=0)
    selected_rating = None if rating_option == "All" else int(rating_option)

    logs = list_brew_logs(bean_id=selected_bean_id, rating=selected_rating)
    if not logs:
        st.info("No logs found.")
        return

    rows = []
    for log in logs:
        bean = bean_map.get(log.bean_id)
        rows.append(
            {
                "LogID": log.id,
                "Date": log.date.strftime("%Y-%m-%d %H:%M"),
                "Bean": bean.name if bean else f"Bean#{log.bean_id}",
                "Days": log.days_from_roast,
                "EY": round(log.yield_ey, 2),
                "Rating": log.rating,
                "Extract(g)": round(log.extract_weight, 2),
                "Powder(g)": round(log.powder_weight, 2),
            }
        )

    # Interactive log list: clicking LogID sets the Select Log, clicking Bean name jumps to Beans page
    st.markdown("### Logs")
    header_cols = st.columns([1, 2, 3, 1, 1, 1, 1, 1])
    header_cols[0].write("LogID")
    header_cols[1].write("Date")
    header_cols[2].write("Bean")
    header_cols[3].write("Days")
    header_cols[4].write("EY")
    header_cols[5].write("Rating")
    header_cols[6].write("Extract(g)")
    header_cols[7].write("Powder(g)")

    for log in logs:
        c0, c1, c2, c3, c4, c5, c6, c7 = st.columns([1, 2, 3, 1, 1, 1, 1, 1])
        if c0.button(str(log.id), key=f"logbtn_{log.id}"):
            st.session_state.selected_log_id = log.id
            from utils.streamlit_compat import safe_rerun

            safe_rerun()
        c1.write(log.date.strftime("%Y-%m-%d %H:%M"))
        bean = bean_map.get(log.bean_id)
        bean_label = bean.name if bean else f"Bean#{log.bean_id}"
        if c2.button(bean_label, key=f"beanbtn_{log.id}"):
            # navigate to Bean Detail page (transient)
            st.session_state.page = "BeanDetail"
            st.session_state.detail_bean_id = str(log.bean_id)
            st.session_state._bean_detail_active = True
            from utils.streamlit_compat import safe_rerun

            safe_rerun()
        c3.write(log.days_from_roast)
        c4.write(round(log.yield_ey, 2))
        c5.write(log.rating)
        c6.write(round(log.extract_weight, 2))
        c7.write(round(log.powder_weight, 2))

    # keep Select Log for compatibility; default follows session state when set
    log_ids = [log.id for log in logs]
    if not log_ids:
        st.warning("No logs available.")
        return
    default_selected = st.session_state.get("selected_log_id")
    if default_selected not in log_ids:
        default_selected = log_ids[0]
    try:
        idx = log_ids.index(default_selected)
    except ValueError:
        idx = 0
        default_selected = log_ids[0]
    selected_log_id = st.selectbox("Select Log", options=log_ids, index=idx)
    st.session_state.selected_log_id = selected_log_id
    selected_log = next(log for log in logs if log.id == selected_log_id)

    st.markdown("### Detail")
    c3, c4 = st.columns(2)
    c3.write(f"Bean ID: {selected_log.bean_id}")
    c3.write(f"Brew Ratio: 1:{selected_log.brew_ratio:.2f}")
    c3.write(f"EY: {selected_log.yield_ey:.2f}")
    c3.write(f"Elapsed: {selected_log.elapsed_time_total:.2f} s")

    c4.write(f"Acidity/Sweetness/Body: {selected_log.acidity}/{selected_log.sweetness}/{selected_log.body}")
    c4.write(f"Rating: {selected_log.rating}")
    c4.write(f"Dripper: {selected_log.dripper}")
    c4.write(f"Grind: {selected_log.grind_size}")

    st.write("Notes")
    st.info(selected_log.notes or "(no notes)")

    series = selected_log.timeseries_json or []
    if series:
        has_temp = any(abs(float(p.get("temp_kettle", 0.0))) > 1e-9 for p in series) or any(abs(float(p.get("temp_dripper", 0.0))) > 1e-9 for p in series)
        if not has_temp:
            st.caption("Temperature is planned and currently disabled in weight-only mode.")
        fig = _build_figure(series)
        st.plotly_chart(fig, width='stretch')
    else:
        st.warning("No timeseries data in this log.")
