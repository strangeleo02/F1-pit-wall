import os
from typing import Any
from fastapi.concurrency import run_in_threadpool
from qdrant_client import AsyncQdrantClient
from app.config import settings
from app.exceptions import TelemetryNotFoundError, TelemetryFetchError

# Heavy libraries (fastf1, pandas, numpy) are imported lazily on first use
# to keep startup memory well under Render's 512MB free tier limit.
_f1_initialized = False
fastf1 = None  # type: ignore[assignment]
pd = None      # type: ignore[assignment]
np = None      # type: ignore[assignment]

def _ensure_f1_libs() -> None:
    """Lazy-initialise fastf1/pandas/numpy exactly once on first real call."""
    global fastf1, pd, np, _f1_initialized
    if _f1_initialized:
        return
    import fastf1 as _fastf1
    import pandas as _pd
    import numpy as _np
    fastf1 = _fastf1
    pd = _pd
    np = _np
    if not os.path.exists(settings.FASTF1_CACHE_DIR):
        os.makedirs(settings.FASTF1_CACHE_DIR)
    fastf1.Cache.enable_cache(settings.FASTF1_CACHE_DIR)
    _f1_initialized = True

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
    _ensure_f1_libs()
    if year in _SCHEDULE_CACHE:
        return _SCHEDULE_CACHE[year]

    try:
        schedule = fastf1.get_event_schedule(year)
        events = []
        now_utc = pd.Timestamp.now(tz='UTC')
        if hasattr(schedule, 'iterrows'):
            for _, row in schedule.iterrows():
                event_name = str(row.get('EventName', '')).strip()
                location = str(row.get('Location', '')).strip()
                country = str(row.get('Country', '')).strip()
                round_num = row.get('RoundNumber', 0)

                if event_name and 'Testing' not in event_name and round_num > 0:
                    race_date_val = row.get('Session5DateUtc')
                    if pd.isna(race_date_val):
                        race_date_val = row.get('EventDate')

                    has_passed = True
                    if pd.notna(race_date_val):
                        try:
                            has_passed = bool(pd.to_datetime(race_date_val, utc=True) <= now_utc)
                        except Exception:
                            has_passed = True

                    events.append({
                        "round": int(round_num),
                        "event_name": event_name,
                        "location": location,
                        "country": country,
                        "search_key": location or event_name.replace(" Grand Prix", "").strip(),
                        "has_passed": has_passed
                    })

        _SCHEDULE_CACHE[year] = events
        return events
    except Exception as e:
        print(f"Schedule fetch warning: {e}")
        return []

async def get_season_schedule_async(year: int) -> list[dict]:
    """Asynchronously fetches official F1 season calendar."""
    return await run_in_threadpool(get_season_schedule, year)

DEFAULT_F1_GRID: list[dict] = [
    {"code": "VER", "name": "Max Verstappen", "team": "Red Bull Racing", "number": "1"},
    {"code": "PER", "name": "Sergio Perez", "team": "Red Bull Racing", "number": "11"},
    {"code": "HAM", "name": "Lewis Hamilton", "team": "Mercedes", "number": "44"},
    {"code": "RUS", "name": "George Russell", "team": "Mercedes", "number": "63"},
    {"code": "LEC", "name": "Charles Leclerc", "team": "Ferrari", "number": "16"},
    {"code": "SAI", "name": "Carlos Sainz", "team": "Ferrari", "number": "55"},
    {"code": "NOR", "name": "Lando Norris", "team": "McLaren", "number": "4"},
    {"code": "PIA", "name": "Oscar Piastri", "team": "McLaren", "number": "81"},
    {"code": "ALO", "name": "Fernando Alonso", "team": "Aston Martin", "number": "14"},
    {"code": "STR", "name": "Lance Stroll", "team": "Aston Martin", "number": "18"},
    {"code": "GAS", "name": "Pierre Gasly", "team": "Alpine", "number": "10"},
    {"code": "OCO", "name": "Esteban Ocon", "team": "Alpine", "number": "31"},
    {"code": "TSU", "name": "Yuki Tsunoda", "team": "RB", "number": "22"},
    {"code": "RIC", "name": "Daniel Ricciardo", "team": "RB", "number": "3"},
    {"code": "ALB", "name": "Alexander Albon", "team": "Williams", "number": "23"},
    {"code": "SAR", "name": "Logan Sargeant", "team": "Williams", "number": "2"},
    {"code": "MAG", "name": "Kevin Magnussen", "team": "Haas F1 Team", "number": "20"},
    {"code": "HUL", "name": "Nico Hulkenberg", "team": "Haas F1 Team", "number": "27"},
    {"code": "BOT", "name": "Valtteri Bottas", "team": "Kick Sauber", "number": "77"},
    {"code": "ZHO", "name": "Zhou Guanyu", "team": "Kick Sauber", "number": "24"}
]

