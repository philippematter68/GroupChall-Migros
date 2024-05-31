import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
import plotly.express as px
import json

# Define the path to the filtered CSV file
filtered_csv_path = r'C:\Users\hellr\Downloads\2022_swiss_statpop\ag-b-00.03-vz2022statpop\filtered_appenzell_innerrhoden.csv'

# Load the filtered data
filtered_data = pd.read_csv(filtered_csv_path)

# Create hectare-sized squares around each point
def create_hectare_square(lat, lon):
    # Size of a hectare in degrees (approx. conversion)
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

# Debugging: Print GeoDataFrame head
print("Squares GeoDataFrame head:")
print(squares_gdf.head())

# Convert GeoDataFrame to GeoJSON
squares_geojson = squares_gdf.to_json()

# Save the GeoJSON to a file for inspection
with open(r'C:\Users\hellr\Downloads\2022_swiss_statpop\squares_geojson.json', 'w') as f:
    json.dump(json.loads(squares_geojson), f, indent=4)

# Ensure that the GeoJSON features have unique IDs that match the DataFrame's index
geojson_data = json.loads(squares_gdf.to_json())
for i, feature in enumerate(geojson_data['features']):
    feature['id'] = str(i)
    feature['properties']['id'] = str(i)

# Create the choropleth map
fig = px.choropleth_mapbox(
    squares_gdf,
    geojson=geojson_data,
    locations=squares_gdf.index.astype(str),
    color='B22BTOT',
    color_continuous_scale="Viridis",
    range_color=(squares_gdf['B22BTOT'].min(), squares_gdf['B22BTOT'].max()),
    mapbox_style="carto-positron",
    featureidkey="properties.id",
    center={"lat": filtered_data['latitude'].mean(), "lon": filtered_data['longitude'].mean()},
    zoom=10,
    opacity=0.5,
    labels={'B22BTOT': 'Population'}
)

# Update layout
fig.update_layout(
    title='Population Density in Appenzell Innerrhoden',
    title_font_size=18,
    margin={"r":0,"t":0,"l":0,"b":0}
)

# Save the figure to an HTML file
output_html = r'C:\Users\hellr\Downloads\2022_swiss_statpop\ag-b-00.03-vz2022statpop\population_density_map.html'
fig.write_html(output_html)

print(f"HTML file saved to {output_html}")
