from pathlib import Path

import pandas as pd


DATA_FILE = Path("weather_data.csv")
REQUIRED_COLUMNS = {"city", "date", "temperature_2m", "precipitation"}


def load_weather_data(data_file: Path = DATA_FILE) -> pd.DataFrame:
    weather_data = pd.read_csv(data_file, parse_dates=["date"])
    missing_columns = REQUIRED_COLUMNS.difference(weather_data.columns)

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing required column(s): {missing}")

    return weather_data


def print_average_temperature_by_city(weather_data: pd.DataFrame) -> None:
    print("Average temperature per city over the past 7 days")

    averages = weather_data.groupby("city")["temperature_2m"].mean().sort_index()
    for city, temperature in averages.items():
        print(f"- {city}: {temperature:.2f} C")


def print_daily_precipitation_by_city(weather_data: pd.DataFrame) -> None:
    print("\nTotal precipitation per city per day")

    daily_data = weather_data.assign(day=weather_data["date"].dt.date)
    precipitation_totals = (
        daily_data.groupby(["city", "day"])["precipitation"].sum().sort_index()
    )

    for (city, day), precipitation in precipitation_totals.items():
        print(f"- {city} on {day}: {precipitation:.2f} mm")


def print_coldest_hour(weather_data: pd.DataFrame) -> None:
    print("\nSingle coldest hour across all the data")

    coldest_row = weather_data.loc[weather_data["temperature_2m"].idxmin()]
    print(f"- City: {coldest_row['city']}")
    print(f"- Time: {coldest_row['date']}")
    print(f"- Temperature: {coldest_row['temperature_2m']:.2f} C")


def main() -> None:
    try:
        weather_data = load_weather_data()
    except FileNotFoundError:
        print(f"Could not find {DATA_FILE}. Run weather_data_fetcher.py first.")
        return
    except ValueError as error:
        print(error)
        return

    print_average_temperature_by_city(weather_data)
    print_daily_precipitation_by_city(weather_data)
    print_coldest_hour(weather_data)


if __name__ == "__main__":
    main()
