import streamlit as st
import db_handler
import sidebar
import pd_table

try:
    sidebar.sidebar()

    header = st.container()
    body = st.container()
    viewer = st.container()

    with header:
        st.title('🔥Firebase Database Viewer')
        st.markdown(
            "This page allows you to view the entire database and download the 3D models. Note that this is a `read-only` page, and you cannot edit the database from here.")
        st.info("ℹ️ Contact the **Zeke Zhang** to get access to the database.")

    if not st.session_state['is_authenticated']:
        with body:
            st.warning("⚠️ You are not authenticated. Please log in to view the database.")
    else:
        pd_table.table(body)
except KeyboardInterrupt:
    pass
finally:
    db_handler.close_app_if_exists(st.session_state['app_name'])
