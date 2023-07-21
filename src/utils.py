import uuid
import streamlit as st
import os


def create_uuid():
    """Creates a unique ID for the data entry."""
    return str(uuid.uuid4())

def clear_temp():
    if os.path.exists('temp'):
        # remove all files in temp
        for file in os.listdir('temp'):
            os.remove(os.path.join('temp', file))
        os.rmdir('temp')


def make_clickable(url):
    """Makes a URL clickable."""
    return f'<a target="_blank" href="{url}">{url}</a>'


@st.cache_data
def check_id():
    try:
        if st.session_state['student_number']:
            return True
        else:
            return False
    except KeyError:
        return False


