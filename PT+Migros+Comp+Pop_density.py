import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from urllib.request import urlopen
import json
from copy import deepcopy
from shape;y.geometry import Polygon

# load little files
MIGROS = pd.read_csv('./data/Migros_Appenzell_Innerrhoden.csv')
COMP = pd.read_csv('./data/Migros_Supermarket_Competitors_Appenzell_Innerrhoden_Filtered.csv')

@st.cache_data
def load_data(path, layer):
    df = gpd.read_file(path, layer=layer)
    return df

@st.cache_data
def load_statpop_data():
    # Define the paths to your data files
    filtered_csv_path = 'path/to/filtered_appenzell_innerrhoden.csv'

    # Load the filtered data
    filtered_data = pd.read_csv(filtered_csv_path)

    # Create hectare-sized squares around each point
    def create_hectare_square(lat, lon):
        side_length = 0.001  # Adjust this value based on latitude if needed
        half_side = side_length / 2
        return Polygon([
            (lon - half_side, lat - half_side),
            (lon + half_side, lat - half_side),
            (lon + half_side, lat + half_side),
            (lon - half_side, lat + half_side)
        ])

    # Apply the function to create a GeoDataFrame with hectare-sized squares
    filtered_data['geometry'] = filtered_data.apply(lambda row: create_hectare_square(row['latitude'], row['longitude']), axis=1)
    squares_gdf = gpd.GeoDataFrame(filtered_data, geometry='geometry')

    # Set the CRS to WGS84
    squares_gdf.set_crs(epsg=4326, inplace=True)

    # Convert GeoDataFrame to GeoJSON
    squares_geojson = squares_gdf.to_json()

    # Ensure that the GeoJSON features have unique IDs that match the DataFrame's index
    geojson_data = json.loads(squares_gdf.to_json())
    for i, feature in enumerate(geojson_data['features']):
        feature['id'] = str(i)
        feature['properties']['id'] = str(i)
    
    return squares_gdf, geojson_data


# Load the GeoPackage file
gdf_raw = load_data('./data/erreichbarkeit-oev_2056.gpkg', 'Reisezeit_Erreichbarkeit')  # for speed
gdf = deepcopy(gdf_raw) # for security
# select only APPENZELL INNERROHDEN
APPENZELL = gdf.iloc[4163:4176,:]  # according to a visual inspection these are the indexes corresponding to AI
# Ensure the GeoDataFrame is in WGS84 (latitude and longitude) format
if APPENZELL.crs != "EPSG:4326":
    APPENZELL = APPENZELL.to_crs("EPSG:4326")

 # Load StatPop data
squares_gdf, geojson_data = load_statpop_data()


# Display in Streamlit
st.title("Migros locations in Appenzell Innerrhoden")

st.write('This app aims at finding the best places to create new Migros stores. Following assumptions are made:\n - Area of interest is limited to the Canton of Appenzell Innerrohden, \n - Scope is limited to supermarkets / groceries stores (no DIY stores e.g.)')
st.write('The analysis is based on: \n - the density of existing stores, \n - the presence of competitors,\n - the population density, \n - as well as the accessibility by public transport.')

# Layout: Checkboxes to choose which layer to display:
st.sidebar.subheader('Layers')
checkbox_PT = st.sidebar.checkbox('Accessibility by public tranport')
checkbox_POP = st.sidebar.checkbox('Population density')
checkbox_COMP = st.sidebar.checkbox('Competitors')
checkbox_MIGROS =st.sidebar.checkbox('Migros stores')
checkbox_StatPop = st.checkbox("Show StatPop Layer")



# EMPTY BASE map:
#################################################
def create_base_map():
    base_map = go.Figure(go.Scattermapbox())
    # Set up the layout for the base map
    base_map.update_layout(
        mapbox_style="open-street-map",
        mapbox_zoom=9.5, 
        mapbox_center={"lat": APPENZELL.geometry.centroid.y.mean(), "lon": APPENZELL.geometry.centroid.x.mean()}
    )
    return base_map

# Initialize base map if not in session state
if 'base_map' not in st.session_state:
    st.session_state.base_map = create_base_map()
    
# Layer Public transport
############################################
def add_PT(base_map):
    PT_layer = px.choropleth_mapbox(
        APPENZELL,
        geojson=APPENZELL.geometry,
        locations=APPENZELL.index,
        color="OeV_Erreichb_EW",  
        mapbox_style="open-street-map",
        center={"lat": APPENZELL.geometry.centroid.y.mean(), "lon": APPENZELL.geometry.centroid.x.mean()},
        zoom=9.5, 
        opacity=0.5,
        labels={'OeV_Erreichb_EW': 'Public Transport Accessibility'}
    )
    PT_layer.update_traces(showlegend= True, name = 'Public Transport Accessibility')
    base_map.add_trace(PT_layer.data[0])
    return base_map

# Layer COMPETITORS
############################################
def add_COMP(base_map):
    COMP_layer = go.Scattermapbox(
    lat=COMP['Latitude'],  
    lon=COMP['Longitude'],  
    mode='markers', 
    marker=dict(size=10,  color='red', opacity= 0.7), 
    text= COMP['Name'],
    hoverinfo='text',
    name="Competitors"   
    )
    base_map.add_trace(COMP_layer)
    return base_map

# Layer MIGROS
############################################
def add_MIGROS(base_map):
    MIGROS_layer = go.Scattermapbox(
    lat=MIGROS['Latitude'],  
    lon=MIGROS['Longitude'],  
    mode='markers',  
    marker=dict(size=10,  color='green', opacity= 0.7), 
    text= MIGROS['Name'],
    hoverinfo='text',
    name = "Migros"   
    )
    base_map.add_trace(MIGROS_layer)
    return base_map

# Layer Stat_Pop
#############################################
def add_StatPop(base_map, geojson_data, squares_gdf):
    statpop_layer = go.Choroplethmapbox(
        geojson=geojson_data,
        locations=squares_gdf.index.astype(str),
        z=squares_gdf['B22BTOT'],
        colorscale="Viridis",
        marker_opacity=0.5,
        marker_line_width=0,
        name="StatPop"
    )
    base_map.add_trace(statpop_layer)
    return base_map



# Add the layers to the base map, IF CHECKED:
if checkbox_PT:
    st.session_state.base_map = add_PT(st.session_state.base_map)
if checkbox_COMP:
    st.session_state.base_map = add_COMP(st.session_state.base_map)
if checkbox_MIGROS:
    st.session_state.base_map = add_MIGROS(st.session_state.base_map)
if checkbox_POP:
    st.session_state.base_map = add_StatPop(st.session_state.base_map, geojson_data, squares_gdf)
if not any([checkbox_PT, checkbox_COMP, checkbox_MIGROS]):
    st.session_state.base_map = create_base_map()

# Update legend and layout only once at the end of the code
st.session_state.base_map.update_layout(
    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01
    )
)
# and display the chart:
st.plotly_chart(st.session_state.base_map, use_container_width=True)

st.subheader('Data sources')
st.write('Accessibility per traffic zone in public transport depending on the public transport travel times from all zones in Switzerland to the traffic zone and the number of inhabitants and jobs in the traffic zone. Source: National Passenger Traffic Model (NPVM) of DETEC.:\n https://data.geo.admin.ch/browser/index.html#/collections/ch.are.erreichbarkeit-oev?.language=en')




