import uuid
import streamlit as st
import os
import hashlib
import time


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


def calculate_md5(file_content):
    """Calculate the MD5 hash of the file content."""
    hash_md5 = hashlib.md5()
    # update the hash with the file content
    hash_md5.update(file_content)
    return hash_md5.hexdigest()


def calculate_size(file_content):
    """Get the size of the content in bytes."""
    return len(file_content)


def get_current_time():
    """Get the current datetime."""
    return time.strftime("%Y-%m-%d %H:%M:%S")


@st.cache_data
def check_id():
    try:
        if st.session_state['student_number']:
            return True
        else:
            return False
    except KeyError:
        return False
