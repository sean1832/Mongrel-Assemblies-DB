import streamlit as st
from backend import db_handler
import file_io
import utils


def compare_dataframes(df_original, df_modified):
    """Compares two DataFrames and returns a list of modified data."""
    modified_data = []

    # Iterate through each row in the original DataFrame
    for idx, row in df_original.iterrows():
        # If the row is not equal to the corresponding row in the modified DataFrame
        if not row.equals(df_modified.loc[idx]):
            # Get the modified row
            modified_row = df_modified.loc[idx]
            # Get the uid and student_number from the original row
            uid = row['uid']
            student_number = row['student_number']

            # Get the modified fields
            modified_fields = {field: modified_row[field] for field in df_original.columns if
                               row[field] != modified_row[field]}

            # Append the result
            modified_data.append({
                'uid': uid,
                'student_number': student_number,
                'modified_fields': modified_fields
            })

    return modified_data


def filter_data(df, filter_dict):
    """Filters the data in the DataFrame."""
    # Get the filter keys
    filter_keys = filter_dict.keys()

    # Loop through the filter keys
    for key in filter_keys:
        # Get the filter value
        filter_value = filter_dict[key]

        # If the filter value is not empty
        if filter_value != '':
            # Check the data type of the column
            if df[key].dtype == 'object':  # String columns
                # Replace NaN with a placeholder and then filter
                df = df[df[key].fillna('PLACEHOLDER').str.contains(filter_value, case=False)]
            elif df[key].dtype in ['int64', 'float64']:  # Numeric columns
                try:
                    numeric_value = float(filter_value)
                    df = df[(df[key] == numeric_value) | df[key].isna()]
                except ValueError:
                    # If the filter value can't be converted to a number, skip filtering for this column
                    pass
            elif df[key].dtype == 'bool':  # Boolean columns
                bool_value = filter_value.lower() in ['true', 'yes', '1']
                df = df[(df[key] == bool_value) | df[key].isna()]

    return df


def handel_update(filtered_df, modified_df):
    try:
        modified_data = compare_dataframes(filtered_df, modified_df)
        if len(modified_data) == 0:
            st.warning("⚠️ No changes detected!")
            return
        else:
            delete_count = 0
            update_count = 0

            # check if modified_fields contains delete
            for data in modified_data:
                if 'delete' in data['modified_fields']:
                    if data['modified_fields']['delete'] == True:
                        db_handler.delete_data(data['uid'], data['student_number'])
                        delete_count += 1
                else:
                    # add current time to modified_fields
                    data['modified_fields']['time'] = utils.get_current_time()
                    db_handler.update_data(data['modified_fields'], data['uid'], data['student_number'])
                    update_count += 1

            st.success(
                f"✅ Successfully updated ({update_count}) and deleted ({delete_count}) items to database!)")
            st.cache_data.clear()
            st.experimental_rerun()
    except Exception as e:
        st.error(f"❌ Error: {e}, Could not update database! Try again, or contact the developer.")


