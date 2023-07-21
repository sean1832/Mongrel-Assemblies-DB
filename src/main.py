import streamlit as st
import sidebar
import io
import db_handler
import utils
import gcp_handler
import file_io
from PIL import Image

# set up page
st.set_page_config(
    page_title="Mongrel Assembly Database",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

if 'is_authenticated' not in st.session_state:
    st.session_state['is_authenticated'] = False
if 'student_number' not in st.session_state:
    st.session_state['student_number'] = None
if 'storage_client' not in st.session_state:
    st.session_state['storage_client'] = None
if 'app_name' not in st.session_state:
    st.session_state['app_name'] = 'mon-asm'
if 'db_root' not in st.session_state:
    st.session_state['db_root'] = 'Inventory'

APP_NAME = st.session_state['app_name']
ROOT = st.session_state['db_root']

# set up containers
app_header = st.container()
app_body = st.form(key="data_form")
sidebar.sidebar()

# clearing database if it exists
app = None
db_handler.close_app_if_exists(APP_NAME)
gcp_handler.init()


def data_form():
    # data form
    if st.session_state['is_authenticated']:
        with app_body:
            st.markdown('#### Data form')
            st.markdown("*This section records the data you are uploading.*")
            # info fields
            col1, col2 = st.columns(2)
            with col1:
                material = st.selectbox('Material', ['Timber', 'Steel', 'Glass', 'Plaster', 'Brick'])
                col3, col4 = st.columns(2)
                with col3:
                    amount = st.number_input('Amount', step=1, min_value=0)
                with col4:
                    unit = st.selectbox('Unit', ['piece', 'm^2', 'm^3', 'kg'])
            with col2:
                notes = st.text_area('Notes/ Description', height=130)

            # image and 3D model uploader
            uploaded_images = st.file_uploader("Reference photographs or images (max 10)", type=["jpg", "jpeg", "png"],
                                               accept_multiple_files=True)
            uploaded_model = st.file_uploader('3D Model (.obj)', type=['obj'], accept_multiple_files=False)
            uid = utils.create_uuid()

            if st.form_submit_button(label='Submit'):
                msg = []
                with st.spinner(text='Uploading data...'):
                    try:
                        if uploaded_images is None or len(uploaded_images) == 0:
                            st.error('❌Please upload an reference image, '
                                     'this could be the photograph of the material '
                                     'or screenshot of the 3D model.')
                            st.stop()
                        elif len(uploaded_images) > 10:
                            st.error('❌Maximum 10 images allowed.')
                            st.stop()
                        elif uploaded_model is None:
                            st.error('❌Please upload a 3D model.')
                            st.stop()
                        elif amount == 0:
                            st.error('❌Count cannot be `0`.')
                            st.stop()
                        else:
                            img_count = 0
                            for uploaded_image in uploaded_images:
                                # Check the image size, and compress if it's over 5MB
                                img_data = uploaded_image.read()
                                if file_io.get_size_from_bytes(img_data) > 5:  # 5MB
                                    img = Image.open(io.BytesIO(img_data))
                                    file_path = file_io.compress_image(img, quality=50)
                                    msg.append(
                                        f"Image {uploaded_image.name} size is `{file_io.get_size_from_bytes(img_data)}`. Compressed to `{file_io.get_size_from_bytes(file_io.compress_image(img))}`.")
                                    with open(file_path, 'rb') as f:
                                        gcp_handler.upload_to_bucket(ROOT, f, uid, f'{uid}-{img_count:02d}')
                                else:
                                    uploaded_image.seek(0)
                                    gcp_handler.upload_to_bucket(ROOT, uploaded_image, uid, f'{uid}-{img_count:02d}')
                                img_count += 1

                            # upload 3D model
                            gcp_handler.upload_to_bucket(ROOT, uploaded_model, uid, uid)

                            # upload metadata to database
                            data = {
                                'material': material,
                                'amount': amount,
                                'unit': unit,
                                'notes': notes,
                                'images': gcp_handler.get_blob_urls(ROOT, uid, f'{uid}-*', ['.jpg', '.jpeg', '.png']),
                                '3d_model': gcp_handler.get_blob_urls(ROOT, uid, uid, ['.obj'])
                            }
                            db_handler.set_data(data, uid)
                            # clear cache
                            st.cache_data.clear()
                            if msg:
                                st.warning("\n\n".join(msg))
                            st.success('🚀Data submitted to database')
                    except Exception as e:
                        st.error(f"❌Error uploading data to database. \n\n{e}")
                        st.stop()


try:
    db_handler.init_db(APP_NAME)
    app = db_handler.get_init_firestore_app(APP_NAME)
    print('Database initialized.')

    with app_header:
        st.title('🚀Mongrel Assembly Data Entry Form')
        st.markdown(
            "Welcome to the Mongrel Assembly Database Interface. "
            "Users can upload images and "
            "3D models of reclaimed materials along with its metadata. "
            "This might help better documenting the materials for future use.")
        st.info("Note: This is a quick & dirty project, so there might be bugs.")

    if not st.session_state['is_authenticated']:
        st.warning('⚠️ Please log in to use the app!')
        st.stop()
    else:
        data_form()


except KeyboardInterrupt:
    pass
finally:
    if app:
        db_handler.close_app_if_exists(APP_NAME)
        utils.clear_temp()
        print('Database closed.')
