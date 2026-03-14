import requests
from pathlib import Path
from typing import Optional
from datetime import datetime
from zoneinfo import ZoneInfo
from geopy.geocoders import Nominatim
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from google.adk.agents import Agent


def _geocode(city: str):
    """Return geopy Location for a city, or None if not found."""
    geolocator = Nominatim(user_agent="weather_agent_team")
    return geolocator.geocode(city)


def is_good_weather_code(code: int) -> bool:
    good_codes = {0, 1, 2, 3}
    return code in good_codes


def score_hour(temp, precip_prob, wind, apparent_temp, weather_code) -> int:
    score = 0

    if 16 <= temp <= 23:
        score += 3
    elif 13 <= temp <= 25:
        score += 2
    elif 10 <= temp <= 27:
        score += 1
    else:
        score -= 3

    if 15 <= apparent_temp <= 23:
        score += 2
    elif 12 <= apparent_temp <= 25:
        score += 1
    else:
        score -= 2

    if precip_prob <= 10:
        score += 3
    elif precip_prob <= 25:
        score += 2
    elif precip_prob > 40:
        score -= 4

    if wind <= 12:
        score += 3
    elif wind <= 20:
        score += 2
    elif wind > 28:
        score -= 3

    score += 2 if is_good_weather_code(weather_code) else -4

    return score


def classify_hour(score: int) -> str:
    if score >= 8:
        return "bardzo dobra"
    if score >= 5:
        return "dobra"
    if score >= 2:
        return "średnia"
    return "słaba"


def fetch_weather(city: str, location) -> dict:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": location.latitude,
        "longitude": location.longitude,
        "timezone": "Europe/Warsaw",
        "forecast_days": 1,
        "hourly": [
            "temperature_2m",
            "precipitation_probability",
            "wind_speed_10m",
            "apparent_temperature",
            "weather_code",
        ],
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def build_hourly_rows(data: dict) -> list:
    hourly = data["hourly"]
    rows = []
    for i, time_str in enumerate(hourly["time"]):
        dt = datetime.fromisoformat(time_str).replace(tzinfo=ZoneInfo("Europe/Warsaw"))
        row = {
            "time": dt,
            "temperature_2m": hourly["temperature_2m"][i],
            "precipitation_probability": hourly["precipitation_probability"][i],
            "wind_speed_10m": hourly["wind_speed_10m"][i],
            "apparent_temperature": hourly["apparent_temperature"][i],
            "weather_code": hourly["weather_code"][i],
        }
        row["score"] = score_hour(
            temp=row["temperature_2m"],
            precip_prob=row["precipitation_probability"],
            wind=row["wind_speed_10m"],
            apparent_temp=row["apparent_temperature"],
            weather_code=row["weather_code"],
        )
        row["quality"] = classify_hour(row["score"])
        rows.append(row)
    return rows


def find_best_windows(rows: list, min_score: int = 5) -> list:
    windows, current = [], []
    for row in rows:
        if row["score"] >= min_score:
            current.append(row)
        elif current:
            windows.append(current)
            current = []
    if current:
        windows.append(current)
    return windows


def summarize_window(window: list) -> dict:
    start = window[0]["time"]
    end = window[-1]["time"]
    temps = [x["temperature_2m"] for x in window]
    winds = [x["wind_speed_10m"] for x in window]
    precips = [x["precipitation_probability"] for x in window]
    return {
        "start": start,
        "end": end,
        "temp_min": min(temps),
        "temp_max": max(temps),
        "wind_max": max(winds),
        "precip_max": max(precips),
        "avg_score": round(sum(x["score"] for x in window) / len(window), 1),
    }


def generate_human_message(city: str, windows: list) -> str:
    if not windows:
        return (
            f"Dzisiaj warunki na rodzinną wycieczkę rowerową w {city} nie wyglądają zbyt dobrze. "
            "Nie widać dłuższego, stabilnego okna z komfortową temperaturą, niskim wiatrem i małym ryzykiem opadów."
        )

    summarized = [summarize_window(w) for w in windows]
    best = max(summarized, key=lambda x: x["avg_score"])

    start_str = best["start"].strftime("%H:%M")
    end_str = best["end"].strftime("%H:%M")

    if best["avg_score"] >= 8:
        verdict = "zdecydowanie warto"
    elif best["avg_score"] >= 6:
        verdict = "warto"
    else:
        verdict = "raczej można"

    return (
        f"Dzisiaj w {city} {verdict} wyjść na wycieczkę rowerową z dziećmi.\n"
        f"Najlepsze okno: {start_str}–{end_str}.\n"
        f"Temperatura: {best['temp_min']:.0f}–{best['temp_max']:.0f}°C, "
        f"maks. wiatr: {best['wind_max']:.0f} km/h, "
        f"maks. ryzyko opadów: {best['precip_max']:.0f}%.\n"
        f"Średnia ocena warunków: {best['avg_score']}/13."
    )


