import firebase_admin
from firebase_admin import firestore
import google_handler
import pandas as pd
import streamlit as st


def get_init_firestore_app(name='default'):
    try:
        # Check if app already exists
        app = firebase_admin.get_app(name)
    except ValueError:
        # If app doesn't exist, initialize it
        cred = google_handler.get_firebase_creds()
        app = firebase_admin.initialize_app(cred, name=name)
    return app


def init_db(name='default'):
    """Initializes the database. This function should be called at the start of the app."""
    app = get_init_firestore_app(name)
    db = firestore.client(app=app)
    if 'db' not in st.session_state:
        st.session_state['db'] = db


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
def get_data(columns_order=['student_number', 'material', 'amount', 'notes', 'uid', 'images', 'created_at']):
    """Gets the data from the database. This function should be called when user wants to retrieve data to dataframe."""
    db = st.session_state['db']
    users_ref = db.collection('Users')
    users_docs = users_ref.stream()
    print("Fetching data from firestore...")

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
    df = df[columns_order]

    # call function for each column that needs exploding
    print("Exploding columns...")
    df = explode_list(df, 'images')
    df = explode_list(df, '3d_model')

    return df

def close_app_if_exists(name='default'):
    """Closes the Firebase app if it exists. This function should be called at the beginning of the script."""
    try:
        app = firebase_admin.get_app(name)
        firebase_admin.delete_app(app)
        print(f'App {name} has been closed.')
    except ValueError as e:
        print(f'App {name} does not exist.')


def fetch_all(db):
    collections = db.collections()
    results = {}

    for collection in collections:
        collection_name = collection.id
        docs = collection.stream()
        results[collection_name] = [doc.to_dict() for doc in docs]

    return results
