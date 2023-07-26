from google.cloud import storage
import streamlit as st
import os
import json
import google_handler
import fnmatch
import file_io
import utils
import traceback
import io


def init():
    creds_str = google_handler.get_gcp_creds()

    if not os.path.exists('temp'):
        os.makedirs('temp')

    with open('temp/google-credentials.json', 'w') as f:
        json.dump(creds_str, f)

    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'temp/google-credentials.json'
    storage_client = storage.Client()
    st.session_state['storage_client'] = storage_client


def upload_to_bucket(root_dir, file, uid, name, metadata=None, compress=None):
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
                file_content = file_obj.read() # read file content once

                default_meta = {
                    'md5_hash': utils.calculate_md5(file_content),
                    'size': utils.calculate_size(file_content),
                    'owner': st.session_state['student_number'],
                    'time': utils.get_current_time()
                }
                # Merge the default metadata with the given metadata
                meta = {**default_meta, **metadata} if metadata else default_meta

                # Set the blob metadata
                blob.metadata = meta

                blob.upload_from_file(io.BytesIO(file_content))
            # Delete the compressed file
            os.remove(compressed_file_path)
        else:
            # If compress is None or False, upload the file as is
            # Convert file_content to a BytesIO object and upload
            file_content = file.read()
            default_meta = {
                'md5_hash': utils.calculate_md5(file_content),
                'size': utils.calculate_size(file_content),
                'owner': st.session_state['student_number'],
                'time': utils.get_current_time()
            }

            # Merge the default metadata with the given metadata
            meta = {**default_meta, **metadata} if metadata else default_meta

            # Set the blob metadata
            blob.metadata = meta

            blob.upload_from_file(io.BytesIO(file_content))

    except Exception as e:
        tb = traceback.format_exc()
        st.error(f'❌Failed to upload to the bucket: **{e}** \n\n **Traceback**:\n ```{tb}```')
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
        st.error(f'failed to download file from bucket. **{e}**')
        st.stop()


def get_blobs(bucket, dir, name_pattern, extensions):
    blobs = []
    if '*' in name_pattern:
        # If wildcard is present in name_pattern, process as pattern.
        prefix, pattern = name_pattern.split('*', 1)
        # List blobs whose names start with the given prefix
        for blob in bucket.list_blobs(prefix=f"{dir}/{prefix}"):
            for extension in extensions:
                if blob.name.endswith(extension) and fnmatch.fnmatch(blob.name, f"{dir}/{name_pattern}"):
                    blobs.append(blob)
                    # Once a match is found, no need to check other extensions
                    break
    else:
        # If no wildcard is present, process name_pattern as exact file name.
        for extension in extensions:
            blob = bucket.blob(f"{dir}/{name_pattern}{extension}")
            if blob.exists():
                blobs.append(blob)
    return blobs


def get_public_urls_from_blobs(blobs):
    return [blob.public_url for blob in blobs]


def get_blob_md5(blobs):
    return [blob.md5_hash for blob in blobs]


def get_blob_info(root_dir, uid, name_pattern, extensions, infos):
    storage_client = st.session_state['storage_client']
    bucket = storage_client.get_bucket(st.secrets['gcp']['bucket_name'])
    dir = f"{root_dir}/{uid}"

    blobs = get_blobs(bucket, dir, name_pattern, extensions)

    for info in infos:
        if info == 'url':
            return get_public_urls_from_blobs(blobs)
        elif info == 'md5':
            return get_blob_md5(blobs)
        elif info == 'size':
            return [blob.size for blob in blobs]
        elif info == 'original_md5':
            return [blob.metadata.get('original_md5') for blob in blobs]
        else:
            raise ValueError(f'Unsupported info type: {info}. Supported types are "url", "md5" and "size".')
