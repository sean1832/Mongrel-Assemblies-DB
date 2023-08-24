import os
import streamlit as st
import json
import io
import gzip
import lzma


def _create_temp_dir():
    if not os.path.exists('temp'):
        os.makedirs('temp')


def get_size_from_bytes(file: bytes):
    """Get the size of the content in megabytes."""
    return len(file) / (1024 * 1024.0)


def compress_image(image, quality=90, format='webp'):
    """Compresses the image to a smaller size."""
    filename_no_extension = os.path.splitext(image.filename)[0]
    filename = f"{filename_no_extension}_compressed.{format}"

    _create_temp_dir()

    image.save(f"temp/{filename}", format, optimize=True, quality=quality)
    return f"temp/{filename}"


@st.cache_data()
def read_json(file, key: str = None):
    """Reads a json file and returns the value of a key."""
    with open(file, "r") as f:
        data = json.load(f)
        if key and isinstance(data, dict):
            return data[key]
        elif key and isinstance(data, list):
            return [d[key] for d in data]
        else:
            return data


def export_to_csv(df, filename):
    """Exports the data to a csv file."""
    csv = df.to_csv(index=False)
    st.download_button("📃Download CSV", csv, f"{filename}.csv", "text/csv")


def export_to_excel(df, filename):
    """Exports the data to an Excel file."""
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, header=True, engine='openpyxl')
    buffer.seek(0)  # reset pointer

    st.download_button("💹Download Excel", buffer, f"{filename}.xlsx",
                       'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


def compress_to_xz(file):
    """Compresses the file to a xz file using lzma compression. This is smaller but slower than gzip."""
    _create_temp_dir()
    compressed_filename = file.name + '.xz'
    with lzma.open(f'temp/{compressed_filename}', 'wb') as f_out:
        f_out.write(file.getvalue())
    return f'temp/{compressed_filename}'


def compress_to_gzip(file):
    """Compresses the file to a gzip file. This is faster but larger than xz. This is the default compression method."""
    _create_temp_dir()
    compressed_filename = file.name + '.gz'
    with gzip.open(f'temp/{compressed_filename}', 'wb') as f_out:
        f_out.write(file.getvalue())
    return f'temp/{compressed_filename}'

# def export_to_json(df, filename):
#     """Exports the data to a json file."""
#     try:
#         db = st.session_state['db']
#         data = db_handler.fetch_all(db)
#         data_json = json.dumps(data)
#         st.download_button("⚙️Download JSON", data_json, f"{filename}.json", "text/json")
#     except Exception as e:
#         st.error(e)
#         st.error('Failed to export to JSON.')
#         st.stop()

def process_uploaded_image(uploaded_image):
    """Process the uploaded image: compress and generate metadata."""
    import io
    from PIL import Image
    import utils

    # Convert to webp to reduce file size
    img_data = uploaded_image.read()
    img = Image.open(io.BytesIO(img_data))
    file_path = compress_image(img, quality=90, format='webp')

    # Create metadata
    img_meta = {
        'category': 'image',
        'original_name': uploaded_image.name,
        'original_size': utils.calculate_size(img_data),
        'original_md5': utils.calculate_md5(img_data)
    }

    return file_path, img_meta

def upload_assets(ROOT, uploaded_image, img_meta, uploaded_model, model_meta, uid, filename):
    """Upload images and 3D model to GCP storage and return the paths."""
    import gcp_handler
    import utils

    # Upload image
    with open(file_path, 'rb') as f:
        gcp_handler.upload_to_bucket(ROOT, f, uid, f'{filename}-{img_count:02d}', metadata=img_meta)
    
    # Upload 3D model
    model_data = uploaded_model.read()
    uploaded_model.seek(0)  # reset pointer
    gcp_handler.upload_to_bucket(ROOT, uploaded_model, uid, filename, compress='gzip', metadata=model_meta)