def table(container):
    """Creates the database table."""
    with container:
        if st.button("🔃 Refresh database"):
            st.cache_data.clear()
            st.experimental_rerun()

        with st.spinner("fetching from database..."):
            # fetch data from database
            order_by = ['delete', 'student_number', 'spec_id', 'name', 'uid', 'material', 'amount', 'unit', 'notes',
                        'source', 'source_notes', 'source_year', 'source_latitude', 'source_longitude', 'origin_country', 'source_state', 'source_city',
                        'origin_name', 'origin_notes', 'origin_year', 'origin_latitude', 'origin_longitude', 'origin_country', 'origin_state', 'origin_city',
                        'images', '3d_model', 'time', 'model_scale']
            original_df = db_handler.get_data(order_by)
            original_df['delete'] = False

        col1, col2 = st.columns(2)
        with col1:
            filter_key = st.selectbox("Filter by", options=original_df.columns, key='filter_by')
        with col2:
            filter_val = st.text_input("Filter value", key='filter_value')

        # Filter the data for editing
        filtered_df = filter_data(original_df.copy(), {filter_key: filter_val})

        # Get list of column names
        df_cols = original_df.columns.tolist()

        # Initialize column_config dictionary
        column_config = {}

        # Loop through the column names
        for col in df_cols:
            if 'images' in col:  # if column is an images column
                column_config[col] = st.column_config.ImageColumn()
            elif '3d_model' in col:  # if column is a 3d_model column
                column_config[col] = st.column_config.LinkColumn(
                    "3D Model", help="This is a link to the 3D model", disabled=True
                )
            elif 'spec_id' in col:  # if column is a spec_id column
                column_config[col] = st.column_config.TextColumn()
            elif 'name' in col:  # if column is a name column
                column_config[col] = st.column_config.TextColumn()
            elif 'material' in col:  # if column is a material column
                column_config[col] = st.column_config.TextColumn()
            elif 'amount' in col:  # if column is a amount column
                column_config[col] = st.column_config.NumberColumn()
            elif 'unit' in col:  # if column is a unit column
                column_config[col] = st.column_config.TextColumn()
            elif 'notes' in col:  # if column is a notes column
                column_config[col] = st.column_config.TextColumn()
            elif 'model_scale' in col:  # if column is a model_scale column
                column_config[col] = st.column_config.SelectboxColumn(
                    options=["mm", "cm", "m"],
                    default="mm"
                )

            elif 'source_name' in col:  # if column is a source column
                column_config[col] = st.column_config.TextColumn()
            elif 'source_notes' in col:  # if column is a shed_id column
                column_config[col] = st.column_config.TextColumn()
            elif 'source_year' in col:  # if column is a source_year column
                column_config[col] = st.column_config.NumberColumn()
            elif 'source_latitude' in col:  # if column is a source_lat column
                column_config[col] = st.column_config.NumberColumn()
            elif 'source_longitude' in col:  # if column is a source_long column
                column_config[col] = st.column_config.NumberColumn()
            elif 'source_country' in col:  # if column is a source_lat column
                column_config[col] = st.column_config.TextColumn()
            elif 'source_state' in col:  # if column is a source_lat column
                column_config[col] = st.column_config.TextColumn()
            elif 'source_city' in col:  # if column is a source_lat column
                column_config[col] = st.column_config.TextColumn()

            elif 'origin_name' in col:  # if column is a origin column
                column_config[col] = st.column_config.TextColumn()
            elif 'origin_notes' in col:  # if column is a shed_id column
                column_config[col] = st.column_config.TextColumn()
            elif 'origin_year' in col:  # if column is a origin_year column
                column_config[col] = st.column_config.NumberColumn()
            elif 'origin_latitude' in col:  # if column is a origin_long column
                column_config[col] = st.column_config.NumberColumn()
            elif 'origin_longitude' in col:  # if column is a origin_lat column
                column_config[col] = st.column_config.NumberColumn()
            elif 'origin_country' in col:  # if column is a origin_lat column
                column_config[col] = st.column_config.TextColumn()
            elif 'origin_state' in col:  # if column is a origin_lat column
                column_config[col] = st.column_config.TextColumn()
            elif 'origin_city' in col:  # if column is a origin_lat column
                column_config[col] = st.column_config.TextColumn()

            elif 'delete' in col:
                column_config[col] = st.column_config.CheckboxColumn()

        modified_df = st.data_editor(
            filtered_df,
            column_config=column_config,
            use_container_width=True,
            disabled=['uid', 'student_number', 'time'],
        )

        col1, col2 = st.columns([0.2, 1])
        with col1:
            if st.button('⬆️ Update changes'):
                handel_update(filtered_df, modified_df)
        with col2:
            col3, col4 = st.columns([0.2, 1])
            with col3:
                file_io.export_to_csv(original_df, 'database')
            with col4:
                file_io.export_to_excel(original_df, "database")
        return original_df
