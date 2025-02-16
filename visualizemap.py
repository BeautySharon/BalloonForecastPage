# 导入必要的库
import pandas as pd
import folium
import random

# 读取历史轨迹数据（清洗过的真实数据）
history_file = "Datafile/cleaned_balloon_data.csv"  # 替换为你的路径
df_history = pd.read_csv(history_file)

# 读取预测数据（仅用于未来轨迹）
forecast_file = "Datafile/BalloonForecast.csv"  # 替换为你的路径
df_forecast = pd.read_csv(forecast_file)

dangerous_balloons_file = "Datafile/dangerous_balloons.csv"  # Replace with actual path
df_dangerous_balloons = pd.read_csv(dangerous_balloons_file)
affected_aircraft_file = "Datafile/affected_aircraft.csv"  # Replace with actual path
df_affected_aircraft = pd.read_csv(affected_aircraft_file)

# 计算地图中心点（所有气球的平均经纬度）
map_center = [df_history["latitude"].mean(), df_history["longitude"].mean()]

# 创建地图
m = folium.Map(location=map_center, zoom_start=3, tiles="OpenStreetMap")

# 生成颜色映射，每个气球分配一个唯一的颜色
balloon_ids = df_history["balloon_id"].unique()
balloon_ids = sorted(balloon_ids, key=lambda x: int(x.split("_")[-1]))  # 假设气球 ID 形如 "balloon_123"
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
        "/Users/lvsihui/Desktop/BalloonForecast/Datafile/plane.jpg",  # Airplane icon URL
        icon_size=(35, 35)  # Adjust icon size
    )
    
    folium.Marker(
        [row["latitude"], row["longitude"]],
        popup=f"✈ Affected Aircraft {row['icao']}<br>Velocity: {row['velocity']} km/h<br>Heading: {row['heading']}°<br>Vertical Rate: {row['vertical_rate']} m/s",
        icon=airplane_icon,
    ).add_to(m)


# 遍历每个气球并添加历史轨迹
for balloon_id in balloon_ids:
    df_balloon_track = df_history[df_history["balloon_id"] == balloon_id]

    # 获取历史轨迹坐标
    past_coordinates = list(zip(df_balloon_track["latitude"], df_balloon_track["longitude"]))

    # 创建 FeatureGroup（每个气球独立的图层）
    balloon_layer = folium.FeatureGroup(name=f"Balloon {balloon_id}",show=False)

    # 添加历史轨迹线（蓝色）
    folium.PolyLine(past_coordinates, color=color_map[balloon_id], weight=2.5, opacity=0.7, tooltip=f"Past Path: {balloon_id}").add_to(balloon_layer)

    # 在气球起点标记（绿色）
    folium.Marker(past_coordinates[0], popup=f"Start: {balloon_id}", icon=folium.Icon(color="green")).add_to(balloon_layer)

    # 在气球终点标记（当前最新位置，蓝色）
    folium.Marker(past_coordinates[-1], popup=f"Current: {balloon_id}", icon=folium.Icon(color="blue")).add_to(balloon_layer)

    # 计算并添加未来轨迹（基于 `predicted_speed_kmh` 和 `predicted_direction_deg`）
    df_future = df_forecast[df_forecast["balloon_id"] == balloon_id]

    if not df_future.empty and "predicted_speed_kmh" in df_future.columns and "predicted_direction_deg" in df_future.columns:
        future_coordinates = [past_coordinates[-1]]  # 未来轨迹的起点是历史轨迹的终点
        lat, lon = past_coordinates[-1]  # 以当前最新的气球坐标作为起点

        # 获取气球的预测速度和方向，并跳过 NaN 值
        speed_values = df_future["predicted_speed_kmh"].dropna()
        direction_values = df_future["predicted_direction_deg"].dropna()

        if not speed_values.empty and not direction_values.empty:
            avg_speed = speed_values.mean()
            avg_direction = direction_values.mean()

            # 计算未来 1 小时的位置（假设气球按当前方向和速度移动）
            for i in range(1, 4):  # 预测未来 1h, 2h, 3h
                lat += (avg_speed / 1000) * 0.1  # 0.1 是缩放因子
                lon += (avg_speed / 1000) * 0.1
                future_coordinates.append((lat, lon))  # 未来轨迹点

            # 仅在 future_coordinates 有效时绘制轨迹
            if len(future_coordinates) > 1:
                folium.PolyLine(future_coordinates, color="red", weight=2.5, opacity=0.7, tooltip=f"Future Path: {balloon_id}").add_to(balloon_layer)
                folium.Marker(future_coordinates[-1], popup=f"Predicted Future: {balloon_id}", icon=folium.Icon(color="red")).add_to(balloon_layer)

    # 添加到地图
    balloon_layer.add_to(m)

