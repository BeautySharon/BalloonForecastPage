# Import necessary libraries
import pandas as pd
import folium
import random
import re

def Step6_visualizemap():
    print("Step6: Visualizing Map")
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
    balloon_ids = sorted(balloon_ids, key=lambda x: int(x.split("_")[-1]))  # Assuming balloon ID is in the form "balloon_123"
    colors = [f"#{random.randint(0, 255):02x}{random.randint(0, 255):02x}{random.randint(0, 255):02x}" for _ in balloon_ids]
    color_map = dict(zip(balloon_ids, colors))

    # # Display dangerous balloons
    # for _, row in df_dangerous_balloons.iterrows():
    #     folium.Marker(
    #         [row["latitude"], row["longitude"]],
    #         popup=f"⚠ Dangerous Balloon {row['balloon_id']}<br>Closest Aircraft Distance: {row['closest_aircraft_distance_km']:.2f} km",
    #         icon=folium.Icon(color="red", icon="exclamation-triangle"),
    #     ).add_to(m)
    # 遍历危险气球并标记
    # Define color mapping for fixed risk categories
    risk_color_map = {
        "Near Aircraft": "pink",          # High Risk - Red
        "Near Military Base": "orange",    # Military Zone - orange
        "In No-Fly Zone": "purple",      # No-Fly Zone - lightgreen
    }

    # Function to determine the marker color dynamically
    def get_risk_color(risk_text):
        """
        Assigns a color based on risk type.
        - Detects dynamic 'Entered X from Y' format for border crossings.
        - Uses predefined color mapping for other risks.
        """
        if re.match(r"Entered .+ from .+", risk_text):  # Detects country entry format
            return "yellow"  # 🟠 Assign orange for border crossing risk
        return risk_color_map.get(risk_text, "white")  # 

    for _, row in df_dangerous_balloons.iterrows():
        risk_info = f"⚠ Dangerous Balloon {row['balloon_id']}<br>Risk: {row['risk']}"
    
        # 如果是 "Near Aircraft"，添加最近飞机信息
        if row["risk"] == "Near Aircraft" and pd.notna(row["closest_aircraft_distance_km"]):
            risk_info += f"<br>Closest Aircraft Distance: {row['closest_aircraft_distance_km']:.2f} km"
        # Determine marker color dynamically
        marker_color = get_risk_color(row["risk"])
        # 添加气球标记
        folium.Marker(
            [row["latitude"], row["longitude"]],
            popup=risk_info,
            icon=folium.Icon(color=marker_color, icon="exclamation-triangle"),
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
    for balloon_id in balloon_ids:
        df_balloon_track = df_history[df_history["balloon_id"] == balloon_id]

        # Get historical trajectory coordinates
        past_coordinates = list(zip(df_balloon_track["latitude"], df_balloon_track["longitude"]))

        # Create FeatureGroup (independent layer for each balloon)
        balloon_layer = folium.FeatureGroup(name=f"Balloon {balloon_id}", show=False)

        # Add historical trajectory line (blue)
        folium.PolyLine(past_coordinates, color=color_map[balloon_id], weight=2.5, opacity=0.7, tooltip=f"Past Path: {balloon_id}").add_to(balloon_layer)

        # Mark balloon start point (green)
        folium.Marker(past_coordinates[0], popup=f"Current: {balloon_id}", icon=folium.Icon(color="green")).add_to(balloon_layer)

        # Mark balloon end point (current latest position, blue)
        folium.Marker(past_coordinates[-1], popup=f"Start: {balloon_id}", icon=folium.Icon(color="blue")).add_to(balloon_layer)

        # Calculate and add future trajectory (based on `predicted_speed_kmh` and `predicted_direction_deg`)
        df_future = df_forecast[df_forecast["balloon_id"] == balloon_id]

        if not df_future.empty and "predicted_speed_kmh" in df_future.columns and "predicted_direction_deg" in df_future.columns:
            future_coordinates = [past_coordinates[0]]  # Future trajectory start point is the end point of historical trajectory
            lat, lon = past_coordinates[0]  # Use the current latest balloon coordinates as the starting point

            # Get balloon's predicted speed and direction, and skip NaN values
            speed_values = df_future["predicted_speed_kmh"].dropna()
            direction_values = df_future["predicted_direction_deg"].dropna()

            if not speed_values.empty and not direction_values.empty:
                avg_speed = speed_values.mean()
                avg_direction = direction_values.mean()

                # Calculate positions for the next 1 hour (assuming the balloon moves in the current direction and speed)
                for i in range(1, 4):  # Predict for the next 1h, 2h, 3h
                    lat += (avg_speed / 1000) * 0.1  # 0.1 is the scaling factor
                    lon += (avg_speed / 1000) * 0.1
                    future_coordinates.append((lat, lon))  # Future trajectory points

                # Draw trajectory only if future_coordinates is valid
                if len(future_coordinates) > 1:
                    folium.PolyLine(future_coordinates, color="red", weight=2.5, opacity=0.7, tooltip=f"Future Path: {balloon_id}").add_to(balloon_layer)
                    folium.Marker(future_coordinates[-1], popup=f"Predicted Future: {balloon_id}", icon=folium.Icon(color="red")).add_to(balloon_layer)

        # Add to map
        balloon_layer.add_to(m)

    # Add layer control button (top right corner)
    folium.LayerControl(collapsed=False).add_to(m)

    search_box_html = """
    <div style="position: fixed; top: 10px; right: 300px; z-index:9999; 
                background:white; padding:10px; border-radius:8px; 
                box-shadow: 2px 2px 10px rgba(0,0,0,0.3); ">
        <input type="text" id="balloonSearch" onkeyup="searchBalloon()" 
            placeholder="🔍 Search Balloon ID..." 
            style="width:180px; padding: 6px; border-radius:5px; border: 1px solid #ccc;">
    </div>
    """

    search_js = """
    <script>
    function searchBalloon() {
        var input = document.getElementById('balloonSearch').value.toLowerCase().trim();
        var layers = document.getElementsByClassName('leaflet-control-layers-selector');
        
        for (var i = 0; i < layers.length; i++) {
            var label = layers[i].nextSibling ? layers[i].nextSibling.innerText.toLowerCase() : "";
            if (label.includes(input)) {
                layers[i].scrollIntoView({ behavior: 'smooth', block: 'center' });
                layers[i].style.border = "2px solid red";
            } else {
                layers[i].style.border = "none";
            }
        }
    }
    </script>
    """
    legend_html = """
    <div style="position: fixed; bottom: 40px; left: 10px; z-index:9999; 
                display: flex; flex-direction: column; gap: 8px;">
        
        <div style="background:white; padding:10px; border-radius:8px; 
                    box-shadow: 2px 2px 10px rgba(0,0,0,0.3); font-size:14px;">
            <b>📍 Balloon Position Legend</b><br>
            <i class="fa fa-map-marker fa-2x" style="color:lightblue"></i> Start Position <br>
            <i class="fa fa-map-marker fa-2x" style="color:lightgreen"></i> Current Position <br>
            <i class="fa fa-map-marker fa-2x" style="color:red"></i> Predicted Position <br>
        </div>

        <div style="background:white; padding:10px; border-radius:8px; 
                    box-shadow: 2px 2px 10px rgba(0,0,0,0.3); font-size:14px;">
            <b>⚠️ Balloon Risk Legend</b><br>
            <i class="fa fa-map-marker fa-2x" style="color:pink"></i> Near Aircraft <br>
            <i class="fa fa-map-marker fa-2x" style="color:purple"></i> In No-Fly Zone <br>
            <i class="fa fa-map-marker fa-2x" style="color:orange"></i> Near Military Base <br>
            <i class="fa fa-map-marker fa-2x" style="color:yellow"></i> Entered Another Country <br>
        </div>
        
    </div>
    """



    layer_control_buttons = """
    <div style="position: fixed; top: 60px; right: 300px; z-index:9999; 
                background:white; padding:8px; border-radius:8px; 
                box-shadow: 2px 2px 10px rgba(0,0,0,0.3); font-size:14px;">
        <button onclick="selectAllLayers()" style="margin-right: 5px;">✅ Show All</button>
        <button onclick="deselectAllLayers()">❌ Hide All</button>
    </div>
    """

    layer_control_js = """
    <script>
    function toggleLayers(selectAll) {
        var checkboxes = document.getElementsByClassName('leaflet-control-layers-selector');

        requestAnimationFrame(() => {
            for (var i = 0; i < checkboxes.length; i++) {
                if ((selectAll && !checkboxes[i].checked) || (!selectAll && checkboxes[i].checked)) {
                    checkboxes[i].click();
                }
            }
        });
    }

    function selectAllLayers() {
        toggleLayers(true);
    }

    function deselectAllLayers() {
        toggleLayers(false);
    }
    </script>
    """


    m.get_root().html.add_child(folium.Element(search_js + search_box_html + legend_html + layer_control_buttons + layer_control_js))

    # Save map
    map_path = "static/Balloon_History_And_Prediction.html"  # Replace with your path
    m.save(map_path)

    # Output map path
    print(f"Interactive map generated: {map_path}")
    print("Step6_visualizemap Completed")