def get_session_drivers(year: int, grand_prix: str, session_type: str) -> list[dict]:
    """
    Fetches driver lineup for a session.
    Uses fast metadata-only FastF1 load (laps=False, 200ms) with fallback to default F1 grid.
    """
    _ensure_f1_libs()
    cache_key = (year, str(grand_prix).lower().strip(), str(session_type).upper().strip())
    if cache_key in _DRIVERS_CACHE:
        return _DRIVERS_CACHE[cache_key]

    try:
        session = fastf1.get_session(year, grand_prix, session_type)
        # laps=False & telemetry=False loads ONLY session metadata (200ms vs 15,000ms!)
        session.load(laps=False, telemetry=False, weather=False, messages=False)

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

        if drivers:
            _DRIVERS_CACHE[cache_key] = drivers
            return drivers
    except Exception as e:
        print(f"Drivers fetch warning for {year} {grand_prix}: {e}")

    # Fallback to default official grid if session results are not available
    _DRIVERS_CACHE[cache_key] = DEFAULT_F1_GRID
    return DEFAULT_F1_GRID

async def get_session_drivers_async(
    year: int,
    grand_prix: str,
    session_type: str,
    qdrant_client: Any | None = None
) -> list[dict]:
    """
    Asynchronously fetches session driver lineup, checking in-memory cache,
    Qdrant vector collection cache, and falling back to FastF1.
    """
    cache_key = (year, str(grand_prix).lower().strip(), str(session_type).upper().strip())
    if cache_key in _DRIVERS_CACHE:
        return _DRIVERS_CACHE[cache_key]

    if qdrant_client:
        try:
            from app.services.vector_db import get_driver_lineup_from_qdrant
            qdrant_drivers = await get_driver_lineup_from_qdrant(qdrant_client, year, grand_prix, session_type)
            if qdrant_drivers:
                _DRIVERS_CACHE[cache_key] = qdrant_drivers
                return qdrant_drivers
        except Exception as e:
            print(f"Qdrant driver cache check warning: {e}")

    drivers = await run_in_threadpool(get_session_drivers, year, grand_prix, session_type)

    if drivers and qdrant_client:
        try:
            from app.services.vector_db import cache_driver_lineup_in_qdrant
            await cache_driver_lineup_in_qdrant(qdrant_client, year, grand_prix, session_type, drivers)
        except Exception as e:
            print(f"Qdrant driver upsert warning: {e}")

    return drivers

