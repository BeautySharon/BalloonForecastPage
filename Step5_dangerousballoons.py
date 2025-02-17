import pandas as pd
import numpy as np
from scipy.spatial import cKDTree

# File paths
balloon_file = "Datafile/BalloonForecast.csv"  # Replace with your actual file path
aircraft_file = "Datafile/aircraft_positions.csv"  # Replace with your actual file path

# Load data
df_balloons = pd.read_csv(balloon_file)
df_aircraft = pd.read_csv(aircraft_file)

# Ensure required columns exist
if "latitude" not in df_balloons.columns or "longitude" not in df_balloons.columns:
    raise ValueError("Balloon data must contain 'latitude' and 'longitude' columns.")
if "latitude" not in df_aircraft.columns or "longitude" not in df_aircraft.columns:
    raise ValueError("Aircraft data must contain 'latitude' and 'longitude' columns.")

# Convert to NumPy arrays for fast calculations
balloon_coords = df_balloons[['latitude', 'longitude']].to_numpy()
aircraft_coords = df_aircraft[['latitude', 'longitude']].to_numpy()

# Build a KDTree for fast nearest-neighbor lookup
aircraft_tree = cKDTree(aircraft_coords)

# Threshold for dangerous distance
THRESHOLD_DISTANCE_KM = 10

# Lists to store dangerous balloons and affected aircraft
dangerous_balloons = []
affected_aircraft = []

for i, balloon in enumerate(balloon_coords):
    # Query the nearest aircraft
    distance, index = aircraft_tree.query(balloon, k=1)
    closest_distance_km = distance * 111  # Convert degrees to km (~111 km per degree)
    
    if closest_distance_km <= THRESHOLD_DISTANCE_KM:
        dangerous_balloons.append({
            "balloon_id": df_balloons.iloc[i]["balloon_id"],
            "latitude": balloon[0],
            "longitude": balloon[1],
            "closest_aircraft_distance_km": closest_distance_km
        })

        # Add affected aircraft details
        affected_aircraft.append({
            "icao": df_aircraft.iloc[index]["icao"],
            "latitude": df_aircraft.iloc[index]["latitude"],
            "longitude": df_aircraft.iloc[index]["longitude"],
            "velocity": df_aircraft.iloc[index]["velocity"],
            "heading": df_aircraft.iloc[index]["heading"],
            "vertical_rate": df_aircraft.iloc[index]["vertical_rate"],
            "on_ground": df_aircraft.iloc[index]["on_ground"]
        })

# Convert to DataFrames and save results
df_dangerous_balloons = pd.DataFrame(dangerous_balloons)
df_affected_aircraft = pd.DataFrame(affected_aircraft)

df_dangerous_balloons.to_csv("Datafile/dangerous_balloons.csv", index=False)
df_affected_aircraft.to_csv("Datafile/affected_aircraft.csv", index=False)

print("✅ Dangerous balloons saved to 'dangerous_balloons.csv'")
print("✅ Affected aircraft saved to 'affected_aircraft.csv'")
