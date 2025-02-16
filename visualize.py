import pandas as pd
import folium
import random

# 读取历史轨迹数据
history_file = "/Users/lvsihui/Desktop/BalloonForecast/Datafile/cleaned_balloon_data.csv"
df_history = pd.read_csv(history_file)

# 读取预测数据
forecast_file = "/Users/lvsihui/Desktop/BalloonForecast/Datafile/BalloonForecast.csv"
df_forecast = pd.read_csv(forecast_file)

# 读取危险气球数据
dangerous_balloons_file = "/Users/lvsihui/Desktop/BalloonForecast/Datafile/dangerous_balloons.csv"
df_dangerous_balloons = pd.read_csv(dangerous_balloons_file)

# 读取受影响飞机数据
affected_aircraft_file = "/Users/lvsihui/Desktop/BalloonForecast/Datafile/affected_aircraft.csv"
df_affected_aircraft = pd.read_csv(affected_aircraft_file)

# 计算地图中心点
map_center = [df_history["latitude"].mean(), df_history["longitude"].mean()]

# 创建地图，使用 Stamen Toner 风格
m = folium.Map(
    location=map_center,
    zoom_start=3,
    tiles="https://stamen-tiles.a.ssl.fastly.net/toner/{z}/{x}/{y}.png",
    attr="Map tiles by <a href='https://stamen.com'>Stamen Design</a>, under <a href='https://creativecommons.org/licenses/by/3.0/'>CC BY 3.0</a>. Data by <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors."
)


# 生成颜色映射，每个气球分配一个唯一的颜色
balloon_ids = df_history["balloon_id"].unique()
colors = [f"#{random.randint(0, 255):02x}{random.randint(0, 255):02x}{random.randint(0, 255):02x}" for _ in balloon_ids]
color_map = dict(zip(balloon_ids, colors))

# **1. 显示危险气球**
for _, row in df_dangerous_balloons.iterrows():
    folium.Marker(
        [row["latitude"], row["longitude"]],
        popup=f"⚠ 危险气球 {row['balloon_id']}<br>最近飞机距离: {row['closest_aircraft_distance_km']:.2f} km",
        icon=folium.Icon(color="red", icon="exclamation-triangle"),
    ).add_to(m)

# **2. 显示受影响的飞机**
for _, row in df_affected_aircraft.iterrows():
    airplane_icon = folium.CustomIcon(
        "/Users/lvsihui/Desktop/BalloonForecast/Datafile/plane.jpg",
        icon_size=(35, 35)
    )
    folium.Marker(
        [row["latitude"], row["longitude"]],
        popup=f"✈ 受影响飞机 {row['icao']}<br>速度: {row['velocity']} km/h<br>航向: {row['heading']}°<br>垂直速度: {row['vertical_rate']} m/s",
        icon=airplane_icon,
    ).add_to(m)

# **3. 解析气球 ID 后的数字，并进行排序**
balloon_ids = sorted(balloon_ids, key=lambda x: int(x.split("_")[-1]))

# **4. 遍历每个气球并添加历史轨迹**
for balloon_id in balloon_ids:
    df_balloon_track = df_history[df_history["balloon_id"] == balloon_id]
    past_coordinates = list(zip(df_balloon_track["latitude"], df_balloon_track["longitude"]))

    # 创建 FeatureGroup（默认不显示）
    balloon_layer = folium.FeatureGroup(name=f"Balloon {balloon_id}", show=False)

    # 添加历史轨迹
    folium.PolyLine(past_coordinates, color=color_map[balloon_id], weight=2.5, opacity=0.7,
                    tooltip=f"Past Path: {balloon_id}").add_to(balloon_layer)

    # 起点（绿色）
    folium.Marker(past_coordinates[0], popup=f"Start: {balloon_id}",
                  icon=folium.Icon(color="green")).add_to(balloon_layer)

    # 终点（蓝色）
    folium.Marker(past_coordinates[-1], popup=f"Current: {balloon_id}",
                  icon=folium.Icon(color="blue")).add_to(balloon_layer)

    # **计算未来轨迹**
    df_future = df_forecast[df_forecast["balloon_id"] == balloon_id]
    if not df_future.empty:
        future_coordinates = [past_coordinates[-1]]
        lat, lon = past_coordinates[-1]
        avg_speed = df_future["predicted_speed_kmh"].dropna().mean()
        avg_direction = df_future["predicted_direction_deg"].dropna().mean()

        # 计算未来 3 小时的位置
        for i in range(1, 4):
            lat += (avg_speed / 1000) * 0.1
            lon += (avg_speed / 1000) * 0.1
            future_coordinates.append((lat, lon))

        if len(future_coordinates) > 1:
            folium.PolyLine(future_coordinates, color="red", weight=2.5, opacity=0.7,
                            tooltip=f"Future Path: {balloon_id}").add_to(balloon_layer)
            folium.Marker(future_coordinates[-1], popup=f"Predicted Future: {balloon_id}",
                          icon=folium.Icon(color="red")).add_to(balloon_layer)

    # 添加图层
    balloon_layer.add_to(m)

# **5. 添加图层控制**
folium.LayerControl().add_to(m)

# **6. 增加搜索功能**
search_box_js = """
<script>
function searchBalloon() {
    var input = document.getElementById('balloonSearch').value.toLowerCase();
    var layers = document.getElementsByClassName('leaflet-control-layers-selector');
    for (var i = 0; i < layers.length; i++) {
        var label = layers[i].nextSibling.innerText.toLowerCase();
        if (label.includes(input)) {
            layers[i].scrollIntoView();
            layers[i].style.border = "2px solid red";
        } else {
            layers[i].style.border = "none";
        }
    }
}
</script>
"""

search_box_html = """
<div style="position: fixed; top: 10px; right: 180px; z-index:9999; background:white; padding:5px; border-radius:5px;">
    <input type="text" id="balloonSearch" onkeyup="searchBalloon()" placeholder="Search Balloon ID..." style="width:150px;">
</div>
"""

# **7. 自动展开图层面板**
auto_expand_js = """
<script>
window.onload = function() {
    setTimeout(function() {
        var layerControlButton = document.querySelector('.leaflet-control-layers-toggle');
        if (layerControlButton) {
            layerControlButton.click();
        }
    }, 500);
};
</script>
"""

# **8. 添加 HTML & JS**
m.get_root().html.add_child(folium.Element(search_box_js + search_box_html + auto_expand_js))

# **9. 保存地图**
map_path = "/Users/lvsihui/Desktop/BalloonForecast/Datafile/Balloon_Map.html"
m.save(map_path)
print(f"交互式地图已生成: {map_path}")
