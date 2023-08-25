from keplergl import KeplerGl
import geopandas as gpd
from streamlit_keplergl import keplergl_static
import folium
from streamlit_folium import folium_static
import streamlit as st


def get_pos(lat, lng):
    return lat, lng


def static_map(location: dict, zoom=10, data=None):
    # Convert the DataFrame to a GeoDataFrame
    if data is None:
        gdf = gpd.GeoDataFrame({'geometry': []})
    else:
        gdf = gpd.GeoDataFrame(data, geometry=gpd.points_from_xy(data.Longitude, data.Latitude))

    # Configuration for the initial map view
    config = {
        'version': 'v1',
        'config': {
            'mapState': {
                'latitude': location['lat'],  # Initial latitude
                'longitude': location['long'],  # Initial longitude
                'zoom': zoom  # Initial zoom level
            }
        }
    }
    # Create a Kepler.gl map
    map_ = KeplerGl(height=600, config=config)

    # Add the GeoDataFrame to the map
    map_.add_data(data=gdf, name="markers")

    # Display the map in Streamlit
    keplergl_static(map_)

    # Return the map object for further processing if needed
    return map_


def interactive_map(location, markers, zoom_start=16, tiles="Satellite"):
    attr = "Map data © OpenStreetMap contributors"  # Default attribution for OSM
    if tiles == "Satellite":
        tiles = "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
        attr = "Map data © Google"

    m = folium.Map(
        location=[location['lat'], location['long']],
        zoom_start=zoom_start,
        tiles=tiles,
        attr=attr
    )

    for marker in markers:
        folium.Marker(
            [marker['lat'], marker['long']], popup=f"<i>{marker['name']}</i>", tooltip=marker['name']
        ).add_to(m)

    # Add a marker for the searched location
    m.add_child(folium.LatLngPopup())

    # Display the map in Streamlit
    folium_static(m)
    return m


def make_map_responsive():
    responsive = """
                 <style>
                 [title~="st.iframe"] { width: 100%}
                 </style>
                """
    st.markdown(responsive, unsafe_allow_html=True)
