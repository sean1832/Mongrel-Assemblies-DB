import uuid
import streamlit as st
import os
import hashlib
import time


def create_uuid():
    """Creates a unique ID for the data entry."""
    return str(uuid.uuid4())


def clear_temp():
    if os.path.exists('temp'):
        # remove all files in temp
        for file in os.listdir('temp'):
            os.remove(os.path.join('temp', file))
        os.rmdir('temp')


def index_of_list(lst, item):
    """Returns the index of the item in the list."""
    try:
        return lst.index(item) if item in lst else 0
    except ValueError:
        return 0


def make_clickable(url):
    """Makes a URL clickable."""
    return f'<a target="_blank" href="{url}">{url}</a>'


def calculate_md5(file_content):
    """Calculate the MD5 hash of the file content."""
    hash_md5 = hashlib.md5()
    # update the hash with the file content
    hash_md5.update(file_content)
    return hash_md5.hexdigest()


def calculate_size(file_content):
    """Get the size of the content in bytes."""
    return len(file_content)


def get_current_time():
    """Get the current datetime."""
    return time.strftime("%Y-%m-%d %H:%M:%S")


@st.cache_data
def check_id():
    try:
        if st.session_state['student_number']:
            return True
        else:
            return False
    except KeyError:
        return False


def initialize_session_state():
    """Initialize or reset the session state variables."""
    import streamlit as st

    defaults = {
        'is_authenticated': False,
        'student_number': None,
        'storage_client': None,
        'app_name': 'mon-asm',
        'db_root': 'Inventory',
        'msg': '',
        'lock_uid': False
    }

    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def validate_submission(uploaded_images, uploaded_model, amount):
    """Validate the form submission inputs."""
    import streamlit as st

    if len(uploaded_images) > 10:
        st.error('❌Maximum 10 images allowed.')
        return False
    elif uploaded_model is None:
        st.error('❌Please upload a 3D model.')
        return False
    elif amount == 0:
        st.error('❌Count cannot be `0`.')
        return False
    return True


def create_metadata(ROOT, spec_id, name, material, amount, unit, notes, filename, uid):
    """Create metadata for the uploaded assets."""
    import gcp_handler

    data = {
        'spec_id': spec_id,
        'name': name,
        'material': material,
        'amount': amount,
        'unit': unit,
        'notes': notes,
        'images': gcp_handler.get_blob_info(ROOT, uid, f'{filename}*', ['.jpg', '.jpeg', '.png', '.webp'],
                                            infos=['url']),
        '3d_model': gcp_handler.get_blob_info(ROOT, uid, f'{filename}*', ['.obj', '.3dm', '.gz', '.xz'],
                                              infos=['url']),
        'original_md5': gcp_handler.get_blob_info(ROOT, uid, f'{filename}*',
                                                  ['.obj', '.3dm', '.gz', '.xz'],
                                                  infos=['original_md5']),
        'md5_hash': gcp_handler.get_blob_info(ROOT, uid, f'{filename}*',
                                              ['.obj', '.3dm', '.gz', '.xz'],
                                              infos=['md5_hash'])
    }

    return data


def submit_data_to_db(ROOT, spec_id, name, material, amount, unit, notes, filename, uid, model_scale):
    """Submit the constructed data to the database."""
    import gcp_handler

    data = {
        'spec_id': spec_id,
        'name': name,
        'material': material,
        'amount': amount,
        'unit': unit,
        'notes': notes,
        'images': gcp_handler.get_blob_info(ROOT, uid, f'{filename}*', ['.jpg', '.jpeg', '.png', '.webp'],
                                            infos=['url']),
        '3d_model': gcp_handler.get_blob_info(ROOT, uid, f'{filename}*', ['.obj', '.3dm', '.gz', '.xz'],
                                              infos=['url']),
        'original_md5': gcp_handler.get_blob_info(ROOT, uid, f'{filename}*',
                                                  ['.obj', '.3dm', '.gz', '.xz'],
                                                  infos=['original_md5']),
        'md5_hash': gcp_handler.get_blob_info(ROOT, uid, f'{filename}*',
                                              ['.obj', '.3dm', '.gz', '.xz'],
                                              infos=['md5_hash']),
        'time': utils.get_current_time(),
        'model_scale': model_scale
    }
    db_handler.set_data(data, uid)


def initialize_and_generate_uid():
    """Initialize and generate a UID if it doesn't exist."""
    import streamlit as st

    if "uid" not in st.session_state:
        st.session_state['uid'] = create_uuid()

    uid_gen = st.session_state['uid']
    with st.container():
        uid = st.text_input(
            '*UID (Override this if you want to update existing data)',
            uid_gen,
            help="**IMPORTANT: UID must be unique within the database! "
                 "Allocate same UID will override associated existing data**")
        col1, col2, col3 = st.columns([0.15, 0.2, 0.8])
        with col1:
            if uid == '' or st.button(label='🔃 Generate new UID'):
                st.session_state['uid'] = create_uuid()
                uid = st.session_state['uid']
                st.experimental_rerun()

    return uid


