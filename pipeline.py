import os
import requests
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, timezone
import sqlite3


# EXTRACT
load_dotenv()
API_KEY = os.getenv('API_KEY')
CITIES_DATA = [
    {"name": "Mumbai",      "id": 1275339},
    {"name": "Delhi",       "id": 1273294},
    {"name": "Bengaluru",   "id": 1277333},
    {"name": "Chennai",     "id": 1264527},
    {"name": "Kolkata",     "id": 1275004},
    {"name": "Hyderabad",   "id": 1269843},
    {"name": "Jaipur",      "id": 1269515},
    {"name": "Pune",        "id": 1259229},
    {"name": "Ghaziabad",   "id": 1271308}
]

DB_FILE = "weather_data.db"
CSV_FILE = "weather_data.csv"

def fetch_weather_data_by_id(city_id, api_key):
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "id": city_id,
        "appid": api_key,
        "units": "metric"
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for city ID {city_id}: {e}")
        return None

print("Starting data extraction for Indian cities using city IDs...")
all_weather_data = []

for city in CITIES_DATA:
    city_name = city['name']
    city_id = city['id']
    
    weather_json = fetch_weather_data_by_id(city_id, API_KEY)
    if weather_json:
        all_weather_data.append(weather_json)
        print(f"Successfully fetched data for {city_name}.")
    else:
        print(f"Failed to fetch data for {city_name}.")


# TRANSFORM
print("Transforming data...")
transformed_data = []

for data in all_weather_data:
    transformed_entry = {
        "city": data['name'],
        "country": data['sys']['country'],
        "temperature_celsius": data['main']['temp'],
        "feels_like_celsius": data['main']['feels_like'],
        "humidity_percent": data['main']['humidity'],
        "weather_main": data['weather'][0]['main'], 
        "weather_description": data['weather'][0]['description'], 
        "timestamp_utc": datetime.fromtimestamp(data['dt'], tz=timezone.utc), 
        "wind_speed_mps": data['wind']['speed'],
        "latitude": data['coord']['lat'],
        "longitude": data['coord']['lon'],
        "load_timestamp_utc": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    }
    transformed_data.append(transformed_entry)

df = pd.DataFrame(transformed_data)
print("Transformation complete. DataFrame created:")
print(df.head(10))


# LOAD
print(f"Loading data to {CSV_FILE}...")
try:
    file_exists = os.path.isfile(CSV_FILE)
    df.to_csv(CSV_FILE, mode='a', header=not file_exists, index=False)
    print("CSV load complete.")
except Exception as e:
    print(f"Error loading to CSV: {e}")


print(f"Loading data to SQLite database: {DB_FILE}...")
try:
    conn = sqlite3.connect(DB_FILE)
    df.to_sql('weather_log', conn, if_exists='append', index=False)
    conn.close()
    print("SQLite load complete.")
except Exception as e:
    print(f"Error loading to SQLite: {e}")

print("Pipeline finished successfully!")