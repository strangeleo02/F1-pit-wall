import httpx
from typing import Optional
from fastapi.concurrency import run_in_threadpool

JOLPICA_BASE_URL = "http://api.jolpi.ca/ergast/f1"
FALLBACK_BASE_URL = "https://ergast.com/api/f1"

# Memory cache for historical requests
_HISTORY_CACHE: dict[str, dict] = {}

def clear_history_cache() -> None:
    """Clears history cache (primarily for testing)."""
    _HISTORY_CACHE.clear()

def fetch_pitstops_sync(year: int, round_num: Optional[int] = None) -> list[dict]:
    """
    Fetches pit stop benchmark timings for a specific season and optional round.
    """
    cache_key = f"pitstops_{year}_{round_num}"
    if cache_key in _HISTORY_CACHE:
        return _HISTORY_CACHE[cache_key].get("pitstops", [])

    endpoint = f"/{year}/{round_num}/pitstops.json?limit=100" if round_num else f"/{year}/pitstops.json?limit=100"
    
    for base in [JOLPICA_BASE_URL, FALLBACK_BASE_URL]:
        try:
            with httpx.Client(timeout=3.0) as client:
                res = client.get(f"{base}{endpoint}")
                if res.status_code == 200:
                    data = res.json()
                    mr_data = data.get("MRData", {})
                    race_table = mr_data.get("RaceTable", {})
                    races = race_table.get("Races", [])
                    
                    stops = []
                    for race in races:
                        race_name = race.get("raceName", "Grand Prix")
                        circuit_name = race.get("Circuit", {}).get("circuitName", "")
                        for stop in race.get("PitStops", []):
                            stops.append({
                                "race_name": race_name,
                                "circuit": circuit_name,
                                "driver_id": stop.get("driverId"),
                                "lap": int(stop.get("lap", 0)),
                                "stop": int(stop.get("stop", 0)),
                                "duration": stop.get("duration", "0.000"),
                                "time": stop.get("time", "")
                            })
                    
                    _HISTORY_CACHE[cache_key] = {"pitstops": stops}
                    return stops
        except Exception as e:
            print(f"Jolpica/Ergast API pitstops fetch warning ({base}): {e}")
            continue

    return []

async def fetch_pitstops_async(year: int, round_num: Optional[int] = None) -> list[dict]:
    """Asynchronously fetches pit stop benchmarks."""
    return await run_in_threadpool(fetch_pitstops_sync, year, round_num)

def fetch_standings_sync(year: int, category: str = "driver") -> list[dict]:
    """
    Fetches World Championship standings (driver or constructor) for a given season.
    """
    cache_key = f"standings_{year}_{category}"
    if cache_key in _HISTORY_CACHE:
        return _HISTORY_CACHE[cache_key].get("standings", [])

    endpoint = f"/{year}/driverStandings.json" if category == "driver" else f"/{year}/constructorStandings.json"
    
    for base in [JOLPICA_BASE_URL, FALLBACK_BASE_URL]:
        try:
            with httpx.Client(timeout=3.0) as client:
                res = client.get(f"{base}{endpoint}")
                if res.status_code == 200:
                    data = res.json()
                    mr_data = data.get("MRData", {})
                    standings_table = mr_data.get("StandingsTable", {})
                    lists = standings_table.get("StandingsLists", [])
                    
                    standings = []
                    if lists:
                        current_list = lists[0]
                        if category == "driver":
                            for item in current_list.get("DriverStandings", []):
                                driver = item.get("Driver", {})
                                constructors = item.get("Constructors", [{}])
                                standings.append({
                                    "position": int(item.get("position", 0)),
                                    "points": float(item.get("points", 0)),
                                    "wins": int(item.get("wins", 0)),
                                    "driver_code": driver.get("code", driver.get("driverId", "")[:3].upper()),
                                    "driver_name": f"{driver.get('givenName', '')} {driver.get('familyName', '')}".strip(),
                                    "team": constructors[0].get("name", "Unknown Team") if constructors else "Unknown Team"
                                })
                        else:
                            for item in current_list.get("ConstructorStandings", []):
                                constructor = item.get("Constructor", {})
                                standings.append({
                                    "position": int(item.get("position", 0)),
                                    "points": float(item.get("points", 0)),
                                    "wins": int(item.get("wins", 0)),
                                    "team": constructor.get("name", ""),
                                    "nationality": constructor.get("nationality", "")
                                })
                    
                    _HISTORY_CACHE[cache_key] = {"standings": standings}
                    return standings
        except Exception as e:
            print(f"Jolpica/Ergast API standings fetch warning ({base}): {e}")
            continue

    return []

async def fetch_standings_async(year: int, category: str = "driver") -> list[dict]:
    """Asynchronously fetches driver/constructor standings."""
    return await run_in_threadpool(fetch_standings_sync, year, category)
