from google.cloud import storage
import streamlit as st
import os
import json
import google_handler
import fnmatch
import file_io

def init():
    creds_str = google_handler.get_gcp_creds()

    if not os.path.exists('temp'):
        os.makedirs('temp')

    with open('temp/google-credentials.json', 'w') as f:
        json.dump(creds_str, f)

    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'temp/google-credentials.json'
    storage_client = storage.Client()
    st.session_state['storage_client'] = storage_client


def upload_to_bucket(root_dir, file, uid, name, compress=None):
    dir = f"{root_dir}/{uid}"
    try:
        # get file extension
        extension = os.path.splitext(file.name)[1]
        filename = name + extension

        compressed_file_path = None

        if compress:
            # Compress file
            if compress == 'gzip':
                compressed_file_path = file_io.compress_to_gzip(file)
                filename += '.gz'  # Add '.gz' extension to the filename
            elif compress == 'xz':
                compressed_file_path = file_io.compress_to_xz(file)
                filename += '.xz'  # Add '.xz' extension to the filename
            else:
                raise ValueError(f'Unsupported compression type: {compress}. Supported types are "gzip" and "xz".'
                                 f'if you do not want to compress the file, set compress=None')

        storage_client = st.session_state['storage_client']
        bucket = storage_client.get_bucket(st.secrets['gcp']['bucket_name'])
        blob = bucket.blob(f"{dir}/{filename}")

        if compress:
            # Open the compressed file in read-binary mode for upload
            with open(compressed_file_path, 'rb') as file_obj:
                blob.upload_from_file(file_obj)
            # Delete the compressed file
            os.remove(compressed_file_path)
        else:
            # If compress is None or False, upload the file as is
            blob.upload_from_file(file)

    except Exception as e:
        st.error(f'❌Failed to upload to the bucket: {e}')
        st.stop()


def download_from_bucket(root_dir, filename, uid):
    try:
        storage_client = st.session_state['storage_client']
        bucket = storage_client.get_bucket(st.secrets['gcp']['bucket_name'])
        blob = bucket.blob(f"{root_dir}/{uid}/{filename}")

        if not os.path.exists('temp'):
            os.makedirs('temp')

        with open(f"temp/{filename}", 'wb') as f:
            storage_client.download_blob_to_file(blob, f)
        return f"temp/{filename}"
    except Exception as e:
        st.error(f'failed to download file from bucket. {e}')
        st.stop()


def get_blob_urls(root_dir, uid, name_pattern, extensions=['.jpg', '.png', '.jpeg']):
    storage_client = st.session_state['storage_client']
    bucket = storage_client.get_bucket(st.secrets['gcp']['bucket_name'])
    dir = f"{root_dir}/{uid}"

    urls = []
    if '*' in name_pattern:
        # If wildcard is present in name_pattern, process as pattern.
        # Split the pattern into a prefix and the rest of the pattern
        prefix, pattern = name_pattern.split('*', 1)
        # List blobs whose names start with the given prefix
        for blob in bucket.list_blobs(prefix=f"{dir}/{prefix}"):
            # For each blob, check if the rest of the name matches the pattern and the extension is one of the allowed extensions
            for extension in extensions:
                if blob.name.endswith(extension) and fnmatch.fnmatch(blob.name, f"{dir}/{name_pattern}"):
                    urls.append(blob.public_url)
                    # Once a match is found, no need to check other extensions
                    break
    else:
        # If no wildcard is present, process name_pattern as exact file name.
        # Combine name_pattern with each extension and check for blob's existence
        for extension in extensions:
            blob = bucket.blob(f"{dir}/{name_pattern}{extension}")
            if blob.exists():
                urls.append(blob.public_url)

    return urls

