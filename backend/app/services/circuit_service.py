import httpx
import json
from typing import Optional
from fastapi.concurrency import run_in_threadpool

# Official mapping of F1 Grand Prix search keys to bacinger/f1-circuits GeoJSON file identifiers
CIRCUIT_GEOJSON_MAP: dict[str, str] = {
    "baku": "az-2016",
    "azerbaijan": "az-2016",
    "monza": "it-1922",
    "italy": "it-1922",
    "italian": "it-1922",
    "monaco": "mc-1929",
    "silverstone": "gb-1948",
    "great britain": "gb-1948",
    "british": "gb-1948",
    "spa": "be-1925",
    "belgian": "be-1925",
    "belgium": "be-1925",
    "bahrain": "bh-2004",
    "sakhir": "bh-2004",
    "singapore": "sg-2008",
    "marina bay": "sg-2008",
    "suzuka": "jp-1962",
    "japan": "jp-1962",
    "japanese": "jp-1962",
    "austin": "us-2012",
    "united states": "us-2012",
    "cota": "us-2012",
    "melbourne": "au-1996",
    "australian": "au-1996",
    "australia": "au-1996",
    "interlagos": "br-1940",
    "brazil": "br-1940",
    "são paulo": "br-1940",
    "zandvoort": "nl-1948",
    "dutch": "nl-1948",
    "red bull ring": "at-1969",
    "austria": "at-1969",
    "austrian": "at-1969",
    "spielberg": "at-1969",
    "barcelona": "es-1991",
    "spanish": "es-1991",
    "catalunya": "es-1991",
    "hungaroring": "hu-1986",
    "hungary": "hu-1986",
    "hungarian": "hu-1986",
    "las vegas": "us-2023",
    "miami": "us-2022",
    "jeddah": "sa-2021",
    "saudi arabia": "sa-2021",
    "qatar": "qa-2021",
    "lusail": "qa-2021",
    "shanghai": "cn-2004",
    "china": "cn-2004",
    "chinese": "cn-2004",
    "imola": "it-1953",
    "emilia romagna": "it-1953",
    "mexico": "mx-1962",
    "mexican": "mx-1962",
    "mexico city": "mx-1962",
    "abu dhabi": "ae-2009",
    "yas marina": "ae-2009"
}

# Curated landmark turn annotations
TRACK_CORNER_DATABASE: dict[str, list[dict]] = {
    "monza": [
        {"number": "T1-T2", "name": "Variante del Rettifilo", "distance_pct": 12.0},
        {"number": "T4-T5", "name": "Variante della Roggia", "distance_pct": 32.0},
        {"number": "T6-T7", "name": "Curva di Lesmo", "distance_pct": 46.0},
        {"number": "T8-T10", "name": "Variante Ascari", "distance_pct": 72.0},
        {"number": "T11", "name": "Curva Parabolica (Alboreto)", "distance_pct": 91.0}
    ],
    "baku": [
        {"number": "T1", "name": "Turn 1 Heavy Braking Zone", "distance_pct": 8.0},
        {"number": "T3", "name": "Turn 3 90° Corner", "distance_pct": 20.0},
        {"number": "T7-T12", "name": "Old City Icherisheher Castle Section", "distance_pct": 45.0},
        {"number": "T16", "name": "Turn 16 Main Straight Entry", "distance_pct": 75.0},
        {"number": "T20", "name": "Neftchilar Avenue 2.2km Straight", "distance_pct": 92.0}
    ],
    "monaco": [
        {"number": "T1", "name": "Sainte Dévote", "distance_pct": 8.0},
        {"number": "T3", "name": "Massenet", "distance_pct": 22.0},
        {"number": "T4", "name": "Casino Square", "distance_pct": 28.0},
        {"number": "T6", "name": "Grand Hotel Hairpin", "distance_pct": 42.0},
        {"number": "T10-T11", "name": "Nouvelle Chicane", "distance_pct": 62.0},
        {"number": "T15-T16", "name": "Piscine (Swimming Pool)", "distance_pct": 82.0},
        {"number": "T18-T19", "name": "Rascasse & Antony Noghès", "distance_pct": 93.0}
    ],
    "spa": [
        {"number": "T1", "name": "La Source", "distance_pct": 6.0},
        {"number": "T2-T4", "name": "Eau Rouge & Raidillon", "distance_pct": 18.0},
        {"number": "T5-T7", "name": "Les Combes", "distance_pct": 38.0},
        {"number": "T8", "name": "Bruxelles", "distance_pct": 46.0},
        {"number": "T10-T11", "name": "Pouhon", "distance_pct": 58.0},
        {"number": "T14-T15", "name": "Stavelot", "distance_pct": 76.0},
        {"number": "T18-T19", "name": "Bus Stop Chicane", "distance_pct": 94.0}
    ],
    "silverstone": [
        {"number": "T1-T2", "name": "Abbey & Farm", "distance_pct": 8.0},
        {"number": "T3-T4", "name": "Village & Loop", "distance_pct": 18.0},
        {"number": "T6", "name": "Brooklands", "distance_pct": 32.0},
        {"number": "T9", "name": "Copse", "distance_pct": 52.0},
        {"number": "T10-T14", "name": "Maggotts, Becketts & Chapel", "distance_pct": 66.0},
        {"number": "T15", "name": "Stowe", "distance_pct": 80.0},
        {"number": "T16-T18", "name": "Vale & Club", "distance_pct": 92.0}
    ]
}