# 添加图层控制按钮（右上角）
folium.LayerControl().add_to(m)

search_box_html = """
<div style="position: fixed; top: 10px; right: 20px; z-index:9999; 
            background:white; padding:10px; border-radius:8px; 
            box-shadow: 2px 2px 10px rgba(0,0,0,0.3); 
            display: flex; align-items: center; gap: 5px;">
    
    <input type="text" id="balloonSearch" onkeyup="searchBalloon()" 
           placeholder="🔍 Search Balloon ID..." 
           style="width:180px; padding: 6px; border-radius:5px; border: 1px solid #ccc;">
    
    <button onclick="clearSearch()" 
            style="background: #ff4d4d; color: white; border: none; 
                   padding: 6px 10px; border-radius:5px; cursor: pointer;">
        ✖
    </button>

    <button onclick="toggleAllLayers(true)" 
            style="background: #4CAF50; color: white; border: none; 
                   padding: 6px 12px; border-radius:5px; cursor: pointer;">
        全选
    </button>

    <button onclick="toggleAllLayers(false)" 
            style="background: #f44336; color: white; border: none; 
                   padding: 6px 12px; border-radius:5px; cursor: pointer;">
        取消全选
    </button>
</div>
"""

full_screen_js = """
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

function clearSearch() {
    document.getElementById('balloonSearch').value = "";
    searchBalloon();
}

function toggleAllLayers(selectAll) {
    var map = document.querySelector(".leaflet-container")._leaflet_map;
    var layers = document.getElementsByClassName('leaflet-control-layers-selector');
    var layerControl = document.querySelector(".leaflet-control-layers-list");

    for (var i = 0; i < layers.length; i++) {
        if (layers[i].type === 'checkbox') {
            layers[i].checked = selectAll;  // UI 选中或取消
            layers[i].dispatchEvent(new Event('change')); 

            // **手动获取图层名称**
            var layerName = layers[i].nextSibling ? layers[i].nextSibling.innerText.trim() : "";
            
            map.eachLayer(function (layer) {
                if (layer.options && layer.options.name === layerName) {
                    if (selectAll && !map.hasLayer(layer)) {
                        map.addLayer(layer);  // **真正显示**
                    } else if (!selectAll && map.hasLayer(layer)) {
                        map.removeLayer(layer);  // **真正隐藏**
                    }
                }
            });
        }
    }

    // **使用 setTimeout 强制触发 Leaflet 重新渲染**
    setTimeout(function () {
        map.invalidateSize();  // 重新计算地图大小，防止 UI 不更新
        var layerControlButton = document.querySelector('.leaflet-control-layers-toggle');
        if (layerControlButton) {
            layerControlButton.click(); // 先关闭
            setTimeout(function () {
                layerControlButton.click(); // 再打开，强制 UI 更新
            }, 500);
        }
    }, 300); // 延迟 300ms 确保 DOM 变化生效
}


// **自动展开图层控制面板**
window.onload = function() {
    setTimeout(function() {
        var layerControlButton = document.querySelector('.leaflet-control-layers-toggle');
        if (layerControlButton) {
            layerControlButton.click();
        }
    }, 1000);
};
</script>
"""

m.get_root().html.add_child(folium.Element(full_screen_js + search_box_html))

# 保存地图
map_path = "Balloon_History_And_Prediction.html"  # 替换为你的路径
m.save(map_path)

# 输出地图路径
print(f"交互式地图已生成: {map_path}")
