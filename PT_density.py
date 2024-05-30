import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from urllib.request import urlopen
import json
from copy import deepcopy

@st.cache_data
def load_data(path, layer):
    df = gpd.read_file(path, layer=layer)
    return df

# Load the GeoPackage file
# gdf = gpd.read_file('./data/erreichbarkeit-oev_2056.gpkg', layer='Reisezeit_Erreichbarkeit')
gdf_raw = load_data('./data/erreichbarkeit-oev_2056.gpkg', 'Reisezeit_Erreichbarkeit')  # for speed
gdf = deepcopy(gdf_raw) # for security
# select only APPENZELL INNERROHDEN
APPENZELL = gdf.iloc[4163:4176,:]  # according to a visual inspection these are the indexes corresponding to AI
# Ensure the GeoDataFrame is in WGS84 (latitude and longitude) format
if APPENZELL.crs != "EPSG:4326":
    APPENZELL = APPENZELL.to_crs("EPSG:4326")

 


# Display in Streamlit
st.title("Migros locations in Appenzell Innerhoden")

st.write('This app aims at finding the best places to create new Migros stores. Following assumptions are made:\n - Area of interest is limited to the Cannton of Appenzell Innerrohden, \n - Scope is limited at supermarkets / groceries stores (no DIY stores e.g.)')
st.write('The analysis is based on: \n - the density of existing stores, \n - the presence of competitors,\n - the population density, \n - as well as the accessibility by public transport.')

# Layout: Checkboxes to choose which layer to display:
st.sidebar.subheader('Layers')
PT = st.sidebar.checkbox('Public tranport density')
st.sidebar.checkbox('Population density')
st.sidebar.checkbox('Competitors')
st.sidebar.checkbox('Migros stores')


# empty BASE map:
#################################################
# Create a base map figure
base_map = go.Figure(go.Scattermapbox())
# Set up the layout for the base map
base_map.update_layout(
    mapbox_style="open-street-map",
    mapbox_zoom=10,  # Adjust zoom level
    mapbox_center={"lat": APPENZELL.geometry.centroid.y.mean(), "lon": APPENZELL.geometry.centroid.x.mean()}  # Adjust center (latitude, longitude)
)
# Show the base map
st.plotly_chart(base_map, use_container_width=True)


# Layer Public transport
############################################
# Create the layer
PT_layer = px.choropleth_mapbox(
    APPENZELL,
    geojson=APPENZELL.geometry,
    locations=APPENZELL.index,
    color="OeV_Erreichb_EW",  # Replace with the name of a column to color by
    mapbox_style="open-street-map",
    center={"lat": APPENZELL.geometry.centroid.y.mean(), "lon": APPENZELL.geometry.centroid.x.mean()},
    zoom=10,  # Adjust zoom level as needed
    opacity=0.5,
)
# Add the Public transport trace to the base map, IF CHECKED:
if PT == True: 
    base_map.add_trace(PT_layer.data[0])
    st.plotly_chart(base_map, use_container_width=True)
else:
    pass






