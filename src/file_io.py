import os
import streamlit as st
import json
import db_handler
import io


def get_size_from_bytes(file: bytes):
    """Get the size of the content in megabytes."""
    return len(file) / (1024 * 1024.0)


def compress_image(image, quality=30):
    """Compresses the image to a smaller size."""
    filename_no_extension = image.filename.split('.')[0]
    st.write(f"filename: {filename_no_extension}")
    filename = f"compressed.jpg"

    if not os.path.exists('temp'):
        os.makedirs('temp')

    image.save(f"temp/{filename}", "JPEG", optimize=True, quality=quality)
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


def export_to_json(df, filename):
    """Exports the data to a json file."""
    try:
        db = st.session_state['db']
        data = db_handler.fetch_all(db)
        data_json = json.dumps(data)
        st.download_button("⚙️Download JSON", data_json, f"{filename}.json", "text/json")
    except Exception as e:
        st.error(e)
        st.error('Failed to export to JSON.')
        st.stop()
