import streamlit as st
import sidebar
import io
from backend import db_handler, gcp_handler
import utils
import file_io
from PIL import Image
import traceback
import streamlit_toggle as toggle
import pd_table
import map
from streamlit_extras.no_default_selectbox import selectbox

# set up page
st.set_page_config(
    page_title="Mongrel Assembly Database",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

utils.initialize_session_state()

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


def submit_form(base_info, source_info, origin_info, uploaded_images, uploaded_model):
    uid = base_info['uid']
    spec_id = base_info['spec_id']
    name = base_info['name']
    material = base_info['material']
    amount = base_info['amount']
    unit = base_info['unit']
    notes = base_info['notes']
    model_scale = base_info['model_scale']

    st.session_state['msg'] = ''
    filename = f'{spec_id}-{name}-{st.session_state["student_number"]}'
    with st.spinner(text='Uploading data...'):
        try:
            if len(uploaded_images) > 10:
                st.error('❌Maximum 10 images allowed.')
                st.stop()
            elif uploaded_model is None and not st.session_state['lock_assets']:
                st.error('❌Please upload a 3D model.')
                st.stop()
            elif amount == 0:
                st.error('❌Count cannot be `0`.')
                st.stop()
            else:
                if not st.session_state['lock_assets']:
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
                    gcp_handler.upload_to_bucket(ROOT, uploaded_model, uid, filename, compress='gzip',
                                                 metadata=model_meta)

                    # upload metadata to database
                    data = {
                        'spec_id': spec_id,
                        'name': name,
                        'material': material,
                        'amount': amount,
                        'unit': unit,
                        'notes': notes,
                        'images': gcp_handler.get_blob_info(ROOT, uid, f'{filename}*',
                                                            ['.jpg', '.jpeg', '.png', '.webp'],
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
                        'model_scale': model_scale,
                        'source_name': source_info['name'],
                        'source_year': source_info['year'],
                        'source_latitude': source_info['latitude'],
                        'source_longitude': source_info['longitude'],
                        'source_country': source_info['country'],
                        'source_state': source_info['state'],
                        'source_city': source_info['city'],
                        'source_notes': source_info['notes'],
                        'origin_name': origin_info['name'],
                        'origin_year': origin_info['year'],
                        'origin_latitude': origin_info['latitude'],
                        'origin_longitude': origin_info['longitude'],
                        'origin_country': origin_info['country'],
                        'origin_state': origin_info['state'],
                        'origin_city': origin_info['city'],
                        'origin_notes': origin_info['notes'],
                        'owner': st.session_state['student_number']
                    }
                    db_handler.set_data(data, uid)
                else:
                    data = {
                        'spec_id': spec_id,
                        'name': name,
                        'material': material,
                        'amount': amount,
                        'unit': unit,
                        'notes': notes,
                        'time': utils.get_current_time(),
                        'model_scale': model_scale,
                        'source_name': source_info['name'],
                        'source_year': source_info['year'],
                        'source_latitude': source_info['latitude'],
                        'source_longitude': source_info['longitude'],
                        'source_country': source_info['country'],
                        'source_state': source_info['state'],
                        'source_city': source_info['city'],
                        'source_notes': source_info['notes'],
                        'origin_name': origin_info['name'],
                        'origin_year': origin_info['year'],
                        'origin_latitude': origin_info['latitude'],
                        'origin_longitude': origin_info['longitude'],
                        'origin_country': origin_info['country'],
                        'origin_state': origin_info['state'],
                        'origin_city': origin_info['city'],
                        'origin_notes': origin_info['notes'],
                        'owner': st.session_state['student_number']
                    }
                    db_handler.update_data(data, uid, st.session_state['student_number'])

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


def db_selector_form():
    """Quick Edit Form"""
    with st.expander("📝 Modify from database"):
        df = pd_table.table(st.container())
        return df


def uid_form():
    # unique id
    if "uid" not in st.session_state:
        st.session_state['uid'] = utils.create_uuid()

    uid_gen = st.session_state['uid']
    with st.container():
        uid = st.text_input(
            '*UID (Override this if you want to update existing data)',
            uid_gen,
            help="**IMPORTANT: UID must be unique within the database! "
                 "Allocate same UID will override associated existing data**")
        col1, col2, col3, col4 = st.columns([0.2, 0.2, 0.2, 0.2])
        with col1:
            if uid == '' or st.button(label='🔃 Generate new UID'):
                st.session_state['uid'] = utils.create_uuid()
                uid = st.session_state['uid']
                st.experimental_rerun()
        with col2:
            if st.button('📝 Check is UID exists in database'):
                st.experimental_rerun()
        with col3:
            if toggle.st_toggle_switch('🔒 Lock UID', key='lock_uid', label_after=True):
                if 'lock_uid' not in st.session_state:
                    st.session_state['lock_uid'] = True
            else:
                if 'lock_uid' not in st.session_state:
                    st.session_state['lock_uid'] = False
        with col4:
            if toggle.st_toggle_switch('🔒 Lock Assets', key='lock_assets', label_after=True):
                if 'lock_assets' not in st.session_state:
                    st.session_state['lock_assets'] = True
            else:
                if 'lock_assets' not in st.session_state:
                    st.session_state['lock_assets'] = False
    return uid


def map_marker_form():
    melbourne_loc = {
        "lat": -37.8074,
        "long": 144.9568
    }
    markers = [
        {
            "name": "QVM",
            "lat": -37.8069,
            "long": 144.9570
        },
        {
            "name": "Beech Forest",
            "lat": -38.626938,
            "long": 143.571625
        }
    ]
    tiles = ["Satellite", "Stamen Terrain", "Stamen Toner", "Stamen Watercolor", "CartoDB Positron",
             "CartoDB Dark_Matter"]
    map.interactive_map(melbourne_loc, markers, 15, tiles=tiles)
    map.make_map_responsive()


def more_info_form():
    target_countries = ['Australia', 'China', 'United States', 'United Kingdom', 'Japan', 'Germany', 'France', 'Italy']

    states_df = file_io.read_csv('data/states.csv')
    cities_df = file_io.read_csv('data/cities.csv')

    # Filter the dataframes based on the desired countries
    filtered_states_df = states_df[states_df['country_name'].isin(target_countries)]
    filtered_cities_df = cities_df[cities_df['country_name'].isin(target_countries)]

    countries_list = target_countries
    states_list = list(set(filtered_states_df['name'].tolist()))
    cities_list = list(set(filtered_cities_df['name'].tolist()))

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("### 🏗️ Source")
        st.info("Where was this item salvaged from?", icon='❔')
        col1, col2 = st.columns(2)
        with col1:
            source_name = st.text_input('Source (e.g. `Queen Victorian Market` or `Beach Forest Quarry`)',
                                        help='Where is this item salvaged from?')
            source_latitude = st.number_input('Latitude',
                                              format='%.5f',
                                              step=0.00001,
                                              help='Latitude of the source location',
                                              min_value=-90.0, max_value=90.0, value=0.0)
        with col2:
            source_year = st.number_input('Year (if unknown, set to `-1`)', step=1, min_value=2023,
                                          help='What year is this item salvaged from?')
            source_longitude = st.number_input('Longitude',
                                               format='%.5f',
                                               step=0.00001,
                                               help='Longitude of the source location',
                                               min_value=-180.0, max_value=180.0, value=0.0)

        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            source_country = st.selectbox('Source Country', countries_list,
                                          index=utils.index_of_list(countries_list, 'Australia'))
        with col2:
            source_state = st.selectbox('Source State', states_list, index=utils.index_of_list(states_list, 'Victoria'))
        with col3:
            source_city = st.selectbox('Source City', cities_list, index=utils.index_of_list(cities_list, 'Melbourne'))
        source_notes = st.text_area('Source Notes (e.g. `shed-a` or `toilet`)', height=130,
                                    help='Notes or description for extra info')
    with col_b:
        st.markdown('### 🏭 Origin')
        st.info('Where was this item manufactured or originated? (if known)', icon='❔')
        col1, col2 = st.columns(2)
        with col1:
            origin_name = st.text_input('Origin (e.g. `Bowling Iron Works`)', help='Where is this item manufactured?')
            origin_latitude = st.number_input('Latitude',
                                              format='%.5f',
                                              step=0.00001,
                                              help='Latitude of the origin location',
                                              min_value=-90.0, max_value=90.0, value=0.0)
        with col2:
            origin_year = st.number_input('Year (if unknown, set to `-1`)', step=1, min_value=-1,
                                          help='What year is this item manufactured?')
            origin_longitude = st.number_input('Longitude',
                                               format='%.5f',
                                               step=0.00001,
                                               help='Longitude of the origin location',
                                               min_value=-180.0, max_value=180.0, value=0.0)

        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            origin_country = selectbox('Origin Country', countries_list, no_selection_label="<Unknown>")
        with col2:
            origin_state = selectbox('Origin State', states_list, no_selection_label="<Unknown>")
        with col3:
            origin_city = selectbox('Origin City', cities_list, no_selection_label="<Unknown>")

        origin_notes = st.text_area('Origin Notes', height=130, help='Notes or description for extra info')

    # handle empty values
    if source_year == -1:
        source_year = None
    if origin_year == -1:
        origin_year = None

    if not origin_country:
        origin_country = "<Unknown>"
    if not origin_state:
        origin_state = "<Unknown>"
    if not origin_city:
        origin_city = "<Unknown>"

    if source_longitude == 0.0 and source_latitude == 0.0:
        source_longitude = None
        source_latitude = None

    if origin_longitude == 0.0 and origin_latitude == 0.0:
        origin_longitude = None
        origin_latitude = None

    source_data = {
        'name': source_name,
        'year': source_year,
        'latitude': source_latitude,
        'longitude': source_longitude,
        'country': source_country,
        'state': source_state,
        'city': source_city,
        'notes': source_notes
    }

    origin_data = {
        'name': origin_name,
        'year': origin_year,
        'latitude': origin_latitude,
        'longitude': origin_longitude,
        'country': origin_country,
        'state': origin_state,
        'city': origin_city,
        'notes': origin_notes
    }

    return source_data, origin_data


def info_form(uid, df):
    # info fields
    uid_exists = df['uid'].str.contains(uid).any()

    mat_list = ['Timber', 'Steel', 'Glass', 'Plaster', 'Brick', 'Concrete', 'polymers', 'Other']
    unit_list = ['piece', 'm', 'm^2', 'm^3', 'kg']
    if uid_exists:
        st.warning('⚠️ UID already exists in database. Editing existing data.')
        spec_id_default = df[df['uid'] == uid]['spec_id'].values[0]
        name_default = df[df['uid'] == uid]['name'].values[0]
        # index of material in list
        material_default = mat_list.index(df[df['uid'] == uid]['material'].values[0])
        amount_default = df[df['uid'] == uid]['amount'].values[0]
        unit_default = unit_list.index(df[df['uid'] == uid]['unit'].values[0])
        notes_default = df[df['uid'] == uid]['notes'].values[0]
    else:
        spec_id_default = ''
        name_default = ''
        material_default = 0
        amount_default = 0
        unit_default = 0
        notes_default = ''
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

            col3, col4 = st.columns([2, 1])
            with col3:
                amount = st.number_input('*Amount', step=1, min_value=0, help='How many components are there?',
                                         value=amount_default)
            with col4:
                unit = st.selectbox('*Unit', unit_list, help='What is the unit of the amount?', index=unit_default)
        with col2:
            notes = st.text_area('Notes/ Description', height=130, help='Notes or description for extra info',
                                 value=notes_default)

        with st.expander('📝 More info', expanded=True):
            source_info, origin_info = more_info_form()
            st.markdown('**Map Marker**: Click on the map to get the exact coordinates. '
                        'Copy and paste the coordinates (`latitude`, `longitude`) to the form.')
            map_marker_form()

        # image and 3D model uploader
        col1, col2, col3 = st.columns([1, 0.8, 0.2])
        with col1:
            uploaded_images = st.file_uploader("🖼️ Reference photographs or images (max 10)",
                                               type=["jpg", "jpeg", "png", "webp"],
                                               accept_multiple_files=True)
        with col2:
            uploaded_model = st.file_uploader('*📐 3D Model (.3dm)', type=['3dm'], accept_multiple_files=False)
        with col3:
            model_scale = st.selectbox('*Model Scale', ['mm', 'cm', 'm'], index=0)

        base_info = {
            'uid': uid,
            'spec_id': spec_id,
            'name': name,
            'material': material,
            'amount': amount,
            'unit': unit,
            'notes': notes,
            'model_scale': model_scale
        }

        if st.form_submit_button(label='🚀 Submit'):
            submit_form(base_info, source_info, origin_info, uploaded_images, uploaded_model)


def data_form():
    # data form
    if st.session_state['is_authenticated']:
        with app_body:
            df = db_selector_form()
            uid = uid_form()
            info_form(uid, df)


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
        # utils.clear_temp()
        # print('Database closed.')
