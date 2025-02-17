# Import necessary libraries
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error

# Read data
file_path = "Datafile/Final_cleaned_balloon_data_with_wind.csv"  # Replace with your data file path
df = pd.read_csv(file_path)

# Select feature columns (historical data of speed and direction)
feature_cols = ["wind_speed", "wind_direction"] + [
    col for col in df.columns if "speed_kmh_" in col or "direction_deg_" in col
]

# Target variables (future speed and direction)
target_speed = "speed_kmh"
target_direction = "direction_deg"

# Drop rows with NaN values
df_cleaned = df.dropna(subset=feature_cols + [target_speed, target_direction])

# Select features and target variables
X = df_cleaned[feature_cols]
y_speed = df_cleaned[target_speed]
y_direction = df_cleaned[target_direction]

# Split into training and testing sets
X_train, X_test, y_train_speed, y_test_speed = train_test_split(X, y_speed, test_size=0.2, random_state=42)
X_train, X_test, y_train_direction, y_test_direction = train_test_split(X, y_direction, test_size=0.2, random_state=42)

# Train speed prediction model (Random Forest Regressor)
speed_model = RandomForestRegressor(n_estimators=100, random_state=42)
speed_model.fit(X_train, y_train_speed)

# Train direction prediction model (Random Forest Regressor)
direction_model = RandomForestRegressor(n_estimators=100, random_state=42)
direction_model.fit(X_train, y_train_direction)

# Predict speed and direction for the entire dataset
df_cleaned["predicted_speed_kmh"] = speed_model.predict(X)
df_cleaned["predicted_direction_deg"] = direction_model.predict(X)

# Calculate error (RMSE)
speed_rmse = np.sqrt(mean_squared_error(y_test_speed, speed_model.predict(X_test)))
direction_rmse = np.sqrt(mean_squared_error(y_test_direction, direction_model.predict(X_test)))

# Output error
print("Speed prediction RMSE:", speed_rmse)
print("Direction prediction RMSE:", direction_rmse)

# Save CSV file with prediction data
output_file_path = "Datafile/BalloonForecast.csv"  # Replace with your desired file name
df_cleaned.to_csv(output_file_path, index=False)

print(f"Prediction results saved to {output_file_path}")
