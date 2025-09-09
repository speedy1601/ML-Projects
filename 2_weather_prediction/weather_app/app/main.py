from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import joblib
import numpy as np
import polars as pl
from polars import col
import os
import requests
from geopy.geocoders import Nominatim

app = FastAPI(title = "Crop Prediction")

# 1) Mount static files.
app.mount(path = "/static", app = StaticFiles(directory = "app/static", html = True), name = "static")

# 2) Jinja2 templates.
templates = Jinja2Templates(directory = "app/templates")

# 3) Load models after creating paths.
# Get the folder, app, where this file, main.py, resides. 
cur_folder = os.path.dirname(os.path.realpath(__file__))

WEATHER_MODEL_PATH = os.path.join(cur_folder, "trained_models", "weather_model.pkl")
weather_model = joblib.load(WEATHER_MODEL_PATH)

# 4) Quantify weather information for the next 5 hours including running hour.

def rainfall_convertion(arr):
    effects  = np.array(['Clear Sky', 'Light rain', 'Noticeable rain', 'Heavy rain', 'Very heavy rain'])
    return effects[arr] # fancy indexing.

def current_weather_info_for_next_5_hours(city_name: str):
    # 1) Finding latitude and longitude of the city name.
    city_name = f"{city_name}, Bangladesh"

    geolocator = Nominatim(user_agent = "my_geocoder_app")
    location = geolocator.geocode(city_name)

    if not location:
        error = np.array(['Not Found'] * 6)
        return error, error, error

    # 2) Prameters for the API request.
    params = {
        "latitude": location.latitude,
        "longitude": location.longitude,
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m", # unit : %.
            "pressure_msl",         # unit : hPa. Sealevel pressure.
            "cloud_cover_low",      # unit : %. The most important cloud layer for rain.
            "cloud_cover",    # unit : %. Great overall context.
            "vapour_pressure_deficit", # unit : kPa (kilopascal).
            # "visibility",           # unit : meters.
            "wind_speed_10m",         
            "wind_direction_10m",   # unit : °.
            "wind_gusts_10m",       # unit : km/h.
            # "precipitation",              # precipitation = the amount of water that is expected to fall from the sky.
            # "precipitation_probability" # precipitation_probability = What's the chance it'll fall? That means its for FORECASTING,
        ],
        "timezone": "Asia/Dhaka", # Set timezone to Dhaka to get 24 hours data aligned with Dhaka's Local time from 0 to 23 because
        "temperature_unit" : "celsius",
        "wind_speed_unit": "kmh",
        "precipitation_unit": "mm",
        "forecast_hours": 6 # current hour + next 5 hours.
    }

    # Make the API request.
    url = "https://api.open-meteo.com/v1/forecast"
    response = requests.get(url, params = params)
    data = response.json()

    hourly_data: dict = data.get("hourly", {}) # dict.get(key, default).

    # 3) Convert the dict/json data to dataframe with CORRECT TIME ZONE and Feature Engineering.
    df = ( pl.DataFrame(data = hourly_data)
        .lazy()
        .rename({"time" : "date"}) # {old_name : new_name}.
        .with_columns(date  = col("date").str.to_datetime(format = "%Y-%m-%dT%H:%M", time_zone = data['timezone']))
        .with_columns(  col("relative_humidity_2m", "cloud_cover_low", "cloud_cover").cast(pl.Int8),
                        col("wind_direction_10m")                                    .cast(pl.Int16),

                        hour        = col('date').dt.hour(),  # 1 to 24 hours.
                        month       = col('date').dt.month(), # 1 to 12 no month.
                        day_of_year = col('date').dt.ordinal_day(), # 1 to 366 days.
                        date_am_pm  = col('date').dt.strftime(format = "%d %B %Y : %I %p"),
        )
        .drop("date")
        .select(col("hour", "month", "day_of_year"),
                col('*').exclude("hour", "month", "day_of_year")) # Features at the front + Target column at the end.
        .collect()
        .to_pandas()
    )

    # 4) Create X_test data and make prediction.
    dates = df['date_am_pm'] # Series.
    X_test = df.drop(columns = 'date_am_pm') # Dataframe.
    predicted_rainfalls = rainfall_convertion(weather_model.predict(X_test)) # numpy 1D array.
    
    # 5) return the necessery info for all the 6 cards.
    return dates, df['temperature_2m'], predicted_rainfalls

# 5) Create the get and post method.
@app.get("/", response_class = HTMLResponse)
async def page( request: Request ):
    dates, temperature, predicted_rainfalls = current_weather_info_for_next_5_hours(city_name = "Dhaka")

    return templates.TemplateResponse(name    = "index.html",
                                      context = {"request"             : request,
                                                 "city"                : "Dhaka",
                                                 "dates"               : dates,
                                                 "temperature"         : temperature,
                                                 "predicted_rainfalls" : predicted_rainfalls})

@app.post("/", response_class = HTMLResponse)
async def predict(request: Request, city: str = Form(...)):
    dates, temperature, predicted_rainfalls = current_weather_info_for_next_5_hours(city_name = city)

    return templates.TemplateResponse(name    = "partials/prediction.html",
                                      context = {"request"             : request,
                                                 "city"                : city,
                                                 "dates"               : dates,
                                                 "temperature"         : temperature,
                                                 "predicted_rainfalls" : predicted_rainfalls})

# cd 2_weather_prediction\weather_app          uvicorn app.main:app --reload