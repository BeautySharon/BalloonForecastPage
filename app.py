from flask import Flask, render_template, send_file
from apscheduler.schedulers.background import BackgroundScheduler
import os
import pandas as pd
import folium
import Step0_test
import Step1_BalloonOriginalData
import Step2_BalloonDataCleanWithWind
import Step3_FetchPlaneData
import Step4_BalloonForecast
import Step5_dangerousballoons
import Step6_visualizemap

app = Flask(__name__)

def update_data():
    Step0_test.my_function()
    Step1_BalloonOriginalData.step1_balloon_original_data()
    Step2_BalloonDataCleanWithWind.Step2_BalloonDataCleanWithWind()
    Step3_FetchPlaneData.Step3_FetchPlaneData()
    Step4_BalloonForecast.Step4_BalloonForecast()
    Step5_dangerousballoons.Step5_DangerousBalloons()
    Step6_visualizemap.Step6_visualizemap()
    
# Set up scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(update_data, 'interval', hours=24)  # Runs every hour
scheduler.start()

# Path to generated map file
MAP_FILE_PATH = "static/Balloon_History_And_Prediction.html"

# Serve the map
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/map")
def show_map():
    return send_file(MAP_FILE_PATH)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5050)
