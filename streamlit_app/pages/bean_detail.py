import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date

from db.repository import get_bean_map, list_brew_logs, update_bean, update_brew_log


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


def render_bean_detail() -> None:
    st.subheader("Bean Detail")

    # determine bean id: session_state.detail_bean_id or focus_bean
    bean_id = st.session_state.get("detail_bean_id") or st.session_state.get("focus_bean")

    bean_map = get_bean_map()
    # If no bean specified, allow user to pick one
    if bean_id is None:
        bean_options = {"Select a bean": None}
        for b in bean_map.values():
            bean_options[f"{b.id}: {b.name}"] = b.id
        selected_label = st.selectbox("Select Bean to view", options=list(bean_options.keys()))
        selected = bean_options[selected_label]
        if selected is None:
            st.info("No bean selected.")
            return
        bean_id = selected
        st.session_state.detail_bean_id = str(bean_id)

    try:
        bean_id = int(bean_id)
    except Exception:
        st.error("Invalid bean id.")
        return

    bean = bean_map.get(int(bean_id)) if bean_map else None
    if bean is None:
        st.error(f"Bean {bean_id} not found")
        return

    st.markdown(f"## {bean.name} (ID: {bean.id})")

    # Edit form
    with st.form("edit_bean_detail", clear_on_submit=False):
        c1, c2 = st.columns(2)
        name = c1.text_input("Name", value=bean.name)
        roaster = c2.text_input("Roaster / Farm", value=bean.roaster)

        p1, p2, p3 = st.columns(3)
        process = p1.text_input("Process", value=bean.process)
        roast_level = p2.text_input("Roast Level", value=str(bean.roast_level))
        roast_date = p3.date_input("Roast Date", value=bean.roast_date)

        notes = st.text_area("Notes", value=bean.notes or "", height=120)
        submitted = st.form_submit_button("Save Bean")
        if submitted:
            update_bean(
                bean_id=bean.id,
                name=name.strip(),
                roaster=roaster.strip(),
                process=process.strip(),
                roast_level=str(roast_level).strip(),
                roast_date=roast_date,
                notes=notes.strip(),
            )
            st.success("Bean updated")
            # refresh state
            st.session_state.detail_bean_id = bean.id
            from utils.streamlit_compat import safe_rerun

            safe_rerun()

    st.divider()

    # Brew logs for this bean
    logs = list_brew_logs(bean_id=bean.id)
    if not logs:
        st.info("No brew logs for this bean.")
        return

    log_ids = [log.id for log in logs]
    selected_log_id = st.selectbox("Select Brew Log", options=log_ids)
    selected_log = next((l for l in logs if l.id == selected_log_id), None)
    if selected_log is None:
        st.warning("Selected log not found")
        return

    c1, c2 = st.columns(2)
    c1.write(f"Date: {selected_log.date.strftime('%Y-%m-%d %H:%M')}")
    c1.write(f"Rating: {selected_log.rating}")
    c1.write(f"Extract(g): {selected_log.extract_weight:.2f}")
    c1.write(f"Powder(g): {selected_log.powder_weight:.2f}")

    c2.write("Notes")
    new_notes = c2.text_area("Log Notes", value=selected_log.notes or "", key=f"lognotes_{selected_log.id}")
    if c2.button("Save Log Notes"):
        update_brew_log(selected_log.id, notes=new_notes)
        st.success("Log notes updated")
        from utils.streamlit_compat import safe_rerun

        safe_rerun()

    series = selected_log.timeseries_json or []
    if series:
        fig = _build_figure(series)
        st.plotly_chart(fig, width='stretch')
    else:
        st.warning("No timeseries data for this log.")