def assess_trip_weather(city: str) -> dict:
    """Assess hourly weather conditions for a family bike trip in a given city.

    Args:
        city: Name of the city, e.g. 'Krakow', 'Warsaw'.

    Returns:
        dict: status and human-readable assessment message.
    """
    try:
        location = _geocode(city)
        if not location:
            return {"status": "error", "error": f"Could not find location for city: {city}"}

        data = fetch_weather(city, location)
        rows = build_hourly_rows(data)
        windows = find_best_windows(rows, min_score=5)
        message = generate_human_message(city, windows)

        return {"status": "success", "message": message}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def get_weather(city: str) -> dict:
    """Get current weather for a given city using the Open-Meteo API.

    Args:
        city: Name of the city, e.g. 'Warsaw', 'London'.

    Returns:
        dict: status and weather report or error message.
    """
    try:
        location = _geocode(city)
        if not location:
            return {"status": "error", "error": f"Could not find location for city: {city}"}

        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={location.latitude}&longitude={location.longitude}"
            f"&current=temperature_2m,weathercode,windspeed_10m"
            f"&wind_speed_unit=ms"
        )
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()["current"]

        return {
            "status": "success",
            "city": city,
            "temperature_c": data["temperature_2m"],
            "wind_speed_ms": data["windspeed_10m"],
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def say_hello(name: Optional[str] = None) -> str:
    """Provides a simple greeting. If a name is provided, it will be used.

    Args:
        name: The name of the person to greet. Defaults to a generic greeting if not provided.

    Returns:
        str: A friendly greeting message.
    """
    if name:
        return f"Hello, {name}!"
    return "Hello there!"


def say_goodbye() -> str:
    """Provides a simple farewell message to conclude the conversation."""
    return "Goodbye! Have a great day."


greeting_agent = Agent(
    name="greeting_agent",
    model="gemini-2.5-flash",
    description="Handles simple greetings and hellos using the 'say_hello' tool.",
    instruction=(
        "You are the Greeting Agent. Your ONLY task is to provide a friendly greeting to the user. "
        "Use the 'say_hello' tool to generate the greeting. "
        "If the user provides their name, make sure to pass it to the tool. "
        "Do not engage in any other conversation or tasks."
    ),
    tools=[say_hello],
)

farewell_agent = Agent(
    name="farewell_agent",
    model="gemini-2.5-flash",
    description="Handles simple farewells and goodbyes using the 'say_goodbye' tool.",
    instruction=(
        "You are the Farewell Agent. Your ONLY task is to provide a polite goodbye message. "
        "Use the 'say_goodbye' tool when the user indicates they are leaving or ending the conversation "
        "(e.g., using words like 'bye', 'goodbye', 'thanks bye', 'see you'). "
        "Do not perform any other actions."
    ),
    tools=[say_goodbye],
)

root_agent = Agent(
    name="weather_agent_v2",
    model="gemini-2.5-flash",
    description="The main coordinator agent. Handles weather requests and delegates greetings/farewells to specialists.",
    instruction=(
        "You are the main Weather Agent coordinating a team. Your primary responsibility is to provide weather information. "
        "Use the 'get_weather' tool for current weather requests (e.g., 'weather in Krakow'). "
        "Use the 'assess_trip_weather' tool when asked about suitability for a bike trip or outdoor activity. "
        "You have specialized sub-agents: "
        "1. 'greeting_agent': Handles simple greetings like 'Hi', 'Hello'. Delegate to it for these. "
        "2. 'farewell_agent': Handles simple farewells like 'Bye', 'See you'. Delegate to it for these. "
        "Analyze the user's query and route it to the appropriate tool or sub-agent."
    ),
    tools=[get_weather, assess_trip_weather],
    sub_agents=[greeting_agent, farewell_agent],
)
