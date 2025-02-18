import requests
import json
import pandas as pd
import numpy as np

# Step 1: Fetch Balloon Data
def step1_balloon_original_data():
    print("Step1: Fetching Original Balloon Data")
    def fetch_balloon_data(hours_ago=0):
        """Fetch balloon data from Windborne Systems API."""
        url = f"https://a.windbornesystems.com/treasure/{str(hours_ago).zfill(2)}.json"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if isinstance(data, list):
                return [
                    {
                        "latitude": item[0],
                        "longitude": item[1],
                        "altitude": item[2],
                        "balloon_id": f"balloon_{index}",
                        "hours_ago": hours_ago,
                    }
                    for index, item in enumerate(data) if isinstance(item, list) and len(item) == 3
                ]
        except (requests.RequestException, json.JSONDecodeError) as e:
            print(f"Error fetching data from {url}: {e}")  # Log error instead of silent failure
        return []

    def fetch_full_flight_history(hours=24):
        """Fetch last 'hours' of balloon flight history."""
        return [entry for i in range(hours) for entry in fetch_balloon_data(i)]

    # Fetch last 24 hours of data
    df = pd.DataFrame(fetch_full_flight_history(24))

    # Step 2: Data Cleaning
    df.dropna(inplace=True)  # Remove missing values
    df = df[df["altitude"] > 0]  # Ensure positive altitude
    df = df[(df["latitude"].between(-90, 90)) & (df["longitude"].between(-180, 180))]  # Validate coordinates

    # Step 3: Sort & Interpolate Missing Timestamps
    df.sort_values(by=["balloon_id", "hours_ago"], inplace=True)

    # Fix duplicate timestamps before interpolation
    df = df.drop_duplicates(subset=["balloon_id", "hours_ago"])

    df = df.groupby("balloon_id", group_keys=False).apply(lambda x: x.set_index("hours_ago").interpolate()).reset_index()

    # Step 4: Compute Speed & Direction
    def haversine(lat1, lon1, lat2, lon2):
        """Compute the Haversine distance (km) between two geographic points."""
        R = 6371  # Earth radius in km
        phi1, phi2 = np.radians(lat1), np.radians(lat2)
        delta_phi, delta_lambda = np.radians(lat2 - lat1), np.radians(lon2 - lon1)
        a = np.sin(delta_phi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda / 2) ** 2
        return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    def compute_bearing(lat1, lon1, lat2, lon2):
        """Compute the initial bearing (direction) from point (lat1, lon1) to (lat2, lon2)."""
        phi1, phi2 = np.radians(lat1), np.radians(lat2)
        delta_lambda = np.radians(lon2 - lon1)

        x = np.sin(delta_lambda) * np.cos(phi2)
        y = np.cos(phi1) * np.sin(phi2) - np.sin(phi1) * np.cos(phi2) * np.cos(delta_lambda)
        theta = np.arctan2(x, y)

        return (np.degrees(theta) + 360) % 360  # Normalize to [0, 360]

    # Initialize new columns
    df["speed_kmh"], df["direction_deg"] = 0.0, 0.0  
    df["time_diff"] = df.groupby("balloon_id")["hours_ago"].diff().abs().fillna(1)  # Avoid NaN errors

    # Compute speed and direction considering time gaps
    for balloon_id, balloon_df in df.groupby("balloon_id"):
        indices = balloon_df.index
        for i in range(1, len(indices)):
            lat1, lon1 = df.loc[indices[i-1], ["latitude", "longitude"]]
            lat2, lon2 = df.loc[indices[i], ["latitude", "longitude"]]
            time_diff = df.loc[indices[i], "time_diff"]

            if time_diff > 0:
                df.at[indices[i], "speed_kmh"] = haversine(lat1, lon1, lat2, lon2) / time_diff
                df.at[indices[i], "direction_deg"] = compute_bearing(lat1, lon1, lat2, lon2)

    # Step 5: Fix Initial Speed & Direction for Each 
    df["speed_kmh"] = df["speed_kmh"].clip(upper=500)  # Cap speed at 500 km/h
    for balloon_id, balloon_df in df.groupby("balloon_id"):
        first_idx = balloon_df.index[0]
        if df.at[first_idx, "speed_kmh"] == 0.0 and len(balloon_df) > 1:
            df.at[first_idx, "speed_kmh"] = df.at[balloon_df.index[1], "speed_kmh"]
            df.at[first_idx, "direction_deg"] = df.at[balloon_df.index[1], "direction_deg"]

    # Fill any remaining NaN directions with forward-fill
    df["direction_deg"] = df.groupby("balloon_id")["direction_deg"].ffill()

    # Step 6: Save Cleaned Data (Updated File Path)
    csv_filename = "Datafile/cleaned_balloon_data.csv"
    df.to_csv(csv_filename, index=False)
    print(f"Processed data saved to {csv_filename}")
    print("Step1: Fetching Original Balloon Data Completed")
