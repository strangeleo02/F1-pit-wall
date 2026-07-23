import os
import fastf1
import pandas as pd
import numpy as np
from fastapi.concurrency import run_in_threadpool
from app.config import settings
from app.exceptions import TelemetryNotFoundError, TelemetryFetchError

# Configure FastF1 cache
if not os.path.exists(settings.FASTF1_CACHE_DIR):
    os.makedirs(settings.FASTF1_CACHE_DIR)
fastf1.Cache.enable_cache(settings.FASTF1_CACHE_DIR)

# In-memory result cache for parsed telemetry objects
_MEMORY_TELEMETRY_CACHE: dict[tuple[int, str, str, str], dict] = {}

def clear_telemetry_memory_cache() -> None:
    """Clears the in-memory telemetry result cache (primarily for tests)."""
    _MEMORY_TELEMETRY_CACHE.clear()

def prewarm_session_cache(year: int, grand_prix: str, session_type: str) -> None:
    """
    Pre-warms the FastF1 disk cache for a specific race session.
    """
    try:
        session = fastf1.get_session(year, grand_prix, session_type)
        session.load(telemetry=True, weather=False, messages=False)
    except Exception as e:
        raise TelemetryFetchError(f"Failed to pre-warm FastF1 telemetry cache: {str(e)}")

async def prewarm_session_cache_async(year: int, grand_prix: str, session_type: str) -> None:
    """
    Asynchronously pre-warms the FastF1 session cache in a worker thread.
    """
    await run_in_threadpool(prewarm_session_cache, year, grand_prix, session_type)

def get_telemetry(year: int, grand_prix: str, session_type: str, driver_code: str) -> dict:
    """
    Fetches comprehensive lap times and detailed time-series telemetry streams for a driver.
    Utilizes FastF1 disk cache and in-memory dict cache for sub-millisecond retrieval.
    """
    cache_key = (year, str(grand_prix).lower().strip(), str(session_type).upper().strip(), str(driver_code).upper().strip())
    if cache_key in _MEMORY_TELEMETRY_CACHE:
        return _MEMORY_TELEMETRY_CACHE[cache_key]

    try:
        # Load the session
        session = fastf1.get_session(year, grand_prix, session_type)
        session.load(telemetry=True, weather=False, messages=False)

        # Get driver's laps
        driver_laps = session.laps.pick_driver(driver_code)

        if driver_laps.empty:
            raise TelemetryNotFoundError(f"No laps found for driver {driver_code} in {year} {grand_prix} {session_type}.")

        # Extract fastest lap and its telemetry stream
        fastest_lap = driver_laps.pick_fastest()
        telemetry = fastest_lap.get_telemetry()

        laps_data = driver_laps[['LapNumber', 'LapTime']].dropna().to_dict(orient='records')

        # Convert Timedelta to float seconds for JSON serialization
        for lap in laps_data:
            if hasattr(lap['LapTime'], 'total_seconds'):
                lap['LapTime'] = float(lap['LapTime'].total_seconds())

        fastest_lap_seconds = float(fastest_lap['LapTime'].total_seconds()) if hasattr(fastest_lap['LapTime'], 'total_seconds') else None

        # Process time-series streams
        telemetry_stream = {
            "time_seconds": [],
            "distance_meters": [],
            "speed_kph": [],
            "throttle_percentage": [],
            "brake": [],
            "gear": [],
            "drs": [],
            "rpm": []
        }
        max_speed = None
        avg_throttle = None
        braking_zones_count = 0

        if not telemetry.empty:
            cols = list(telemetry.columns) if hasattr(telemetry, 'columns') and isinstance(telemetry.columns, (pd.Index, list)) else []

            if 'Time' in cols:
                telemetry_stream["time_seconds"] = [
                    float(t.total_seconds()) if hasattr(t, 'total_seconds') else float(t)
                    for t in telemetry['Time']
                ]
            if 'Distance' in cols:
                telemetry_stream["distance_meters"] = [float(x) for x in telemetry['Distance']]
            if 'Speed' in cols:
                speed_vals = [float(x) for x in telemetry['Speed']]
                telemetry_stream["speed_kph"] = speed_vals
                max_speed = float(np.max(speed_vals)) if len(speed_vals) > 0 else None
            elif hasattr(telemetry, '__getitem__'):
                try:
                    speed_obj = telemetry['Speed']
                    if hasattr(speed_obj, 'max'):
                        val = speed_obj.max()
                        max_speed = float(val() if callable(val) else val)
                except Exception:
                    pass

            if 'Throttle' in cols:
                throttle_vals = [float(x) for x in telemetry['Throttle']]
                telemetry_stream["throttle_percentage"] = throttle_vals
                avg_throttle = float(np.mean(throttle_vals)) if len(throttle_vals) > 0 else None

            if 'Brake' in cols:
                brake_vals = [bool(x) for x in telemetry['Brake']]
                telemetry_stream["brake"] = brake_vals
                braking_zones_count = int(sum(1 for i in range(1, len(brake_vals)) if brake_vals[i] and not brake_vals[i-1]))

            if 'nGear' in cols:
                telemetry_stream["gear"] = [int(x) for x in telemetry['nGear']]
            if 'DRS' in cols:
                telemetry_stream["drs"] = [int(x) for x in telemetry['DRS']]
            if 'RPM' in cols:
                telemetry_stream["rpm"] = [int(x) for x in telemetry['RPM']]

        result = {
            "driver": driver_code,
            "fastest_lap_number": int(fastest_lap['LapNumber']) if 'LapNumber' in fastest_lap else None,
            "fastest_lap_time_seconds": fastest_lap_seconds,
            "max_speed_kph": max_speed,
            "avg_throttle_percentage": round(avg_throttle, 2) if avg_throttle is not None else None,
            "braking_zones_count": braking_zones_count,
            "telemetry_stream": telemetry_stream,
            "laps": laps_data
        }
        _MEMORY_TELEMETRY_CACHE[cache_key] = result
        return result
    except TelemetryNotFoundError:
        raise
    except Exception as e:
        raise TelemetryFetchError(f"Failed to fetch telemetry: {str(e)}")

async def get_telemetry_async(year: int, grand_prix: str, session_type: str, driver_code: str) -> dict:
    """
    Asynchronously fetches telemetry data by running FastF1 logic in a threadpool worker.
    """
    return await run_in_threadpool(get_telemetry, year, grand_prix, session_type, driver_code)
