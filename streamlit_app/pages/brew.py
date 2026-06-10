from datetime import date

import streamlit as st

from db.repository import create_brew_log, list_beans
from services.udp_receiver import compute_flow_rate


def _bean_label(bean) -> str:
    days = (date.today() - bean.roast_date).days
    return f"{bean.id}: {bean.name} ({days}d)"


def _calc_ey(extract_weight: float, tds: float, powder_weight: float) -> float:
    if powder_weight <= 0:
        return 0.0
    return (extract_weight * tds) / powder_weight


def _reset_brew_session() -> None:
    st.session_state.powder_weight = 0.0
    st.session_state.target_water = 0.0
    st.session_state.is_collecting = False
    st.session_state.brew_finished = False
    st.session_state.brew_final_elapsed = 0.0
    st.session_state.brew_final_weight = 0.0
    st.session_state.brew_points = []


def render_brew_page() -> None:
    st.subheader("Brew")

    beans = list_beans(include_archived=False)
    if not beans:
        st.warning("Please register beans first.")
        return

    bean_labels = [_bean_label(bean) for bean in beans]
    bean_map = {label: bean for label, bean in zip(bean_labels, beans)}

    c1, c2 = st.columns([2, 1])
    selected_label = c1.selectbox("Bean", options=bean_labels)
    ratio = c2.number_input("Target Brew Ratio (1:X)", min_value=1.0, max_value=30.0, value=float(st.session_state.target_ratio), step=0.1)
    st.session_state.target_ratio = ratio

    # Only request a recent window of points to avoid copying the entire buffer
    latest, points = st.session_state.telemetry_buffer.snapshot(max_points=200)
    flow_rate = compute_flow_rate(points)

    if latest and st.session_state.is_collecting:
        # Downsample UI recording to at most once every 50ms to reduce UI and DB load
        last_elapsed = st.session_state.brew_points[-1]["elapsed"] if st.session_state.brew_points else -1.0
        if not st.session_state.brew_points or (latest.elapsed - last_elapsed >= 0.05):
            st.session_state.brew_points.append(
                {
                    "elapsed": latest.elapsed,
                    "weight": latest.weight,
                    "temp_kettle": latest.temp_kettle,
                    "temp_dripper": latest.temp_dripper,
                    "flow_rate": flow_rate,
                    "state": latest.state,
                }
            )

    if st.session_state.is_collecting and st.session_state.target_water > 0 and latest:
        progress_check = min(max(latest.weight / st.session_state.target_water, 0.0), 1.0)
        if progress_check >= 1.0:
            st.session_state.is_collecting = False
            st.session_state.brew_finished = True
            st.session_state.brew_final_elapsed = latest.elapsed
            st.session_state.brew_final_weight = latest.weight
            st.session_state.brew_points = list(st.session_state.brew_points)
            st.info("Pour Progress reached 100%. Measurement stopped. Fill in Save Result (after brew) and submit.")

    c3, c4 = st.columns(2)
    if c3.button("Tare (風袋引き)", width='stretch'):
        ok, msg = st.session_state.control_client.tare()
        if ok:
            _reset_brew_session()
            st.success("Tare sent.")
            # Immediately refresh UI so displayed weight shows 0.00g after tare
            st.rerun()
        else:
            st.error(f"Tare failed: {msg}")

    if c4.button("Start (抽出モード待機)", width='stretch'):
        current_weight = latest.weight if latest else 0.0
        st.session_state.powder_weight = max(current_weight, 0.0)
        st.session_state.target_water = st.session_state.powder_weight * ratio
        st.session_state.brew_finished = False
        st.session_state.brew_final_elapsed = 0.0
        st.session_state.brew_final_weight = 0.0
        ok, msg = st.session_state.control_client.start()
        if ok:
            st.session_state.is_collecting = True
            st.session_state.brew_points = []
            st.success("Start sent. Waiting for +5g trigger.")
            # Refresh UI so collection state is reflected immediately
            st.rerun()
        else:
            st.error(f"Start failed: {msg}")

    st.divider()

    latest_state = latest.state if latest else "unknown"
    current_weight = latest.weight if latest else 0.0
    elapsed = latest.elapsed if latest else 0.0
    if st.session_state.brew_finished:
        current_weight = st.session_state.brew_final_weight
        elapsed = st.session_state.brew_final_elapsed
    target_water = st.session_state.target_water
    current_ratio = (current_weight / st.session_state.powder_weight) if st.session_state.powder_weight > 0 else 0.0

    m1, m2, m3, m4 = st.columns(4)
    m5, m6, m7, m8 = st.columns(4)

    m1.metric("Powder (g)", f"{st.session_state.powder_weight:.2f}")
    m2.metric("Elapsed (s)", f"{elapsed:.1f}")
    m3.metric("Weight (g)", f"{current_weight:.2f}", f"/ {target_water:.2f}")
    m4.metric("Ratio (1:X)", f"{current_ratio:.2f}")

    m5.metric("Flow (g/s)", f"{flow_rate:.2f}")
    m6.metric("State", latest_state)
    m7.metric("Temp Kettle", "Planned")
    m8.metric("Temp Dripper", "Planned")

    progress = 0.0
    if target_water > 0:
        progress = min(max(current_weight / target_water, 0.0), 1.0)
    st.progress(progress, text=f"Pour Progress: {progress * 100:.1f}%")
    if st.session_state.brew_finished:
        st.success("Measurement finished. Save Result (after brew) is now ready.")

    st.divider()
    st.markdown("### Save Result (after brew)")

    selected_bean = bean_map[selected_label]
    days_from_roast = (date.today() - selected_bean.roast_date).days

    with st.form("save_brew_form"):
        c9, c10, c11 = st.columns(3)
        powder_weight_input = c9.number_input("Powder Weight (g)", min_value=0.0, value=float(st.session_state.powder_weight), step=0.1)
        extract_weight = c10.number_input("Extract Weight (g)", min_value=0.0, value=max(current_weight, 0.0), step=0.1)
        tds = c11.number_input("TDS (%)", min_value=0.0, max_value=20.0, value=0.0, step=0.1)

        ey = _calc_ey(extract_weight, tds, powder_weight_input)
        st.caption(f"EY (%) = (extract_weight * tds) / powder_weight = {ey:.2f}")

        c12, c13 = st.columns(2)
        grind_size = c12.text_input("Grind Size", value="")
        dripper = c13.text_input("Dripper", value="")

        c14, c15, c16, c17 = st.columns(4)
        acidity = c14.slider("Acidity", 1, 5, 3)
        sweetness = c15.slider("Sweetness", 1, 5, 3)
        body = c16.slider("Body", 1, 5, 3)
        rating = c17.slider("Rating", 1, 5, 3)

        notes = st.text_area("Notes", value="")
        submitted = st.form_submit_button("Save BrewLog")

        if submitted:
            series = list(st.session_state.brew_points)
            elapsed_total = series[-1]["elapsed"] if series else elapsed
            max_weight = max([p["weight"] for p in series], default=current_weight)

            create_brew_log(
                bean_id=selected_bean.id,
                days_from_roast=days_from_roast,
                elapsed_time_total=elapsed_total,
                max_weight=max_weight,
                powder_weight=powder_weight_input,
                extract_weight=extract_weight,
                tds=tds,
                yield_ey=ey,
                brew_ratio=ratio,
                grind_size=grind_size,
                dripper=dripper,
                acidity=acidity,
                sweetness=sweetness,
                body=body,
                rating=rating,
                notes=notes,
                timeseries_json=series,
            )

            _reset_brew_session()
            st.success("Saved brew log.")
