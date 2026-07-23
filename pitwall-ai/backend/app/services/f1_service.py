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

# In-memory result cache for parsed telemetry objects and metadata
_MEMORY_TELEMETRY_CACHE: dict[tuple[int, str, str, str], dict] = {}
_SCHEDULE_CACHE: dict[int, list[dict]] = {}
_DRIVERS_CACHE: dict[tuple[int, str, str], list[dict]] = {}

def clear_telemetry_memory_cache() -> None:
    """Clears in-memory caches (primarily for tests)."""
    _MEMORY_TELEMETRY_CACHE.clear()
    _SCHEDULE_CACHE.clear()
    _DRIVERS_CACHE.clear()

def get_season_schedule(year: int) -> list[dict]:
    """
    Returns the real official F1 calendar for a given season year using FastF1 event schedule.
    """
    if year in _SCHEDULE_CACHE:
        return _SCHEDULE_CACHE[year]

    try:
        schedule = fastf1.get_event_schedule(year)
        events = []
        if hasattr(schedule, 'iterrows'):
            for _, row in schedule.iterrows():
                event_name = str(row.get('EventName', '')).strip()
                location = str(row.get('Location', '')).strip()
                country = str(row.get('Country', '')).strip()
                round_num = row.get('RoundNumber', 0)

                if event_name and 'Testing' not in event_name and round_num > 0:
                    events.append({
                        "round": int(round_num),
                        "event_name": event_name,
                        "location": location,
                        "country": country,
                        "search_key": location or event_name.replace(" Grand Prix", "").strip()
                    })

        _SCHEDULE_CACHE[year] = events
        return events
    except Exception as e:
        print(f"Schedule fetch warning: {e}")
        return []

async def get_season_schedule_async(year: int) -> list[dict]:
    """Asynchronously fetches official F1 season calendar."""
    return await run_in_threadpool(get_season_schedule, year)

def get_session_drivers(year: int, grand_prix: str, session_type: str) -> list[dict]:
    """
    Fetches the actual participating driver lineup for a specific race session.
    """
    cache_key = (year, str(grand_prix).lower().strip(), str(session_type).upper().strip())
    if cache_key in _DRIVERS_CACHE:
        return _DRIVERS_CACHE[cache_key]

    try:
        session = fastf1.get_session(year, grand_prix, session_type)
        session.load(laps=True, telemetry=False, weather=False, messages=False)

        drivers = []
        if hasattr(session, 'results') and not session.results.empty:
            for _, row in session.results.iterrows():
                code = str(row.get('Abbreviation', '')).strip().upper()
                name = str(row.get('FullName', row.get('BroadcastName', code))).strip()
                team = str(row.get('TeamName', '')).strip()
                num = str(row.get('DriverNumber', ''))
                if code:
                    drivers.append({
                        "code": code,
                        "name": name,
                        "team": team,
                        "number": num
                    })
        elif hasattr(session, 'laps') and not session.laps.empty:
            driver_codes = session.laps['Driver'].dropna().unique()
            for code in driver_codes:
                code_str = str(code).strip().upper()
                if code_str:
                    drivers.append({
                        "code": code_str,
                        "name": code_str,
                        "team": "F1 Team",
                        "number": ""
                    })

        _DRIVERS_CACHE[cache_key] = drivers
        return drivers
    except Exception as e:
        print(f"Drivers fetch warning: {e}")
        return []

async def get_session_drivers_async(year: int, grand_prix: str, session_type: str) -> list[dict]:
    """Asynchronously fetches session driver lineup."""
    return await run_in_threadpool(get_session_drivers, year, grand_prix, session_type)

def prewarm_session_cache(year: int, grand_prix: str, session_type: str) -> None:
    """
    Pre-warms the FastF1 disk cache for a specific race session.
    """
    try:
        session = fastf1.get_session(year, grand_prix, session_type)
        session.load(telemetry=True, weather=False, messages=False)
    except Exception as e:
        raise TelemetryFetchError(f"Failed to pre-warm FastF1 telemetry cache: {str(e)}")

