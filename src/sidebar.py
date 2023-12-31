import streamlit as st
import file_io
import auth


def sidebar():
    with st.sidebar:
        auth.login()
        st.markdown("## 🧭 Navigation\n"
                    "1. 📃 Enter the form to add data to the database\n"
                    "2. ⬇️ Review & download models from database\n")

        info_panel = st.container()

        st.session_state['MANIFEST'] = manifest_data = file_io.read_json('manifest.json')

        with info_panel:
            st.markdown('---')
            st.markdown(f"# {manifest_data['name']}")
            st.markdown(f"Version: `{manifest_data['version']}`")
            st.markdown(f"Author: [{manifest_data['author']}]({manifest_data['homepage']})")
            st.markdown(f"Description: {manifest_data['description']}")
            st.markdown(f"[Report a Bug]({manifest_data['bugs']['url']})")
            st.markdown(f"[Github Repo]({manifest_data['repository']['url']})")
            st.markdown(f"License: [{manifest_data['license']['type']}]({manifest_data['license']['url']})")
