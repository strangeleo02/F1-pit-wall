import os
import fastf1
from app.config import settings

# Configure FastF1 cache
if not os.path.exists(settings.FASTF1_CACHE_DIR):
    os.makedirs(settings.FASTF1_CACHE_DIR)
fastf1.Cache.enable_cache(settings.FASTF1_CACHE_DIR)

def get_telemetry(year: int, grand_prix: str, session_type: str, driver_code: str):
    """
    Fetches basic lap time and speed telemetry data for a specific driver.

    Args:
        year (int): The year of the race (e.g., 2023).
        grand_prix (str): The name of the Grand Prix or location (e.g., 'Monza').
        session_type (str): The session type (e.g., 'R' for Race, 'Q' for Qualifying).
        driver_code (str): The 3-letter driver code (e.g., 'VER', 'HAM').

    Returns:
        dict: A dictionary containing lap times and basic telemetry summary.
    """
    try:
        # Load the session
        session = fastf1.get_session(year, grand_prix, session_type)
        session.load(telemetry=True, weather=False, messages=False)

        # Get driver's laps
        driver_laps = session.laps.pick_driver(driver_code)

        if driver_laps.empty:
            return {"error": f"No laps found for driver {driver_code} in {year} {grand_prix} {session_type}."}

        # Extract fastest lap and its telemetry
        fastest_lap = driver_laps.pick_fastest()
        telemetry = fastest_lap.get_telemetry()

        # Extract basic data: lap times and max speed
        laps_data = driver_laps[['LapNumber', 'LapTime']].dropna().to_dict(orient='records')

        # Convert Timedelta to string for JSON serialization
        for lap in laps_data:
            if hasattr(lap['LapTime'], 'total_seconds'):
                lap['LapTime'] = lap['LapTime'].total_seconds()

        max_speed = float(telemetry['Speed'].max()) if not telemetry.empty else None

        return {
            "driver": driver_code,
            "fastest_lap_time_seconds": fastest_lap['LapTime'].total_seconds() if hasattr(fastest_lap['LapTime'], 'total_seconds') else None,
            "max_speed_kph": max_speed,
            "laps": laps_data
        }
    except Exception as e:
        return {"error": f"Failed to fetch telemetry: {str(e)}"}
