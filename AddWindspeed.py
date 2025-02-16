import requests
import pandas as pd
import time

# OpenWeather API Key (替换为你的 API Key)
API_KEY = "a351eca8ae07ffc560ad357f61f573f2"

# Function to get wind speed and direction
def get_wind_data(latitude, longitude):
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get("wind", {}).get("speed", None), data.get("wind", {}).get("deg", None)
    else:
        print(f"Failed to fetch data for {latitude}, {longitude}: {response.status_code}")
        return None, None

# Load CSV file
file_path = "/Users/lvsihui/Desktop/BalloonForecast/Datafile/Final_cleaned_balloon_data.csv"
df = pd.read_csv(file_path)

# Create empty lists to store wind data
wind_speeds = []
wind_directions = []

# Iterate through the rows
for _, row in df.iterrows():
    wind_speed, wind_direction = get_wind_data(row["latitude"], row["longitude"])
    wind_speeds.append(wind_speed*3.6)
    wind_directions.append(wind_direction)
    time.sleep(1)  # Prevent API rate limit issues

# Assign collected wind data to the DataFrame
df["wind_speed"] = wind_speeds
df["wind_direction"] = wind_directions

# Save the updated file
updated_file_path = "/Users/lvsihui/Desktop/BalloonForecast/Datafile/Final_cleaned_balloon_data_with_wind.csv"
df.to_csv(updated_file_path, index=False)

print(f"Updated dataset with wind data saved to {updated_file_path}")