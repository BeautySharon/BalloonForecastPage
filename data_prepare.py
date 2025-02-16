import pandas as pd
import numpy as np
# Load dataset
file_path = "/Users/lvsihui/Desktop/BalloonForecast/Datafile/cleaned_balloon_data.csv"
df = pd.read_csv(file_path)

# Sort by balloon_id and hours_ago

df.sort_values(by=["balloon_id", "hours_ago"], ascending=[True, True], inplace=True)

# Extract base data (0 hours ago)
base_df = df[df["hours_ago"] == 0].copy()

# Merge historical data
history_data = df[df["hours_ago"] != 0].pivot(index="balloon_id", columns="hours_ago", values=["speed_kmh", "direction_deg"])
history_data.columns = [f"{col[0]}_{col[1]}h" for col in history_data.columns]
base_df = base_df.merge(history_data, on="balloon_id", how="left")

# Sort final result by balloon_id
# base_df.sort_values(by="balloon_id", inplace=True)
base_df["balloon_id"] = base_df["balloon_id"].astype(str)
base_df = base_df.sort_values(by="balloon_id", key=lambda x: x.str.extract('(\d+)')[0].astype(int))
base_df = base_df[["balloon_id", "latitude", "longitude", "altitude", "speed_kmh", "direction_deg"] + 
                  [col for col in base_df.columns if "speed_kmh_" in col or "direction_deg_" in col]]
# Save cleaned data for LSTM training
ready_file = "/Users/lvsihui/Desktop/BalloonForecast/Datafile/Final_cleaned_balloon_data.csv"
base_df.to_csv(ready_file, index=False)

print(f"Final cleaned dataset saved to {ready_file}")

# Display result
target_columns = ["latitude", "longitude", "altitude", "balloon_id", "speed_kmh", "direction_deg"] + [col for col in base_df.columns if "speed_kmh_" in col or "direction_deg_" in col]
