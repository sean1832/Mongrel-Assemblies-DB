import firebase_admin
from firebase_admin import firestore
from backend import credential, gcp_handler
import pandas as pd
import streamlit as st


def get_init_firestore_app(name='default'):
    try:
        # Check if app already exists
        app = firebase_admin.get_app(name)
    except ValueError:
        # If app doesn't exist, initialize it
        cred_json = credential.google_creds()
        cred = firebase_admin.credentials.Certificate(cred_json)
        app = firebase_admin.initialize_app(cred, name=name)
    return app


def init_db(name='default'):
    """Initializes the database. This function should be called at the start of the app."""
    app = get_init_firestore_app(name)
    db = firestore.client(app=app)
    if 'db' not in st.session_state:
        st.session_state['db'] = db


def get_user_ref(student_number: str):
    """Returns the user reference from the database."""
    db = st.session_state['db']
    user_ref = db.collection('Users').document(student_number)
    return user_ref


def set_data(data: dict, uid: str):
    """Sets the data in the database. This function should be called when the user submits the data form."""
    student_number = st.session_state['student_number']
    user_ref = get_user_ref(student_number)

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


def update_data(data: dict, uid: str, student_number: str):
    """Updates the data in the database. This function should be called when the user modified the database table."""
    user_ref = get_user_ref(student_number)

    # update data
    item_ref = user_ref.collection('Items').document(uid)
    item_ref.update(data)


def delete_data(uid: str, student_number: str):
    """Deletes the data in the database. This function should be called when the user modified the database table."""
    user_ref = get_user_ref(student_number)


    item_ref = user_ref.collection('Items').document(uid)

    # get 3d model and images path
    item_data = item_ref.get().to_dict()
    models_path = item_data['3d_model']
    images_path = item_data['images']

    # get filenames
    models_filename = [model_path.split('/')[-1] for model_path in models_path]
    images_filename = [image_path.split('/')[-1] for image_path in images_path]

    # delete from bucket
    gcp_handler.delete_from_bucket(st.session_state['db_root'], models_filename, uid)
    gcp_handler.delete_from_bucket(st.session_state['db_root'], images_filename, uid)

    # delete data
    item_ref.delete()


def explode_list(df, col_name):
    """Explodes the list in the DataFrame"""
    # find the maximum length of list in the DataFrame
    max_len = df[col_name].str.len().max()

    # create new columns and split the list
    col_names = [f'{col_name}_{n}' for n in range(max_len)]
    temp_df = pd.DataFrame(df[col_name].tolist(), index=df.index, columns=col_names)

    # sort the columns
    temp_df = temp_df.reindex(sorted(temp_df.columns), axis=1)

    # drop original column and join with the sorted DataFrame
    df = df.drop(col_name, axis=1)
    df = df.join(temp_df)

    return df


@st.cache_data
def get_data(columns_order):
    """Gets the data from the database. This function should be called when user wants to retrieve data to dataframe."""
    db = st.session_state['db']
    users_ref = db.collection('Users')
    users_docs = users_ref.stream()
    print("Fetching data from firestore...")

    data = []
    for user_doc in users_docs:
        user_id = user_doc.id
        items_ref = users_ref.document(user_id).collection('Items')
        items_docs = items_ref.stream()

        for item_doc in items_docs:
            item_data = item_doc.to_dict()
            item_id = item_doc.id
            item_data['uid'] = item_id
            item_data['student_number'] = user_id

            data.append(item_data)
    df = pd.DataFrame(data)
    # reorder columns
    exist_columns = []
    # check if column exists
    exist_columns = []
    for column in columns_order:
        if column in df.columns:
            exist_columns.append(column)
    df = df[exist_columns]

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
    except ValueError as e:
        pass


def fetch_all(db):
    collections = db.collections()
    results = {}

    for collection in collections:
        collection_name = collection.id
        docs = collection.stream()
        results[collection_name] = [doc.to_dict() for doc in docs]

    return results
