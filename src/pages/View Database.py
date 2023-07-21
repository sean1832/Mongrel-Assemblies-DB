import streamlit as st
import db_handler
import file_io
import sidebar
import auth

sidebar.sidebar()

header = st.container()
body = st.container()
viewer = st.container()

with header:
    st.header('🔥Firebase Database Viewer')
    st.markdown("This page allows you to view the entire database and download the 3D models. Note that this is a `read-only` page, and you cannot edit the database from here.")
    st.info("Contact the **Zeke Zhang** to get access to the database.")
    auth.login()

with body:
    if st.button("🔃 Refresh database"):
        st.cache_data.clear()
    df = db_handler.get_data()

    col1, col2, col3 = st.columns([0.1, 0.1, 1])
    with col1:
        file_io.export_to_csv(df, 'database.csv')
    with col2:
        file_io.export_to_excel(df, "database.xlsx")
    with col3:
        file_io.export_to_json(df, "database.json")

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
                "Download 3D Model", help="This is a link to the 3D model"
            )

    st.dataframe(
        df,
        column_config=column_config,
        use_container_width=True
    )
