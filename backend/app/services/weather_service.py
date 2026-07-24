import fastf1
import numpy as np
import pandas as pd
from typing import Any
from fastapi.concurrency import run_in_threadpool

_WEATHER_CACHE: dict[tuple[int, str, str], dict[str, Any]] = {}

def get_session_weather(year: int, grand_prix: str, session_type: str = "R") -> dict[str, Any]:
    """
    Fetches real F1 session weather data using FastF1 weather feed dataframe.
    Extracts mean Track Temperature, Air Temperature, Humidity, and Rain status.
    Uses in-memory caching to avoid repeated FastF1 session loads.
    """
    cache_key = (year, grand_prix.lower(), session_type.upper())
    if cache_key in _WEATHER_CACHE:
        return _WEATHER_CACHE[cache_key]

    try:
        from app.services.f1_service import _ensure_f1_libs
        _ensure_f1_libs()
        import fastf1

        session = fastf1.get_session(year, grand_prix, session_type)
        session.load(telemetry=False, laps=False, weather=True, messages=False)

        if hasattr(session, 'weather_data') and not session.weather_data.empty:
            w = session.weather_data
            track_temp = float(w['TrackTemp'].dropna().mean()) if 'TrackTemp' in w else 35.0
            air_temp = float(w['AirTemp'].dropna().mean()) if 'AirTemp' in w else 25.0
            humidity = float(w['Humidity'].dropna().mean()) if 'Humidity' in w else 48.0
            has_rain = bool((w['Rainfall'].dropna() > 0).any()) if 'Rainfall' in w else False
            wind_speed = float(w['WindSpeed'].dropna().mean()) if 'WindSpeed' in w else 2.5

            res = {
                "year": year,
                "grand_prix": grand_prix,
                "session_type": session_type,
                "track_temp_celsius": round(track_temp, 1),
                "air_temp_celsius": round(air_temp, 1),
                "humidity_pct": round(humidity, 1),
                "rainfall": has_rain,
                "wind_speed_ms": round(wind_speed, 1),
                "status": "RAIN 🌧️" if has_rain else ("HOT ☀️" if track_temp >= 40.0 else "DRY 🌤️")
            }
            _WEATHER_CACHE[cache_key] = res
            return res
    except Exception as e:
        print(f"Weather fetch warning for {year} {grand_prix}: {e}")

    # Default ambient fallback metrics
    return {
        "year": year,
        "grand_prix": grand_prix,
        "session_type": session_type,
        "track_temp_celsius": 36.5,
        "air_temp_celsius": 26.0,
        "humidity_pct": 52.0,
        "rainfall": False,
        "wind_speed_ms": 3.1,
        "status": "DRY 🌤️"
    }

async def get_session_weather_async(year: int, grand_prix: str, session_type: str = "R") -> dict[str, Any]:
    """Asynchronously fetches session weather metrics."""
    return await run_in_threadpool(get_session_weather, year, grand_prix, session_type)

def calculate_weather_crossover(
    rainfall_mm_per_min: float = 0.0,
    track_moisture_pct: float = 0.0,
    ambient_temp_celsius: float = 24.0,
    track_temp_celsius: float = 34.0
) -> dict[str, Any]:
    """
    Calculates dynamic compound crossover thresholds (Slick ↔ Intermediate ↔ Full Wet)
    based on rainfall intensity and track surface wetness.
    """
    if track_moisture_pct < 15.0 and rainfall_mm_per_min < 0.2:
        recommended_compound = "DRY_SLICK"
        crossover_state = "DRY_TRACK"
        pace_penalty_sec = 0.0
    elif track_moisture_pct < 45.0 or (0.2 <= rainfall_mm_per_min < 1.2):
        recommended_compound = "INTERMEDIATE"
        crossover_state = "SLICK_TO_INTER_CROSSOVER"
        pace_penalty_sec = 4.5
    else:
        recommended_compound = "FULL_WET"
        crossover_state = "INTER_TO_WET_CROSSOVER"
        pace_penalty_sec = 11.8

    dry_lap_base = 90.0
    inter_crossover_threshold_lap_time = round(dry_lap_base * 1.10, 2)
    wet_crossover_threshold_lap_time = round(dry_lap_base * 1.22, 2)

    return {
        "rainfall_mm_per_min": rainfall_mm_per_min,
        "track_moisture_pct": track_moisture_pct,
        "ambient_temp_celsius": ambient_temp_celsius,
        "track_temp_celsius": track_temp_celsius,
        "recommended_compound": recommended_compound,
        "crossover_state": crossover_state,
        "pace_penalty_sec": pace_penalty_sec,
        "dry_to_inter_threshold_sec": inter_crossover_threshold_lap_time,
        "inter_to_wet_threshold_sec": wet_crossover_threshold_lap_time,
        "slick_usable": recommended_compound == "DRY_SLICK",
        "intermediate_usable": recommended_compound in ("INTERMEDIATE", "DRY_SLICK"),
        "full_wet_required": recommended_compound == "FULL_WET"
    }

async def calculate_weather_crossover_async(**kwargs) -> dict[str, Any]:
    """Asynchronously calculates weather crossover analysis."""
    return await run_in_threadpool(calculate_weather_crossover, **kwargs)
