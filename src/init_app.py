import streamlit as st
import file_io


def init():
    if 'is_authenticated' not in st.session_state:
        st.session_state['is_authenticated'] = False
    if 'MANIFEST' not in st.session_state:
        st.session_state['MANIFEST'] = file_io.read_json('manifest.json')

    if 'student_number' not in st.session_state:
        st.session_state['student_number'] = None
    if 'db' not in st.session_state:
        st.session_state['db'] = None
    if 'storage_client' not in st.session_state:
        st.session_state['storage_client'] = None
