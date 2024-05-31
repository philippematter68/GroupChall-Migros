import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
from urllib.request import urlopen
import json
from shapely.geometry import Polygon
from copy import deepcopy
import plotly.colors as pcolors

# Ensure necessary imports are included at the top


# load little files
MIGROS = pd.read_csv('./data/Migros_Appenzell_Innerrhoden.csv')
COMP = pd.read_csv('./data/Migros_Supermarket_Competitors_Appenzell_Innerrhoden_Filtered.csv')

@st.cache_data
def load_data(path, layer):
    df = gpd.read_file(path, layer=layer)
    return df

@st.cache_data
def load_statpop_data():
    # Define the path to your filtered CSV file
    filtered_csv_path = './data/filtered_appenzell_innerrhoden.csv'

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
    geojson_data = json.loads(squares_gdf.to_json())
    for i, feature in enumerate(geojson_data['features']):
        feature['id'] = str(i)
        feature['properties']['id'] = str(i)

    return squares_gdf, geojson_data

# Load the GeoPackage file
gdf_raw = load_data('./data/erreichbarkeit-oev_2056.gpkg', 'Reisezeit_Erreichbarkeit')  # for speed
gdf = deepcopy(gdf_raw)  # for security
# select only APPENZELL INNERROHDEN
APPENZELL = gdf.iloc[4163:4176, :]  # according to a visual inspection these are the indexes corresponding to AI
# Ensure the GeoDataFrame is in WGS84 (latitude and longitude) format
if APPENZELL.crs != "EPSG:4326":
    APPENZELL = APPENZELL.to_crs("EPSG:4326")

# Load StatPop data
squares_gdf, geojson_data = load_statpop_data()

# Get the "Oranges" color scale
oranges_scale = pcolors.sequential.Oranges

# Create a custom color scale starting from the midpoint of "Oranges"
custom_oranges_scale = oranges_scale[len(oranges_scale)//2:]

# Display in Streamlit
st.title("Migros locations in Appenzell Innerrhoden")

st.write('This app aims at finding the best places to create new Migros stores. Following assumptions are made:\n - Area of interest is limited to the Canton of Appenzell Innerrohden, \n - Scope is limited to supermarkets / groceries stores (no DIY stores e.g.)')
st.write('The analysis is based on: \n - the density of existing stores, \n - the presence of competitors,\n - the population density, \n - as well as the accessibility by public transport.')

# Layout: Checkboxes to choose which layer to display:
st.sidebar.subheader('Layers')
checkbox_PT = st.sidebar.checkbox('Accessibility by public tranport')
checkbox_COMP = st.sidebar.checkbox('Competitors')
checkbox_MIGROS =st.sidebar.checkbox('Migros stores')
checkbox_StatPop = st.sidebar.checkbox("Show StatPop Layer")



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

# Create the base map
base_map = create_base_map()

    
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
        labels={'OeV_Erreichb_EW': 'Public Transport Accessibility'},
        color_continuous_scale="Viridis"
    )
    PT_layer.update_traces(showlegend= True, name = 'Public Transport Accessibility')
    for trace in PT_layer.data:
        trace['coloraxis']='coloraxis1'
    base_map.add_traces(PT_layer.data)
    return base_map

# Layer COMPETITORS
############################################
def add_COMP(base_map):
    COMP_layer = go.Scattermapbox(
    lat=COMP['Latitude'],  
    lon=COMP['Longitude'],  
    mode='markers', 
    marker=dict(size=15,  color='red', opacity= 0.7), 
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
    marker=dict(size=15,  color='green', opacity= 0.7), 
    text= MIGROS['Name'],
    hoverinfo='text',
    name = "Migros"   
    )
    base_map.add_trace(MIGROS_layer)
    return base_map

# Layer StatPop
def add_StatPop(base_map, geojson_data, squares_gdf):
    statpop_layer = go.Choroplethmapbox(
        geojson=geojson_data,
        locations=squares_gdf.index.astype(str),
        z=squares_gdf['B22BTOT'],
        colorscale='Plasma',  # Use custom "Oranges" color scale
        marker_opacity=0.8,
        marker_line_width=0,
        showlegend=True,
        name="Population Density"
    )
    statpop_layer['coloraxis'] = 'coloraxis2'  # Assign to coloraxis2
    base_map.add_trace(statpop_layer)
    return base_map





# Add the layers to the base map, IF CHECKED:
if checkbox_PT:
    base_map = add_PT(base_map)
if checkbox_COMP:
    base_map = add_COMP(base_map)
if checkbox_MIGROS:
    base_map = add_MIGROS(base_map)
if checkbox_StatPop:
    base_map = add_StatPop(base_map, geojson_data, squares_gdf)

# Update layout with custom figure size and horizontal color bars below the figure
base_map.update_layout(
    width=1200,  # Set the desired width
    height=800,  # Set the desired height
    coloraxis1=dict(
        colorscale="Viridis", 
        colorbar=dict(
            title="PT Accessibility",
            orientation="h",  # Horizontal orientation
            x=0.5,  # Centered horizontally
            y=-0.2,  # Position below the figure
            xanchor="center",
            yanchor="top",
            len=0.5  # Length of the color bar
        )
    ),
    coloraxis2=dict(
        colorscale='Plasma',  # Updated to use custom "Oranges" color scale
        colorbar=dict(
            title="Population Density",
            orientation="h",  # Horizontal orientation
            x=0.5,  # Centered horizontally
            y=-0.4,  # Position further below the first color bar
            xanchor="center",
            yanchor="top",
            len=0.5  # Length of the color bar
        )
    ),
    mapbox=dict(
        style="open-street-map",
        zoom=9.5,
        center={"lat": APPENZELL.geometry.centroid.y.mean(), "lon": APPENZELL.geometry.centroid.x.mean()}
    ),
    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01
    )
)





# and display the chart:
st.plotly_chart(base_map, use_container_width=True)


st.subheader('Data sources')
st.write('Accessibility per traffic zone in public transport depending on the public transport travel times from all zones in Switzerland to the traffic zone and the number of inhabitants and jobs in the traffic zone. Source: National Passenger Traffic Model (NPVM) of DETEC.:\n https://data.geo.admin.ch/browser/index.html#/collections/ch.are.erreichbarkeit-oev?.language=en')




