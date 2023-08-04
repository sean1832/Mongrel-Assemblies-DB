import streamlit as st
import db_handler
import file_io


def compare_dataframes(df_original, df_modified):
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
            modified_fields = {field: modified_row[field] for field in df_original.columns if row[field] != modified_row[field]}

            # Append the result
            modified_data.append({
                'uid': uid,
                'student_number': student_number,
                'modified_fields': modified_fields
            })

    return modified_data
def table(container):
    with container:
        if st.button("🔃 Refresh database"):
            st.cache_data.clear()
            st.experimental_rerun()

        with st.spinner("fetching from database..."):
            # fetch data from database
            order_by = ['student_number', 'spec_id', 'name', 'material', 'amount', 'unit', 'notes', 'uid', 'images',
                        '3d_model', 'time']
            df = db_handler.get_data(order_by)

        col1, col2, col3 = st.columns([0.1, 0.1, 1])
        with col1:
            file_io.export_to_csv(df, 'database')
        with col2:
            file_io.export_to_excel(df, "database")

        # Get list of column names
        df_cols = df.columns.tolist()

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

        modified_df = st.data_editor(
            df,
            column_config=column_config,
            use_container_width=True,
            disabled=['uid', 'student_number', 'time']
        )

        if st.button('⬆️ Update changes'):
            try:
                modified_data = compare_dataframes(df, modified_df)
                if len(modified_data) == 0:
                    st.warning("⚠️ No changes detected!")
                    return
                else:
                    for data in modified_data:
                        db_handler.update_data(data['modified_fields'], data['uid'], data['student_number'])
                    st.success("✅ Successfully updated database!")
                    st.cache_data.clear()
                    st.experimental_rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}, Could not update database! Try again, or contact the developer.")
        return df