# Cache for fetched GeoJSON circuit coordinates
_GEOJSON_CACHE: dict[str, list[dict]] = {}

def fetch_official_geojson_points(circuit_id: str) -> list[dict]:
    """
    Fetches official track LineString coordinates from bacinger/f1-circuits open GitHub API dataset.
    """
    if circuit_id in _GEOJSON_CACHE:
        return _GEOJSON_CACHE[circuit_id]

    raw_url = f"https://raw.githubusercontent.com/bacinger/f1-circuits/master/circuits/{circuit_id}.geojson"
    try:
        with httpx.Client(timeout=5.0) as client:
            res = client.get(raw_url)
            if res.status_code == 200:
                data = res.json()
                features = data.get("features", [])
                for feat in features:
                    geom = feat.get("geometry", {})
                    if geom.get("type") == "LineString":
                        coords = geom.get("coordinates", [])
                        if coords:
                            points = []
                            total = len(coords)
                            for idx, c in enumerate(coords):
                                # c = [lon, lat]
                                points.append({
                                    "x": float(c[0]),
                                    "y": float(c[1]),
                                    "distance_pct": round((idx / (total - 1)) * 100, 2)
                                })
                            _GEOJSON_CACHE[circuit_id] = points
                            return points
    except Exception as e:
        print(f"GeoJSON fetch warning for {circuit_id}: {e}")

    return []

def get_circuit_layout(grand_prix: str) -> dict:
    """
    Returns official GeoJSON LineString coordinates and landmark turn annotations for a Grand Prix.
    """
    clean_key = grand_prix.lower().replace(" grand prix", "").replace("gp", "").strip()
    
    # Resolve circuit identifier
    circuit_id = CIRCUIT_GEOJSON_MAP.get(clean_key, "az-2016")
    for k, cid in CIRCUIT_GEOJSON_MAP.items():
        if k in clean_key:
            circuit_id = cid
            break

    geojson_pts = fetch_official_geojson_points(circuit_id)

    corners = TRACK_CORNER_DATABASE.get(clean_key, [
        {"number": "T1", "name": "Turn 1", "distance_pct": 10.0},
        {"number": "S1", "name": "Sector 1 Split", "distance_pct": 33.3},
        {"number": "S2", "name": "Sector 2 Split", "distance_pct": 66.6},
        {"number": "T-Final", "name": "Final Corner", "distance_pct": 92.0}
    ])

    return {
        "grand_prix": grand_prix,
        "circuit_key": clean_key,
        "circuit_id": circuit_id,
        "corners": corners,
        "points": geojson_pts
    }

async def get_circuit_layout_async(grand_prix: str) -> dict:
    """Asynchronously fetches official GeoJSON circuit geometry."""
    return await run_in_threadpool(get_circuit_layout, grand_prix)
