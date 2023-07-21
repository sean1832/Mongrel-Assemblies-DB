import streamlit as st
import time


def auth_user(username):
    """Authenticates the user. If user exist in the data, return True, else return False."""
    # tolerate case sensitivity
    username = username.lower()

    if username in st.secrets["auth"]["users"]:
        st.session_state['student_number'] = username
        st.session_state['is_authenticated'] = True
        return True
    else:
        return False


def login():
    if not check_login():
        login_form = st.container()

        with login_form:
            st.markdown('### Login')
            st.markdown(
                "*This section authenticate your identity so that the database can record who is uploading what."
                "This also prevent external user from manipulate the database.*")
            username = st.text_input(
                'Student Number (include the "S")',
                help="Student number is required to upload data. This will form a kind of ID for the data.",
                placeholder="e.g. s1234567"
            )
            if st.button('Login'):
                if auth_user(username):
                    st.session_state['student_number'] = username
                    st.session_state['is_authenticated'] = True
                    st.experimental_rerun()
                    st.cache_data.clear()
                else:
                    st.error('Incorrect username')
    logout_button()

def logout_button():
    """Logout button."""
    logout_container = st.empty()
    if check_login():
        logout_container.markdown(f"### {st.session_state['student_number']}")
        if logout_container.button('Logout'):
            st.session_state['is_authenticated'] = False
            st.session_state['student_number'] = None
            st.experimental_rerun()
            st.cache_data.clear()
            st.success('Logged out successfully.')



def check_login():
    """Checks if the user is logged in."""
    try:
        if st.session_state['is_authenticated'] and st.session_state['student_number']:
            return True
        else:
            return False
    except KeyError:
        return False
