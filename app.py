from flask import Flask, render_template, request
import pickle
import numpy as np
import pandas as pd
import mysql.connector
import os

app = Flask(__name__)

# === Load Model and Features ===
try:
    with open("game_sales_model.pkl", "rb") as model_file:
        model = pickle.load(model_file)

    with open("features.pkl", "rb") as features_file:
        features = pickle.load(features_file)

    print("✅ Model and features loaded.")
except Exception as e:
    print("❌ Error loading model or features:", e)
    model = None
    features = []

# === Connect to XAMPP MySQL ===
try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  # default password for XAMPP
        database="game_db"
    )
    cursor = db.cursor()
    print("✅ Connected to MySQL.")
except Exception as e:
    print("❌ MySQL connection failed:", e)

# === Static dropdown options (or load from features.pkl if needed) ===
genre_options = [
    "Action", "Adventure", "RPG", "Simulation", "Sports",
    "Puzzle", "Strategy", "Shooter"
]

publisher_options = [
    "Nintendo", "Electronic Arts", "Ubisoft", "Activision", "Sega",
    "Square Enix", "Sony Computer Entertainment", "Capcom"
]

# === Main Route ===
@app.route('/', methods=['GET', 'POST'])
def index():
    prediction = None
    message = ''

    if request.method == 'POST':
        genre = request.form.get('genre')
        publisher = request.form.get('publisher')

        # Create input DataFrame filled with zeros
        input_data = pd.DataFrame([0]*len(features), index=features).T

        # One-hot encode user inputs
        genre_col = f"Genre_{genre}"
        publisher_col = f"Publisher_{publisher}"

        if genre_col in input_data.columns:
            input_data.at[0, genre_col] = 1
        if publisher_col in input_data.columns:
            input_data.at[0, publisher_col] = 1

        try:
            prediction = model.predict(input_data)[0]
            message = f"🎯 Predicted Sales: {prediction:.2f} million units"

            # Save prediction to database
            sql = "INSERT INTO predictions (genre, publisher, predicted_sales) VALUES (%s, %s, %s)"
            cursor.execute(sql, (genre, publisher, prediction))
            db.commit()

        except Exception as e:
            message = f"❌ Prediction error: {e}"

    return render_template(
        'index.html',
        prediction=prediction,
        message=message,
        genre_options=genre_options,
        publisher_options=publisher_options
    )

# === Run App ===
if __name__ == '__main__':
    app.run(debug=True)
