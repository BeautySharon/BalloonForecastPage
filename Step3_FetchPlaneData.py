import requests
import pandas as pd

# OpenSky API URL
OPENSKY_API_URL = "https://opensky-network.org/api/states/all"

# Fetch aircraft data
response = requests.get(OPENSKY_API_URL, timeout=10)
aircraft_data = response.json()

# Extract aircraft data
aircraft_states = aircraft_data.get("states", [])

# Process aircraft data
filtered_aircrafts = [
    {
        "icao": ac[0],
        "latitude": ac[6],
        "longitude": ac[5],
        "velocity": ac[9],
        "heading": ac[10],
        "vertical_rate": ac[11],
        "on_ground": ac[8]
    }
    for ac in aircraft_states if ac[6] and ac[5] and (-90 <= ac[6] <= 90) and (-180 <= ac[5] <= 180)
]

# Convert to DataFrame
df_aircraft = pd.DataFrame(filtered_aircrafts)

# Save as CSV
df_aircraft.to_csv("Datafile/aircraft_positions.csv", index=False)
print("✅ Aircraft data saved to 'aircraft_positions.csv'")