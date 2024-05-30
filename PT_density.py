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
# Create the Plotly map
fig = px.choropleth_mapbox(
    APPENZELL,
    geojson=APPENZELL.geometry,
    locations=APPENZELL.index,
    color="OeV_Erreichb_EW",  # Replace with the name of a column to color by
    mapbox_style="open-street-map",
    center={"lat": APPENZELL.geometry.centroid.y.mean(), "lon": APPENZELL.geometry.centroid.x.mean()},
    zoom=10,  # Adjust zoom level as needed
    opacity=0.5,
)
# Update layout for better presentation
fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})


# Display in Streamlit
st.title("Migros locations in Appenzell Innerhoden")

st.plotly_chart(fig)

