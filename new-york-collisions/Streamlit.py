import streamlit as st
import folium
from streamlit_folium import folium_static

# Create a Streamlit app
st.title("New York Map with Folium")

# Create a Folium map centered on New York City
ny_map = folium.Map(location=[40.7128, -74.0060], zoom_start=12)

# Display the map in the Streamlit app
folium_static(ny_map)
