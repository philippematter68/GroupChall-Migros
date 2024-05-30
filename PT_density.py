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
st.title("Migros locations in Appenzell Innerrhoden")

st.write('This app aims at finding the best places to create new Migros stores. Following assumptions are made:\n - Area of interest is limited to the Canton of Appenzell Innerrohden, \n - Scope is limited to supermarkets / groceries stores (no DIY stores e.g.)')
st.write('The analysis is based on: \n - the density of existing stores, \n - the presence of competitors,\n - the population density, \n - as well as the accessibility by public transport.')

# Layout: Checkboxes to choose which layer to display:
st.sidebar.subheader('Layers')
PT = st.sidebar.checkbox('Accessibility by public tranport')
st.sidebar.checkbox('Population density')
st.sidebar.checkbox('Competitors')
st.sidebar.checkbox('Migros stores')


# empty BASE map:
#################################################
# Create a base map figure

def create_base_map():
    base_map = go.Figure(go.Scattermapbox())
    # Set up the layout for the base map
    base_map.update_layout(
        mapbox_style="open-street-map",
        mapbox_zoom=9.5,  # Adjust zoom level
        mapbox_center={"lat": APPENZELL.geometry.centroid.y.mean(), "lon": APPENZELL.geometry.centroid.x.mean()}  # Adjust center (latitude, longitude)
    )
    return base_map

# # Initialize the base map in session state if not already present
# if 'base_map' not in st.session_state:
#     st.session_state.base_map = create_base_map()

# Layer Public transport
############################################
# Create the layer
def add_PT(base_map):
    PT_layer = px.choropleth_mapbox(
        APPENZELL,
        geojson=APPENZELL.geometry,
        locations=APPENZELL.index,
        color="OeV_Erreichb_EW",  # Replace with the name of a column to color by
        mapbox_style="open-street-map",
        center={"lat": APPENZELL.geometry.centroid.y.mean(), "lon": APPENZELL.geometry.centroid.x.mean()},
        zoom=9.5,  # Adjust zoom level as needed
        opacity=0.5,
    )
    base_map.add_trace(PT_layer.data[0])
    return base_map

# Add the Public transport trace to the base map, IF CHECKED:
if PT == True: 
    st.session_state.base_map = add_PT(st.session_state.base_map)
else:
    st.session_state.base_map = create_base_map()



# 
st.plotly_chart(st.session_state.base_map, use_container_width=True)

st.subheader('Data sources')
st.write('Accessibility by public transport: https://data.geo.admin.ch/browser/index.html#/collections/ch.are.erreichbarkeit-oev?.language=en')