def check_uid_and_get_defaults(df, uid):
    """Check if the UID exists in the database and fetch default values for the form."""
    uid_exists = df['uid'].str.contains(uid).any()

    mat_list = ['Timber', 'Steel', 'Glass', 'Plaster', 'Brick', 'Concrete', 'polymers', 'Other']
    unit_list = ['piece', 'm', 'm^2', 'm^3', 'kg']
    defaults = {}
    if uid_exists:
        st.warning('⚠️ UID already exists in database. Editing existing data.')
        defaults['spec_id'] = df[df['uid'] == uid]['spec_id'].values[0]
        defaults['name'] = df[df['uid'] == uid]['name'].values[0]
        defaults['material'] = mat_list.index(df[df['uid'] == uid]['material'].values[0])
        defaults['amount'] = df[df['uid'] == uid]['amount'].values[0]
        defaults['unit'] = unit_list.index(df[df['uid'] == uid]['unit'].values[0])
        defaults['notes'] = df[df['uid'] == uid]['notes'].values[0]

    return uid_exists, defaults


def create_info_form(spec_id_default, name_default, material_default):
    """Create form fields for Specification ID, Name, and Material."""
    with st.form(key='info_form'):
        col1, col2 = st.columns(2)
        with col1:
            col3, col4, col5 = st.columns([1, 2, 1.5])
            with col3:
                spec_id = st.text_input('*Specification ID',
                                        help='What is the specification ID of the component?',
                                        placeholder='e.g. W01-F', value=spec_id_default)
                spec_id = spec_id.upper()
            with col4:
                name = st.text_input('*Name',
                                     help='What is the name of the component?',
                                     placeholder='e.g. Shop Front Window Frame', value=name_default)
            with col5:
                material = st.selectbox('*Material', mat_list, help='What material is the component made of?',
                                        index=material_default)

    return spec_id, name, material


def create_amount_unit_notes_form(amount_default, unit_default, notes_default):
    """Create form fields for Amount, Unit, and Notes/Description."""
    col3, col4 = st.columns([2, 1])
    with col3:
        amount = st.number_input('*Amount', step=1, min_value=0, help='How many components are there?',
                                 value=amount_default)
    with col4:
        unit = st.selectbox('*Unit', unit_list, help='What is the unit of the amount?', index=unit_default)
    with col2:
        notes = st.text_area('Notes/ Description', height=130, help='Notes or description for extra info',
                             value=notes_default)

    return amount, unit, notes


def create_additional_info_form(amount_default, unit_default, notes_default):
    """Create form fields for the component's Amount, Unit, and Notes."""
    with col2:
        col6, col7, col8 = st.columns([0.8, 1.2, 2])
        with col6:
            amount = st.number_input('*Amount',
                                     help='How much is the component? (e.g. 2.5)',
                                     format="%.2f", value=amount_default)
        with col7:
            unit = st.selectbox('*Unit', unit_list, help='What is the unit of the component?', index=unit_default)
        with col8:
            notes = st.text_area('Notes',
                                 help='Add any additional notes or details about the component here',
                                 placeholder='e.g. This is the main frame for the shop front window',
                                 value=notes_default)

    return amount, unit, notes


def create_uploaders():
    """Create uploaders for reference photographs or images and 3D models."""
    col1, col2, col3 = st.columns([1, 0.8, 0.2])
    with col1:
        uploaded_images = st.file_uploader("🖼️ Reference photographs or images (max 10)",
                                           type=["jpg", "jpeg", "png"],
                                           accept_multiple_files=True)
    with col2:
        uploaded_model = st.file_uploader('*📐 3D Model (.3dm)', type=['3dm'])

    return uploaded_images, uploaded_model


def create_model_scale_selector():
    """Create a selector for the model scale."""
    with col3:
        model_scale = st.selectbox('*Model Scale', ['mm', 'cm', 'm'], index=0)
    return model_scale


def display_messages():
    """Display informational and warning messages."""
    st.info("ℹ️ Note: This is a quick & dirty project, so there might be bugs.")
    st.markdown("This page is for submitting data to the database. Field contains `*` are required.")
    st.markdown('')

    if not st.session_state['is_authenticated']:
        st.warning('⚠️ Please log in to use the app! (Enter your student number and click Login)')
        st.stop()
    else:
        if st.session_state['msg'] != '':
            st.success(st.session_state['msg'])
            st.session_state['msg'] = ''
