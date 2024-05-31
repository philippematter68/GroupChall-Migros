import requests
import pandas as pd
import time

# Read the API key from the file
api_key_path = r"C:\Users\hellr\Documents\API Keys\Google Maps API Key\Google Key.txt"
with open(api_key_path, 'r') as file:
    api_key = file.read().strip()

# Verify the API key
if not api_key or api_key == "YOUR_API_KEY":
    print("The API key is missing or incorrect. Please update the key in the file and try again.")
    exit()

# Define the coordinates for Appenzell Innerrhoden (main part and "islands")
locations = [
    {"location": "47.3165,9.4167", "radius": 13000},  # Main part
    {"location": "47.343,9.431", "radius": 5000},     # First island area
    {"location": "47.337,9.381", "radius": 5000}      # Second island area
]

# Define the search query for all supermarkets
search_query = "Migros"

# Define the URL for the Google Places API
places_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

# Function to make a request to the Google Places API
def make_request(url, params):
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

# Initialize an empty list to store results
results = []

# Loop through each location and radius
for loc in locations:
    params = {
        "location": loc["location"],
        "radius": loc["radius"],
        "keyword": search_query,
        "key": api_key
    }
    
    # Initial API request
    data = make_request(places_url, params)
    print(f"API response for location {loc['location']}:", data)  # Debugging line
    
    # Extract results
    if data.get("results"):
        results.extend(data["results"])
    
    # Check if there's a next page token
    next_page_token = data.get("next_page_token")
    
    # Handle pagination
    while next_page_token:
        # Google Places API requires a short delay before making a request with the next page token
        time.sleep(2)
        
        params["pagetoken"] = next_page_token
        data = make_request(places_url, params)
        print(f"Next page API response for location {loc['location']}:", data)  # Debugging line
        if data.get("results"):
            results.extend(data["results"])
        next_page_token = data.get("next_page_token")

# Extract the relevant information from the results
extracted_results = []
for place in results:
    place_id = place.get("place_id")
    name = place.get("name")
    lat = place["geometry"]["location"]["lat"]
    lng = place["geometry"]["location"]["lng"]
    address = place.get("vicinity")
    extracted_results.append({"Place ID": place_id, "Name": name, "Latitude": lat, "Longitude": lng, "Address": address})

# Convert to a DataFrame
df = pd.DataFrame(extracted_results)

# Filter out any places with "Migros" or "Migrolino" in their names
#df_filtered = df[~df['Name'].str.contains("Migros|Migrolino", case=False, na=False)].copy()

# Print the DataFrame to check the results
#print("Extracted and filtered results DataFrame:", df_filtered)  # Debugging line

# Remove duplicates (if any)
df.drop_duplicates(subset=["Place ID"], inplace=True)

# Save to a CSV file
output_path = r"C:\Users\hellr\Downloads\Migros_Supermarket_Appenzell_Innerrhoden_Around.csv"
df.to_csv(output_path, index=False)

print(f"Data has been saved to {output_path}")
