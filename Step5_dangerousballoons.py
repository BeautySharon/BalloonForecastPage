import pandas as pd
import numpy as np
import geopandas as gpd
from scipy.spatial import cKDTree
from shapely.geometry import Point, Polygon

def Step5_DangerousBalloons():
        # Step 1: 获取全球军事基地 (OSM API)
    def get_military_bases():
        overpass_url = "http://overpass-api.de/api/interpreter"
        query = "[out:json]; node[landuse=military]; out body;"
        response = requests.get(overpass_url, params={'data': query})
        if response.status_code == 200:
            data = response.json()
            return [(node["lat"], node["lon"]) for node in data.get("elements", []) if "lat" in node and "lon" in node]
        return []

    # Step 2: 获取美国禁飞区 (FAA API)
    def get_faa_no_fly_zones():
        faa_url = "https://ais-faa.opendata.arcgis.com/datasets/faa-special-use-airspace-sua.geojson"
        response = requests.get(faa_url)
        if response.status_code == 200:
            data = response.json()
            return [Polygon(feature["geometry"]["coordinates"][0]) for feature in data["features"] if feature["geometry"]["type"] == "Polygon"]
        return []

    # Step 3: 读取全球国家边界 (自动检测字段)
    def get_country_boundaries():
        shapefile_path = "Datafile/ne_110m_admin_0_countries.shp"
        world = gpd.read_file(shapefile_path)

        # 确保国家名称字段可用
        expected_columns = ["ADMIN", "NAME", "name"]
        available_columns = world.columns
        country_name_column = next((col for col in expected_columns if col in available_columns), None)

        if not country_name_column:
            raise ValueError("Could not find a country name column in the shapefile.")

        return world, country_name_column

    # Step 4: 获取气球的初始国家
    def get_balloon_initial_country(balloon_lat, balloon_lon, country_boundaries, country_name_column):
        balloon_point = Point(balloon_lon, balloon_lat)
        for _, country in country_boundaries.iterrows():
            if country["geometry"].contains(balloon_point):
                return country[country_name_column]
        return None  # 如果没找到，则返回 None

    # Step 5: 识别所有危险气球
    def Step5_DangerousBalloons():
        print("Step5: Identifying Dangerous Balloons")

        # 加载数据
        df_balloons = pd.read_csv("Datafile/BalloonForecast.csv")
        df_aircraft = pd.read_csv("Datafile/aircraft_positions.csv")

        # 确保数据包含必要列
        if "latitude" not in df_balloons or "longitude" not in df_balloons:
            raise ValueError("Balloon data must contain 'latitude' and 'longitude' columns.")
        if "latitude" not in df_aircraft or "longitude" not in df_aircraft:
            raise ValueError("Aircraft data must contain 'latitude' and 'longitude' columns.")

        # 解析数据
        balloon_coords = df_balloons[['latitude', 'longitude']].to_numpy()
        aircraft_coords = df_aircraft[['latitude', 'longitude']].to_numpy()

        # 使用 KDTree 进行最近邻计算
        aircraft_tree = cKDTree(aircraft_coords)
        THRESHOLD_DISTANCE_KM = 10

        # 获取军事基地、禁飞区、国界数据
        military_bases = get_military_bases()
        no_fly_zones = get_faa_no_fly_zones()
        country_boundaries, country_name_column = get_country_boundaries()

        # 记录所有危险气球
        dangerous_balloons = []
        affected_aircraft = []

        # **记录气球的初始国家**
        initial_countries = {
            row["balloon_id"]: get_balloon_initial_country(row["latitude"], row["longitude"], country_boundaries, country_name_column)
            for _, row in df_balloons.iterrows()
        }

        for i, balloon in enumerate(balloon_coords):
            balloon_point = Point(balloon[1], balloon[0])  # 转换为 Point 进行地理计算
            balloon_id = df_balloons.iloc[i]["balloon_id"]
            balloon_lat, balloon_lon = balloon[0], balloon[1]

            # 1️⃣ 检查是否接近飞机
            distance, index = aircraft_tree.query(balloon, k=1)
            closest_distance_km = distance * 111  # 近似转换为 km
            if closest_distance_km <= THRESHOLD_DISTANCE_KM:
                dangerous_balloons.append({
                    "balloon_id": balloon_id,
                    "latitude": balloon_lat,
                    "longitude": balloon_lon,
                    "risk": "Near Aircraft",
                    "closest_aircraft_distance_km": closest_distance_km
                })
                affected_aircraft.append({
                    "icao": df_aircraft.iloc[index]["icao"],
                    "latitude": df_aircraft.iloc[index]["latitude"],
                    "longitude": df_aircraft.iloc[index]["longitude"],
                    "velocity": df_aircraft.iloc[index]["velocity"],
                    "heading": df_aircraft.iloc[index]["heading"],
                    "vertical_rate": df_aircraft.iloc[index]["vertical_rate"],
                    "on_ground": df_aircraft.iloc[index]["on_ground"]
                })

            # 2️⃣ 检查是否接近军事基地
            for base in military_bases:
                base_point = Point(base[1], base[0])
                if balloon_point.distance(base_point) < 0.01:  # 约 1km
                    dangerous_balloons.append({
                        "balloon_id": balloon_id,
                        "latitude": balloon_lat,
                        "longitude": balloon_lon,
                        "risk": "Near Military Base"
                    })
                    break

            # 3️⃣ 检查是否进入禁飞区
            for zone in no_fly_zones:
                if zone.contains(balloon_point):
                    dangerous_balloons.append({
                        "balloon_id": balloon_id,
                        "latitude": balloon_lat,
                        "longitude": balloon_lon,
                        "risk": "In No-Fly Zone"
                    })
                    break

            # 4️⃣ 检查气球是否进入其他国家
            current_country = None
            for _, country in country_boundaries.iterrows():
                if country["geometry"].contains(balloon_point):
                    current_country = country[country_name_column]
                    break

            # **只有当气球原本的国家和现在的国家不一样，才记录进入新国家**
            initial_country = initial_countries.get(balloon_id)
            if initial_country and current_country and initial_country != current_country:
                dangerous_balloons.append({
                    "balloon_id": balloon_id,
                    "latitude": balloon_lat,
                    "longitude": balloon_lon,
                    "risk": f"Entered {current_country} from {initial_country}"
                })

        # 保存数据
        df_dangerous_balloons = pd.DataFrame(dangerous_balloons)
        df_affected_aircraft = pd.DataFrame(affected_aircraft)
        df_dangerous_balloons.to_csv("Datafile/dangerous_balloons.csv", index=False)
        df_affected_aircraft.to_csv("Datafile/affected_aircraft.csv", index=False)

        print("✅ Dangerous balloons saved to 'dangerous_balloons.csv'")
        print("✅ Affected aircraft saved to 'affected_aircraft.csv'")
        print("Step5: Identifying Dangerous Balloons Completed")
