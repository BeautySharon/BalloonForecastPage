# 导入必要的库
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error

# 读取数据
file_path = "/Users/lvsihui/Desktop/BalloonForecast/Datafile/Final_cleaned_balloon_data_with_wind.csv"  # 替换为你的数据文件路径
df = pd.read_csv(file_path)

# 选择特征列（速度和方向的历史数据）
feature_cols = ["wind_speed","wind_direction",
    "speed_kmh_1h", "speed_kmh_2h", "speed_kmh_4h", "speed_kmh_5h",
    "speed_kmh_7h", "speed_kmh_12h", "speed_kmh_14h", "speed_kmh_18h","speed_kmh_21h",
    "direction_deg_1h", "direction_deg_2h", "direction_deg_4h", "direction_deg_5h",
    "direction_deg_7h", "direction_deg_12h", "direction_deg_14h", "direction_deg_18h","direction_deg_21h"
]

# 目标变量（未来速度和方向）
target_speed = "speed_kmh"
target_direction = "direction_deg"

# 删除包含 NaN 的行
df_cleaned = df.dropna(subset=feature_cols + [target_speed, target_direction])

# 选择特征和目标变量
X = df_cleaned[feature_cols]
y_speed = df_cleaned[target_speed]
y_direction = df_cleaned[target_direction]

# 划分训练集和测试集
X_train, X_test, y_train_speed, y_test_speed = train_test_split(X, y_speed, test_size=0.2, random_state=42)
X_train, X_test, y_train_direction, y_test_direction = train_test_split(X, y_direction, test_size=0.2, random_state=42)

# 训练速度预测模型（随机森林回归）
speed_model = RandomForestRegressor(n_estimators=100, random_state=42)
speed_model.fit(X_train, y_train_speed)

# 训练方向预测模型（随机森林回归）
direction_model = RandomForestRegressor(n_estimators=100, random_state=42)
direction_model.fit(X_train, y_train_direction)

# 预测整个数据集的速度和方向
df_cleaned["predicted_speed_kmh"] = speed_model.predict(X)
df_cleaned["predicted_direction_deg"] = direction_model.predict(X)

# 计算误差 (RMSE)
speed_rmse = np.sqrt(mean_squared_error(y_test_speed, speed_model.predict(X_test)))
direction_rmse = np.sqrt(mean_squared_error(y_test_direction, direction_model.predict(X_test)))

# 输出误差
print("速度预测 RMSE:", speed_rmse)
print("方向预测 RMSE:", direction_rmse)

# 保存带有预测数据的 CSV 文件
output_file_path = "/Users/lvsihui/Desktop/BalloonForecast/Datafile/BalloonForecast.csv"  # 替换为你想保存的文件名
df_cleaned.to_csv(output_file_path, index=False)

print(f"预测结果已保存到 {output_file_path}")