async def get_telemetry_async(
    year: int,
    grand_prix: str,
    session_type: str,
    driver_code: str,
    qdrant_client: AsyncQdrantClient | None = None
) -> dict:
    """
    Asynchronously fetches telemetry data using Qdrant vector database cache,
    in-memory dict cache, or on-demand FastF1 fallback.
    """
    cache_key = (year, str(grand_prix).lower().strip(), str(session_type).upper().strip(), str(driver_code).upper().strip())
    if cache_key in _MEMORY_TELEMETRY_CACHE:
        return _MEMORY_TELEMETRY_CACHE[cache_key]

    # Level 2: Try retrieving cached telemetry record directly from Qdrant race_telemetry collection
    if qdrant_client:
        try:
            from app.services.vector_db import search_race_telemetry
            cached_points = await search_race_telemetry(
                client=qdrant_client,
                query_embedding=[0.0] * 384,
                driver=driver_code.upper().strip(),
                session=session_type.upper().strip(),
                year=year,
                grand_prix=grand_prix,
                limit=1
            )
            if cached_points and isinstance(cached_points[0], dict) and "telemetry_stream" in cached_points[0]:
                data = cached_points[0]
                _MEMORY_TELEMETRY_CACHE[cache_key] = data
                return data
        except Exception:
            pass

    # Level 3: Compute via FastF1 in threadpool if not yet cached in Qdrant
    res = await run_in_threadpool(get_telemetry, year, grand_prix, session_type, driver_code)

    # Persist computed telemetry into Qdrant race_telemetry collection for future queries
    if qdrant_client and res:
        try:
            from app.services.embedding_service import generate_embedding_async
            from app.services.vector_db import upsert_telemetry_records

            summary = (
                f"{year} {grand_prix} Grand Prix ({session_type}) - Driver {driver_code}: "
                f"Fastest Lap {res.get('fastest_lap_number')} ({res.get('fastest_lap_time_seconds')}s), "
                f"Max Speed {res.get('max_speed_kph')} km/h."
            )
            emb = await generate_embedding_async(summary)
            res_payload = {
                **res,
                "year": year,
                "grand_prix": grand_prix,
                "session": session_type,
                "summary_text": summary
            }
            await upsert_telemetry_records(qdrant_client, [res_payload], [emb])
        except Exception:
            pass

    return res

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
        if hasattr(session.laps, 'pick_drivers'):
            driver_laps = session.laps.pick_drivers(driver_code)
        else:
            driver_laps = session.laps.pick_driver(driver_code)

        if driver_laps.empty:
            raise TelemetryNotFoundError(f"No laps found for driver {driver_code} in {year} {grand_prix} {session_type}.")

        # Extract fastest lap and its telemetry stream
        fastest_lap = driver_laps.pick_fastest()
        if fastest_lap is None or (isinstance(fastest_lap, (pd.Series, pd.DataFrame)) and (fastest_lap.empty if hasattr(fastest_lap, 'empty') else False)):
            raise TelemetryNotFoundError(f"No timed fastest lap found for driver {driver_code} in {year} {grand_prix} {session_type}.")

        telemetry = fastest_lap.get_telemetry() if hasattr(fastest_lap, 'get_telemetry') else pd.DataFrame()

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
            "rpm": [],
            "x_m": [],
            "y_m": []
        }
        max_speed = None
        avg_throttle = None
        braking_zones_count = 0

        if telemetry is not None and hasattr(telemetry, 'empty') and not telemetry.empty:
            cols = list(telemetry.columns) if hasattr(telemetry, 'columns') and isinstance(telemetry.columns, (pd.Index, list)) else []

            if 'Time' in cols:
                telemetry_stream["time_seconds"] = [
                    float(t.total_seconds()) if hasattr(t, 'total_seconds') else float(t)
                    for t in telemetry['Time']
                ]
            if 'Distance' in cols:
                telemetry_stream["distance_meters"] = [float(x) for x in telemetry['Distance']]
            if 'X' in cols:
                telemetry_stream["x_m"] = [float(x) for x in telemetry['X']]
            if 'Y' in cols:
                telemetry_stream["y_m"] = [float(y) for y in telemetry['Y']]
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

            # Downsample telemetry stream arrays to max 150 points for lightweight JSON payloads
            n_points = len(telemetry_stream["time_seconds"])
            if n_points > 150:
                step = max(1, n_points // 150)
                for key in telemetry_stream:
                    if telemetry_stream[key]:
                        telemetry_stream[key] = telemetry_stream[key][::step]

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
