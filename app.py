from flask import Flask, render_template, send_file
import os
import pandas as pd
import folium

app = Flask(__name__)

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
