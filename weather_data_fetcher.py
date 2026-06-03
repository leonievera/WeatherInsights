from pathlib import Path

import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry


API_URL = "https://api.open-meteo.com/v1/forecast"
OUTPUT_FILE = Path("weather_data.csv")
REQUIRED_COLUMNS = [
    "city",
    "date",
    "temperature_2m",
    "wind_speed_10m",
    "precipitation",
]
WEATHER_COLUMNS = ["temperature_2m", "wind_speed_10m", "precipitation"]
CITIES = [
    {"city": "Zurich", "latitude": 47.38, "longitude": 8.54},
    {"city": "London", "latitude": 51.51, "longitude": -0.13},
    {"city": "New York", "latitude": 40.71, "longitude": -74.01},
]


def create_openmeteo_client() -> openmeteo_requests.Client:
    cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    return openmeteo_requests.Client(session=retry_session)


def fetch_weather_data() -> pd.DataFrame:
    openmeteo = create_openmeteo_client()
    params = {
        "latitude": [city["latitude"] for city in CITIES],
        "longitude": [city["longitude"] for city in CITIES],
        "hourly": WEATHER_COLUMNS,
        "past_days": 7,
        "forecast_days": 0,
    }
    responses = openmeteo.weather_api(API_URL, params=params)

    dataframes = []
    for city, response in zip(CITIES, responses):
        hourly = response.Hourly()
        hourly_data = {
            "city": city["city"],
            "date": pd.date_range(
                start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=hourly.Interval()),
                inclusive="left",
            ),
            "temperature_2m": hourly.Variables(0).ValuesAsNumpy(),
            "wind_speed_10m": hourly.Variables(1).ValuesAsNumpy(),
            "precipitation": hourly.Variables(2).ValuesAsNumpy(),
        }
        dataframes.append(pd.DataFrame(data=hourly_data))

    return pd.concat(dataframes, ignore_index=True)


def clean_weather_data(weather_data: pd.DataFrame) -> pd.DataFrame:
    cleaned_data = weather_data.copy()

    cleaned_data["city"] = cleaned_data["city"].astype("string")
    cleaned_data["date"] = pd.to_datetime(cleaned_data["date"], utc=True)

    for column in WEATHER_COLUMNS:
        cleaned_data[column] = pd.to_numeric(cleaned_data[column], errors="coerce")

    cleaned_data = cleaned_data.dropna(subset=REQUIRED_COLUMNS)
    cleaned_data = cleaned_data.sort_values(["city", "date"])
    return cleaned_data.reset_index(drop=True)


def save_weather_data(output_file: Path = OUTPUT_FILE) -> pd.DataFrame:
    weather_data = fetch_weather_data()
    cleaned_data = clean_weather_data(weather_data)
    cleaned_data.to_csv(output_file, index=False)
    return cleaned_data


if __name__ == "__main__":
    saved_data = save_weather_data()
    print(f"Saved {len(saved_data)} cleaned rows to {OUTPUT_FILE}")
