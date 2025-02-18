import requests
import pandas as pd
import time
from concurrent.futures import ThreadPoolExecutor

# Load dataset
def Step2_BalloonDataCleanWithWind():
    print("Step2: Cleaning Balloon Data with Wind Data")
    file_path = "Datafile/cleaned_balloon_data.csv"
    df = pd.read_csv(file_path)

    # Sort dataset by balloon_id and hours_ago in ascending order
    df.sort_values(by=["balloon_id", "hours_ago"], ascending=[True, True], inplace=True)

    # Extract base data where hours_ago is 0 (current state of balloons)
    base_df = df[df["hours_ago"] == 0].copy()

    # Pivot historical data (speed and direction at different hours ago)
    history_data = df[df["hours_ago"] != 0].pivot(index="balloon_id", columns="hours_ago", values=["speed_kmh", "direction_deg"])
    history_data.columns = [f"{col[0]}_{col[1]}h" for col in history_data.columns]

    # Merge historical data with base data
    base_df = base_df.merge(history_data, on="balloon_id", how="left")

    # Convert balloon_id to numeric for efficient sorting
    base_df["balloon_id"] = base_df["balloon_id"].astype(str)
    base_df["balloon_id_numeric"] = base_df["balloon_id"].str.extract(r'(\d+)')[0].astype(float)
    base_df = base_df.sort_values(by="balloon_id_numeric").drop(columns=["balloon_id_numeric"])

    # Select relevant columns
    selected_columns = ["balloon_id", "latitude", "longitude", "altitude", "speed_kmh", "direction_deg"] + \
                    [col for col in base_df.columns if "speed_kmh_" in col or "direction_deg_" in col]
    base_df = base_df[selected_columns]

    # Save the cleaned dataset
    ready_file = "Datafile/Final_cleaned_balloon_data.csv"
    base_df.to_csv(ready_file, index=False)
    print(f"Final cleaned dataset saved to {ready_file}")

    # OpenWeather API Key
    API_KEY = "a351eca8ae07ffc560ad357f61f573f2"

    # Function to fetch wind speed and direction from OpenWeather API
    def get_wind_data(lat, lon):
        """Fetch wind speed and direction from OpenWeather API."""
        url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        try:
            response = requests.get(url, timeout=5)  # Set timeout to avoid hanging requests
            if response.status_code == 200:
                data = response.json()
                return data.get("wind", {}).get("speed", 0) * 3.6, data.get("wind", {}).get("deg", 0)  # Convert m/s to km/h
            else:
                print(f"Failed to fetch data for {lat}, {lon}: {response.status_code}")
                return None, None
        except requests.RequestException as e:
            print(f"Request error: {e}")
            return None, None

    # Load the cleaned dataset
    file_path = "Datafile/Final_cleaned_balloon_data.csv"
    df = pd.read_csv(file_path)

    # Use ThreadPoolExecutor for parallel API calls
    with ThreadPoolExecutor(max_workers=10) as executor:  # Adjust max_workers based on API rate limit
        wind_data = list(executor.map(get_wind_data, df["latitude"], df["longitude"]))

    # Extract wind speed and direction
    df["wind_speed"], df["wind_direction"] = zip(*wind_data)

    # Save the updated dataset with wind data
    updated_file_path = "Datafile/Final_cleaned_balloon_data_with_wind.csv"
    df.to_csv(updated_file_path, index=False)
    print(f"Updated dataset with wind data saved to {updated_file_path}")
    print("Step2: Completed")
