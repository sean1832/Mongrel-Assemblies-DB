import firebase_admin
from firebase_admin import credentials, firestore
import google_handler
import gcp_handler
import pandas as pd
import streamlit as st


def init_db():
    """Initializes the database. This function should be called at the start of the app."""
    try:
        cred = google_handler.get_firebase_creds()
        app = firebase_admin.initialize_app(cred)
        db = firestore.client()
        if 'db' not in st.session_state:
            st.session_state['db'] = db
        return app
    except ValueError:
        st.error("Database already initialized.")
        return None


def set_data(data: dict, uid: str):
    """Sets the data in the database. This function should be called when the user submits the data form."""
    student_number = st.session_state['student_number']
    db = st.session_state['db']
    user_ref = db.collection('Users').document(student_number)

    # Check if user is admin
    is_admin = False
    if student_number is st.secrets['auth']['admin']:
        is_admin = True
    # set access
    access = "admin" if is_admin else "user"
    user_ref.set({'access': access})

    # Store data
    item_ref = user_ref.collection('Items').document(uid)
    item_ref.set(data)


def explode_list(df, col_name):
    """Explodes the list in the DataFrame"""
    # find the maximum length of list in the DataFrame
    max_len = df[col_name].str.len().max()

    # create new columns and split the list
    col_names = [f'{col_name}_{n}' for n in range(max_len)]
    df[col_names] = pd.DataFrame(df[col_name].tolist(), index=df.index)

    # drop original column
    df = df.drop(col_name, axis=1)
    return df


@st.cache_data
def get_data():
    """Gets the data from the database. This function should be called when user wants to retrieve data to dataframe."""
    db = st.session_state['db']
    users_ref = db.collection('Users')
    users_docs = users_ref.stream()
    data = []
    for user_doc in users_docs:
        print("Processing user doc...")
        user_id = user_doc.id
        items_ref = users_ref.document(user_id).collection('Items')
        items_docs = items_ref.stream()

        for item_doc in items_docs:
            print("Processing item doc...")
            item_data = item_doc.to_dict()
            item_id = item_doc.id
            item_data['uid'] = item_id
            item_data['student_number'] = user_id

            data.append(item_data)
    df = pd.DataFrame(data)
    # reorder columns
    df = df[['student_number', 'material', 'amount', 'notes', 'uid', 'images', '3d_model']]

    # call function for each column that needs exploding
    print("Exploding columns...")
    df = explode_list(df, 'images')
    df = explode_list(df, '3d_model')

    return df



def close_db(app):
    """Closes the database. This function should be called at the end of the app."""
    firebase_admin.delete_app(app)


def close_db_not_exist():
    """Closes the database. This function should be called at the end of the app."""
    if firebase_admin._DEFAULT_APP_NAME in firebase_admin._apps:
        firebase_admin.delete_app(firebase_admin._apps[firebase_admin._DEFAULT_APP_NAME])


def fetch_all(db):
    collections = db.collections()
    results = {}

    for collection in collections:
        collection_name = collection.id
        docs = collection.stream()
        results[collection_name] = [doc.to_dict() for doc in docs]

    return results