def prewarm_session_cache(year: int, grand_prix: str, session_type: str) -> None:
    """
    Pre-warms the FastF1 disk cache for a specific race session.
    """
    _ensure_f1_libs()
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
    _ensure_f1_libs()
    if year >= 2026:
        raise TelemetryNotFoundError(f"Telemetry data for the {year} season is not yet available.")

    cache_key = (year, str(grand_prix).lower().strip(), str(session_type).upper().strip(), str(driver_code).upper().strip())
    if cache_key in _MEMORY_TELEMETRY_CACHE:
        return _MEMORY_TELEMETRY_CACHE[cache_key]

    # Level 1.5: Disk JSON cache check
    import json
    cache_dir = os.path.join(settings.FASTF1_CACHE_DIR, "parsed_telemetry")
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir, exist_ok=True)

    disk_file = os.path.join(cache_dir, f"tel_{year}_{grand_prix.lower().strip()}_{session_type.lower().strip()}_{driver_code.lower().strip()}.json")
    if os.path.exists(disk_file):
        try:
            with open(disk_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                _MEMORY_TELEMETRY_CACHE[cache_key] = data
                return data
        except Exception:
            pass

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

        s1_sec = float(fastest_lap['Sector1Time'].total_seconds()) if ('Sector1Time' in fastest_lap and hasattr(fastest_lap['Sector1Time'], 'total_seconds') and pd.notna(fastest_lap['Sector1Time'])) else None
        s2_sec = float(fastest_lap['Sector2Time'].total_seconds()) if ('Sector2Time' in fastest_lap and hasattr(fastest_lap['Sector2Time'], 'total_seconds') and pd.notna(fastest_lap['Sector2Time'])) else None
        s3_sec = float(fastest_lap['Sector3Time'].total_seconds()) if ('Sector3Time' in fastest_lap and hasattr(fastest_lap['Sector3Time'], 'total_seconds') and pd.notna(fastest_lap['Sector3Time'])) else None

        result = {
            "driver": driver_code,
            "fastest_lap_number": int(fastest_lap['LapNumber']) if 'LapNumber' in fastest_lap else None,
            "fastest_lap_time_seconds": fastest_lap_seconds,
            "sector1_seconds": s1_sec,
            "sector2_seconds": s2_sec,
            "sector3_seconds": s3_sec,
            "max_speed_kph": max_speed,
            "avg_throttle_percentage": round(avg_throttle, 2) if avg_throttle is not None else None,
            "braking_zones_count": braking_zones_count,
            "telemetry_stream": telemetry_stream,
            "laps": laps_data
        }
        _MEMORY_TELEMETRY_CACHE[cache_key] = result
        try:
            with open(disk_file, "w", encoding="utf-8") as f:
                json.dump(result, f)
        except Exception:
            pass

        # Explicitly clean up heavy Pandas objects from memory
        import gc
        del session, driver_laps, fastest_lap, telemetry
        gc.collect()

        return result
    except TelemetryNotFoundError:
        raise
    except Exception as e:
        raise TelemetryFetchError(f"Failed to fetch telemetry: {str(e)}")

_SESSION_WEATHER_CACHE: dict[tuple[int, str, str], dict] = {}

def get_session_weather_and_laps(year: int = 2024, grand_prix: str = "Monza", session_type: str = "Race") -> dict[str, Any]:
    """
    Fetches real historical weather telemetry (AirTemp, TrackTemp, Humidity, Rainfall)
    and total session laps for a specific Year, Grand Prix, and Session from FastF1 API.
    """
    _ensure_f1_libs()
    from typing import Any
    gp_norm = grand_prix.strip()
    cache_key = (year, gp_norm.lower(), session_type.lower())
    if cache_key in _SESSION_WEATHER_CACHE:
        return _SESSION_WEATHER_CACHE[cache_key]

    try:
        session = fastf1.get_session(year, gp_norm, session_type)
        session.load(telemetry=False, weather=True, messages=False)

        total_laps = 57
        if hasattr(session, 'laps') and not session.laps.empty:
            if 'LapNumber' in session.laps.columns:
                max_lap = session.laps['LapNumber'].max()
                if not pd.isna(max_lap) and max_lap > 0:
                    total_laps = int(max_lap)

        track_temp = 38.0
        air_temp = 25.0
        humidity = 45.0
        rainfall = False
        rain_intensity = 0.0

        if hasattr(session, 'weather_data') and not session.weather_data.empty:
            w = session.weather_data
            if 'TrackTemp' in w.columns and not w['TrackTemp'].dropna().empty:
                track_temp = round(float(w['TrackTemp'].mean()), 1)
            if 'AirTemp' in w.columns and not w['AirTemp'].dropna().empty:
                air_temp = round(float(w['AirTemp'].mean()), 1)
            if 'Humidity' in w.columns and not w['Humidity'].dropna().empty:
                humidity = round(float(w['Humidity'].mean()), 1)
            if 'Rainfall' in w.columns and not w['Rainfall'].dropna().empty:
                rainfall = bool(w['Rainfall'].any())
                if rainfall:
                    rain_intensity = 1.2

        result = {
            "year": year,
            "grand_prix": grand_prix,
            "session_type": session_type,
            "total_laps": total_laps,
            "track_temp_celsius": track_temp,
            "air_temp_celsius": air_temp,
            "humidity_pct": humidity,
            "is_rainfall": rainfall,
            "rainfall_intensity_mm_per_min": rain_intensity,
            "api_source": f"FastF1 API ({year} {grand_prix})"
        }
        _SESSION_WEATHER_CACHE[cache_key] = result
        return result
    except Exception as e:
        print(f"Weather/laps fetch fallback for {year} {grand_prix}: {e}")
        from app.services.tyre_service import get_circuit_tyre_profile
        profile = get_circuit_tyre_profile(grand_prix)
        fallback = {
            "year": year,
            "grand_prix": grand_prix,
            "session_type": session_type,
            "total_laps": profile.get("total_laps", 57),
            "track_temp_celsius": 38.0,
            "air_temp_celsius": 25.0,
            "humidity_pct": 45.0,
            "is_rainfall": False,
            "rainfall_intensity_mm_per_min": 0.0,
            "api_source": "Circuit Database Fallback"
        }
        _SESSION_WEATHER_CACHE[cache_key] = fallback
        return fallback

async def get_session_weather_and_laps_async(year: int = 2024, grand_prix: str = "Monza", session_type: str = "Race") -> dict[str, Any]:
    return await run_in_threadpool(get_session_weather_and_laps, year, grand_prix, session_type)

