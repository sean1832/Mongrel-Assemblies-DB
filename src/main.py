import streamlit as st
import sidebar
import io
import db_handler
import utils
import gcp_handler
import file_io
from PIL import Image
import traceback
import streamlit_toggle as toggle

# set up page
st.set_page_config(
    page_title="Mongrel Assembly Database",
    page_icon="🔥",
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
if 'msg' not in st.session_state:
    st.session_state['msg'] = ''
if 'lock_uid' not in st.session_state:
    st.session_state['lock_uid'] = False

APP_NAME = st.session_state['app_name']
ROOT = st.session_state['db_root']

# set up containers
app_header = st.container()
app_body = st.container()
sidebar.sidebar()

# clearing database if it exists
app = None
db_handler.close_app_if_exists(APP_NAME)
gcp_handler.init()

def submit_form(uid, spec_id, name, material, amount, unit, notes, uploaded_images, uploaded_model):
    st.session_state['msg'] = ''
    filename = f'{spec_id}-{name}-{st.session_state["student_number"]}'
    with st.spinner(text='Uploading data...'):
        try:
            if len(uploaded_images) > 10:
                st.error('❌Maximum 10 images allowed.')
                st.stop()
            elif uploaded_model is None:
                st.error('❌Please upload a 3D model.')
                st.stop()
            elif amount == 0:
                st.error('❌Count cannot be `0`.')
                st.stop()
            else:
                # upload images
                img_count = 0
                for uploaded_image in uploaded_images:
                    # Convert to webp to reduce file size
                    img_data = uploaded_image.read()
                    img = Image.open(io.BytesIO(img_data))
                    file_path = file_io.compress_image(img, quality=90, format='webp')

                    # create metadata
                    img_meta = {
                        'category': 'image',
                        'original_name': uploaded_image.name,
                        'original_size': utils.calculate_size(img_data),
                        'original_md5': utils.calculate_md5(img_data)
                    }

                    with open(file_path, 'rb') as f:
                        gcp_handler.upload_to_bucket(ROOT, f, uid, f'{filename}-{img_count:02d}', metadata=img_meta)
                    img_count += 1

                # upload 3D model
                model_data = uploaded_model.read()
                model_meta = {
                    'category': '3d_model',
                    'original_name': uploaded_model.name,
                    'original_size': utils.calculate_size(model_data),
                    'original_md5': utils.calculate_md5(model_data)
                }
                uploaded_model.seek(0)  # reset pointer
                gcp_handler.upload_to_bucket(ROOT, uploaded_model, uid, filename, compress='gzip', metadata=model_meta)

                # upload metadata to database
                data = {
                    'spec_id': spec_id,
                    'name': name,
                    'material': material,
                    'amount': amount,
                    'unit': unit,
                    'notes': notes,
                    'images': gcp_handler.get_blob_info(ROOT, uid, f'{filename}*', ['.jpg', '.jpeg', '.png', '.webp'], infos=['url']),
                    '3d_model': gcp_handler.get_blob_info(ROOT, uid, f'{filename}*', ['.obj', '.3dm', '.gz', '.xz'], infos=['url']),
                    '3d_model_original_md5': gcp_handler.get_blob_info(ROOT, uid, f'{filename}*', ['.obj', '.3dm', '.gz', '.xz'], infos=['original_md5']),
                    '3d_model_compressed_md5': gcp_handler.get_blob_info(ROOT, uid, f'{filename}*', ['.obj', '.3dm', '.gz', '.xz'], infos=['md5']),
                    'time': utils.get_current_time()
                }
                db_handler.set_data(data, uid)
                # clear cache
                st.cache_data.clear()

                if not st.session_state['lock_uid']:
                    st.session_state['uid'] = utils.create_uuid()
                    st.session_state['msg'] = '🚀Data submitted to database! New UID generated.'
                else:
                    st.session_state['msg'] = '🚀Data submitted to database! UID is kept the same.'
                st.experimental_rerun()
        except Exception as e:
            tb = traceback.format_exc()
            st.error(f"❌Error uploading data to database. **\n\n{e}**\n\n**Traceback**:\n ```{tb}```")
            st.stop()


def data_form():
    # data form
    if st.session_state['is_authenticated']:
        if "uid" not in st.session_state:
            st.session_state['uid'] = utils.create_uuid()

        uid_gen = st.session_state['uid']
        with app_body:

            # unique id
            with st.container():
                uid = st.text_input(
                    '*UID (Override this if you want to update existing data)',
                    uid_gen,
                    help="**IMPORTANT: UID must be unique within the database! "
                         "Allocate same UID will override associated existing data**")
                col1, col2 = st.columns([0.2, 1])
                with col1:
                    if uid == '' or st.button(label='🔃 Generate new UID'):
                        st.session_state['uid'] = utils.create_uuid()
                        uid = st.session_state['uid']
                        st.experimental_rerun()
                with col2:
                    if toggle.st_toggle_switch('🔒 Lock UID', key='lock_uid', label_after=True):
                        if 'lock_uid' not in st.session_state:
                            st.session_state['lock_uid'] = True
                    else:
                        if 'lock_uid' not in st.session_state:
                            st.session_state['lock_uid'] = False
            # info fields
            with st.form(key='info_form'):
                col1, col2 = st.columns(2)
                with col1:
                    col3, col4, col5 = st.columns([1, 2, 1.5])
                    with col3:
                        spec_id = st.text_input('*Specification ID',
                                                help='What is the specification ID of the component?',
                                                placeholder='e.g. W01-F')
                        spec_id = spec_id.upper()
                    with col4:
                        name = st.text_input('*Name',
                                             help='What is the name of the component?',
                                             placeholder='e.g. Shop Front Window Frame')
                    with col5:
                        mat_list = ['Timber', 'Steel', 'Glass', 'Plaster', 'Brick', 'Concrete', 'polymers', 'Other']
                        material = st.selectbox('*Material', mat_list, help='What material is the component made of?')

                    col3, col4 = st.columns([2, 1])
                    with col3:
                        amount = st.number_input('*Amount', step=1, min_value=0, help='How many components are there?')
                    with col4:
                        unit = st.selectbox('*Unit', ['piece', 'm^2', 'm^3', 'kg'], help='What is the unit of the amount?')
                with col2:
                    notes = st.text_area('Notes/ Description', height=130, help='Notes or description for extra info')

                # image and 3D model uploader
                col1, col2 = st.columns(2)
                with col1:
                    uploaded_images = st.file_uploader("🖼️ Reference photographs or images (max 10)",
                                                       type=["jpg", "jpeg", "png"],
                                                       accept_multiple_files=True)
                with col2:
                    uploaded_model = st.file_uploader('*📐 3D Model (.3dm)', type=['3dm'], accept_multiple_files=False)

                if st.form_submit_button(label='🚀 Submit'):
                    submit_form(uid, spec_id, name, material, amount, unit, notes, uploaded_images, uploaded_model)

try:
    db_handler.init_db(APP_NAME)
    app = db_handler.get_init_firestore_app(APP_NAME)
    print('Database initialized.')

    with app_header:
        st.title('🔥Mongrel Assembly Data Entry Form')
        st.markdown(
            "Welcome to the Mongrel Assembly Database Interface. "
            "Users can upload images and "
            "3D models of reclaimed materials along with its metadata. "
            "This might help better documenting the materials for future use.")
        st.info("ℹ️ Note: This is a quick & dirty project, so there might be bugs.")
        st.markdown("This page is for submitting data to the database. Field contains `*` are required.")

        st.markdown('')

    if not st.session_state['is_authenticated']:
        st.warning('⚠️ Please log in to use the app! (Enter your student number and click Login)')
        st.stop()
    else:
        data_form()
        if st.session_state['msg'] != '':
            st.success(st.session_state['msg'])
            st.session_state['msg'] = ''

except KeyboardInterrupt:
    pass
finally:
    if app:
        db_handler.close_app_if_exists(APP_NAME)
        utils.clear_temp()
        print('Database closed.')
