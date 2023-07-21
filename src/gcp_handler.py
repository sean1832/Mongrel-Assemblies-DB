from google.cloud import storage
import streamlit as st
import os
import json
import google_handler
import fnmatch

def init():
    creds_str = google_handler.get_gcp_creds()

    if not os.path.exists('temp'):
        os.makedirs('temp')

    with open('temp/google-credentials.json', 'w') as f:
        json.dump(creds_str, f)

    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'temp/google-credentials.json'
    storage_client = storage.Client()
    st.session_state['storage_client'] = storage_client


def upload_to_bucket(file, uid, name):
    try:
        # get file extension
        extension = os.path.splitext(file.name)[1]
        filename = name + extension

        storage_client = st.session_state['storage_client']
        bucket = storage_client.get_bucket(st.secrets['gcp']['bucket_name'])
        blob = bucket.blob(f"{uid}/{filename}")
        blob.upload_from_file(file)
    except Exception as e:
        st.error(e)
        st.stop()


def download_from_bucket(filename, uid):
    try:
        storage_client = st.session_state['storage_client']
        bucket = storage_client.get_bucket(st.secrets['gcp']['bucket_name'])
        blob = bucket.blob(f"{uid}/{filename}")

        if not os.path.exists('temp'):
            os.makedirs('temp')

        with open(f"temp/{filename}", 'wb') as f:
            storage_client.download_blob_to_file(blob, f)
        return f"temp/{filename}"
    except Exception as e:
        st.error(f'failed to download file from bucket. {e}')
        st.stop()


def get_blob_urls(uid, name_pattern, extensions=['.jpg', '.png', '.jpeg']):
    storage_client = st.session_state['storage_client']
    bucket = storage_client.get_bucket(st.secrets['gcp']['bucket_name'])

    urls = []
    if '*' in name_pattern:
        # If wildcard is present in name_pattern, process as pattern.
        # Split the pattern into a prefix and the rest of the pattern
        prefix, pattern = name_pattern.split('*', 1)
        # List blobs whose names start with the given prefix
        for blob in bucket.list_blobs(prefix=f"{uid}/{prefix}"):
            # For each blob, check if the rest of the name matches the pattern and the extension is one of the allowed extensions
            for extension in extensions:
                if blob.name.endswith(extension) and fnmatch.fnmatch(blob.name, f"{uid}/{name_pattern}"):
                    urls.append(blob.public_url)
                    # Once a match is found, no need to check other extensions
                    break
    else:
        # If no wildcard is present, process name_pattern as exact file name.
        # Combine name_pattern with each extension and check for blob's existence
        for extension in extensions:
            blob = bucket.blob(f"{uid}/{name_pattern}{extension}")
            if blob.exists():
                urls.append(blob.public_url)

    return urls

