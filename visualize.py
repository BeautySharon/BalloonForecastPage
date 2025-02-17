import pandas as pd
import folium
import random

# Read historical trajectory data (cleaned real data)
history_file = "Datafile/cleaned_balloon_data.csv" 
df_history = pd.read_csv(history_file)

# Read forecast data (only for future trajectories)
forecast_file = "Datafile/BalloonForecast.csv"
df_forecast = pd.read_csv(forecast_file)

dangerous_balloons_file = "Datafile/dangerous_balloons.csv" 
df_dangerous_balloons = pd.read_csv(dangerous_balloons_file)
affected_aircraft_file = "Datafile/affected_aircraft.csv" 
df_affected_aircraft = pd.read_csv(affected_aircraft_file)

# Calculate map center point (average latitude and longitude of all balloons)
map_center = [df_history["latitude"].mean(), df_history["longitude"].mean()]

# Create map
m = folium.Map(location=map_center, zoom_start=3, tiles="OpenStreetMap")

# Generate color mapping, assign a unique color to each balloon
balloon_ids = df_history["balloon_id"].unique()
balloon_ids = sorted(balloon_ids, key=lambda x: int(x.split("_")[-1]))
colors = [f"#{random.randint(0, 255):02x}{random.randint(0, 255):02x}{random.randint(0, 255):02x}" for _ in balloon_ids]
color_map = dict(zip(balloon_ids, colors))

# Display dangerous balloons
for _, row in df_dangerous_balloons.iterrows():
    folium.Marker(
        [row["latitude"], row["longitude"]],
        popup=f"⚠ Dangerous Balloon {row['balloon_id']}<br>Closest Aircraft Distance: {row['closest_aircraft_distance_km']:.2f} km",
        icon=folium.Icon(color="red", icon="exclamation-triangle"),
    ).add_to(m)

# Display affected aircraft with airplane icons
for _, row in df_affected_aircraft.iterrows():
    airplane_icon = folium.CustomIcon(
        "Datafile/plane1.png",  # Airplane icon URL
        icon_size=(35, 35)  # Adjust icon size
    )
    
    folium.Marker(
        [row["latitude"], row["longitude"]],
        popup=f"✈ Affected Aircraft {row['icao']}<br>Velocity: {row['velocity']} km/h<br>Heading: {row['heading']}°<br>Vertical Rate: {row['vertical_rate']} m/s",
        icon=airplane_icon,
    ).add_to(m)

# Iterate through each balloon and add historical trajectory
balloon_layers = {}
for balloon_id in balloon_ids:
    df_balloon_track = df_history[df_history["balloon_id"] == balloon_id]
    past_coordinates = list(zip(df_balloon_track["latitude"], df_balloon_track["longitude"]))
    balloon_layer = folium.FeatureGroup(name=f"Balloon {balloon_id}", show=True)
    
    folium.PolyLine(past_coordinates, color=color_map[balloon_id], weight=2.5, opacity=0.7, tooltip=f"Past Path: {balloon_id}").add_to(balloon_layer)
    folium.Marker(past_coordinates[0], popup=f"Current: {balloon_id}", icon=folium.Icon(color="green")).add_to(balloon_layer)
    folium.Marker(past_coordinates[-1], popup=f"Start: {balloon_id}", icon=folium.Icon(color="blue")).add_to(balloon_layer)
    
    balloon_layer.add_to(m)
    balloon_layers[balloon_id] = balloon_layer

folium.LayerControl(collapsed=False).add_to(m)

# Add buttons for selecting/deselecting all layers
buttons_html = """
<div style="position: fixed; bottom: 20px; right: 20px; z-index:9999; ">
    <button onclick="toggleBalloonLayers(true)" style="background: #4CAF50; color: white; padding: 8px; border: none; border-radius: 5px; cursor: pointer;">Show All Balloons</button>
    <button onclick="toggleBalloonLayers(false)" style="background: #f44336; color: white; padding: 8px; border: none; border-radius: 5px; cursor: pointer;">Hide All Balloons</button>
</div>
<script>
function toggleBalloonLayers(show) {
    var map = document.querySelector('.leaflet-container')._leaflet_map;
    var checkboxes = document.getElementsByClassName('leaflet-control-layers-selector');
    var layers = map._layers;
    
    for (var i = 0; i < checkboxes.length; i++) {
        if (checkboxes[i].type === 'checkbox') {
            checkboxes[i].checked = show;
            checkboxes[i].dispatchEvent(new Event('change'));
        }
    }
    
    Object.values(layers).forEach(layer => {
        if (layer.options && layer.options.name && layer.options.name.includes("Balloon")) {
            if (show && !map.hasLayer(layer)) {
                map.addLayer(layer);
            } else if (!show && map.hasLayer(layer)) {
                map.removeLayer(layer);
            }
        }
    });
    
    setTimeout(function() {
        map.invalidateSize();
    }, 300);
}
</script>
"""

m.get_root().html.add_child(folium.Element(buttons_html))

map_path = "static/Balloon_History_And_Prediction.html"
m.save(map_path)

print(f"Interactive map generated: {map_path}")
