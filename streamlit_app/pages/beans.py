from datetime import date

import streamlit as st

from db.repository import create_bean, list_beans, update_bean


PROCESSES = ["Washed", "Natural", "Anaerobic", "Honey", "Other"]


def _days_from_roast(roast_date: date) -> int:
    return (date.today() - roast_date).days


def render_beans_page() -> None:
    st.subheader("Beans Master")

    # allow focusing a bean via query params (e.g. ?focus_bean=3)
    try:
        params = {}
        get_q = getattr(st, "experimental_get_query_params", None)
        if callable(get_q):
            params = get_q()
        focus_bean = int(params.get("focus_bean", [None])[0]) if params.get("focus_bean") else None
    except Exception:
        focus_bean = None

    # fallback: session_state may have been set by other pages
    if focus_bean is None:
        fb = st.session_state.get("focus_bean")
        try:
            focus_bean = int(fb) if fb is not None else None
        except Exception:
            focus_bean = None

    with st.form("bean_new_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name = c1.text_input("Bean Name", value="")
        roaster = c2.text_input("Roaster / Farm", value="")

        c3, c4, c5 = st.columns(3)
        process = c3.selectbox("Process", options=PROCESSES, index=0)
        roast_level = c4.number_input("Roast Level (1-9)", min_value=1, max_value=9, value=5, step=1)
        roast_date = c5.date_input("Roast Date", value=date.today())

        notes = st.text_area("Notes (optional)", value="", height=60)

        submitted = st.form_submit_button("Add Bean")
        if submitted:
            if not name.strip():
                st.warning("Bean name is required.")
            else:
                create_bean(
                    name=name.strip(),
                    roaster=roaster.strip(),
                    process=process,
                    roast_level=str(roast_level),
                    roast_date=roast_date,
                    notes=notes.strip(),
                )
                st.success("Bean added.")
                st.rerun()

    st.divider()
    st.markdown("### Bean List")

    beans = list_beans(include_archived=True)
    if not beans:
        st.info("No beans yet.")
        return

    for bean in beans:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            expanded = (bean.id == focus_bean)
            with st.expander(f"🫘 {bean.name} (ID: {bean.id})", expanded=expanded):
                c1, c2, c3 = st.columns(3)
                c1.write(f"**Roaster:** {bean.roaster}")
                c2.write(f"**Process:** {bean.process}")
                c3.write(f"**Roast Level:** {bean.roast_level}/9")
                
                c4, c5 = st.columns(2)
                c4.write(f"**Roast Date:** {bean.roast_date.isoformat()}")
                c5.write(f"**Days:** {_days_from_roast(bean.roast_date)}")
                
                st.markdown("**Edit Bean:**")
                with st.form(f"edit_bean_{bean.id}", clear_on_submit=False):
                    new_name = st.text_input("Bean Name", value=bean.name)
                    new_roaster = st.text_input("Roaster / Farm", value=bean.roaster)
                    
                    e1, e2, e3 = st.columns(3)
                    new_process = e1.selectbox("Process", options=PROCESSES, index=PROCESSES.index(bean.process) if bean.process in PROCESSES else 0, key=f"process_{bean.id}")
                    new_roast_level = e2.number_input("Roast Level (1-9)", min_value=1, max_value=9, value=int(bean.roast_level) if bean.roast_level.isdigit() else 5, step=1, key=f"level_{bean.id}")
                    new_roast_date = e3.date_input("Roast Date", value=bean.roast_date, key=f"date_{bean.id}")
                    
                    new_notes = st.text_area("Notes", value=bean.notes or "", height=60, key=f"notes_{bean.id}")
                    
                    e4, e5 = st.columns(2)
                    new_archived = e4.checkbox("Archive", value=bean.is_archived, key=f"archived_{bean.id}")
                    
                    submitted = e5.form_submit_button("Update Bean")
                    if submitted:
                        update_bean(
                            bean_id=bean.id,
                            name=new_name,
                            roaster=new_roaster,
                            process=new_process,
                            roast_level=str(new_roast_level),
                            roast_date=new_roast_date,
                            notes=new_notes,
                            is_archived=new_archived,
                        )
                        st.success(f"Bean {bean.id} updated!")
                        st.rerun()
