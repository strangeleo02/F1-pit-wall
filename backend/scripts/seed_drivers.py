import asyncio
import os
import sys

# Ensure backend root directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.dependencies import get_qdrant_client
from app.services.vector_db import cache_driver_lineup_in_qdrant, ensure_collection_exists

SEASON_DRIVER_LINEUPS = {
    2023: [
        {"code": "VER", "name": "Max Verstappen", "number": "1", "team": "Red Bull Racing"},
        {"code": "PER", "name": "Sergio Perez", "number": "11", "team": "Red Bull Racing"},
        {"code": "HAM", "name": "Lewis Hamilton", "number": "44", "team": "Mercedes"},
        {"code": "RUS", "name": "George Russell", "number": "63", "team": "Mercedes"},
        {"code": "LEC", "name": "Charles Leclerc", "number": "16", "team": "Ferrari"},
        {"code": "SAI", "name": "Carlos Sainz", "number": "55", "team": "Ferrari"},
        {"code": "NOR", "name": "Lando Norris", "number": "4", "team": "McLaren"},
        {"code": "PIA", "name": "Oscar Piastri", "number": "81", "team": "McLaren"},
        {"code": "ALO", "name": "Fernando Alonso", "number": "14", "team": "Aston Martin"},
        {"code": "STR", "name": "Lance Stroll", "number": "18", "team": "Aston Martin"},
        {"code": "GAS", "name": "Pierre Gasly", "number": "10", "team": "Alpine"},
        {"code": "OCO", "name": "Esteban Ocon", "number": "31", "team": "Alpine"},
        {"code": "ALB", "name": "Alexander Albon", "number": "23", "team": "Williams"},
        {"code": "SAR", "name": "Logan Sargeant", "number": "2", "team": "Williams"},
        {"code": "TSU", "name": "Yuki Tsunoda", "number": "22", "team": "AlphaTauri"},
        {"code": "RIC", "name": "Daniel Ricciardo", "number": "3", "team": "AlphaTauri"},
        {"code": "MAG", "name": "Kevin Magnussen", "number": "20", "team": "Haas F1 Team"},
        {"code": "HUL", "name": "Nico Hulkenberg", "number": "27", "team": "Haas F1 Team"},
        {"code": "BOT", "name": "Valtteri Bottas", "number": "77", "team": "Alfa Romeo"},
        {"code": "ZHO", "name": "Zhou Guanyu", "number": "24", "team": "Alfa Romeo"}
    ],
    2024: [
        {"code": "VER", "name": "Max Verstappen", "number": "1", "team": "Red Bull Racing"},
        {"code": "PER", "name": "Sergio Perez", "number": "11", "team": "Red Bull Racing"},
        {"code": "HAM", "name": "Lewis Hamilton", "number": "44", "team": "Mercedes"},
        {"code": "RUS", "name": "George Russell", "number": "63", "team": "Mercedes"},
        {"code": "LEC", "name": "Charles Leclerc", "number": "16", "team": "Ferrari"},
        {"code": "SAI", "name": "Carlos Sainz", "number": "55", "team": "Ferrari"},
        {"code": "NOR", "name": "Lando Norris", "number": "4", "team": "McLaren"},
        {"code": "PIA", "name": "Oscar Piastri", "number": "81", "team": "McLaren"},
        {"code": "ALO", "name": "Fernando Alonso", "number": "14", "team": "Aston Martin"},
        {"code": "STR", "name": "Lance Stroll", "number": "18", "team": "Aston Martin"},
        {"code": "GAS", "name": "Pierre Gasly", "number": "10", "team": "Alpine"},
        {"code": "OCO", "name": "Esteban Ocon", "number": "31", "team": "Alpine"},
        {"code": "ALB", "name": "Alexander Albon", "number": "23", "team": "Williams"},
        {"code": "COL", "name": "Franco Colapinto", "number": "43", "team": "Williams"},
        {"code": "TSU", "name": "Yuki Tsunoda", "number": "22", "team": "RB"},
        {"code": "LAW", "name": "Liam Lawson", "number": "30", "team": "RB"},
        {"code": "MAG", "name": "Kevin Magnussen", "number": "20", "team": "Haas F1 Team"},
        {"code": "HUL", "name": "Nico Hulkenberg", "number": "27", "team": "Haas F1 Team"},
        {"code": "BOT", "name": "Valtteri Bottas", "number": "77", "team": "Kick Sauber"},
        {"code": "ZHO", "name": "Zhou Guanyu", "number": "24", "team": "Kick Sauber"}
    ],
    2025: [
        {"code": "VER", "name": "Max Verstappen", "number": "1", "team": "Red Bull Racing"},
        {"code": "LAW", "name": "Liam Lawson", "number": "30", "team": "Red Bull Racing"},
        {"code": "HAM", "name": "Lewis Hamilton", "number": "44", "team": "Ferrari"},
        {"code": "LEC", "name": "Charles Leclerc", "number": "16", "team": "Ferrari"},
        {"code": "NOR", "name": "Lando Norris", "number": "4", "team": "McLaren"},
        {"code": "PIA", "name": "Oscar Piastri", "number": "81", "team": "McLaren"},
        {"code": "RUS", "name": "George Russell", "number": "63", "team": "Mercedes"},
        {"code": "ANT", "name": "Kimi Antonelli", "number": "12", "team": "Mercedes"},
        {"code": "ALO", "name": "Fernando Alonso", "number": "14", "team": "Aston Martin"},
        {"code": "STR", "name": "Lance Stroll", "number": "18", "team": "Aston Martin"},
        {"code": "SAI", "name": "Carlos Sainz", "number": "55", "team": "Williams"},
        {"code": "ALB", "name": "Alexander Albon", "number": "23", "team": "Williams"},
        {"code": "GAS", "name": "Pierre Gasly", "number": "10", "team": "Alpine"},
        {"code": "DOO", "name": "Jack Doohan", "number": "7", "team": "Alpine"},
        {"code": "TSU", "name": "Yuki Tsunoda", "number": "22", "team": "RB"},
        {"code": "HAD", "name": "Isack Hadjar", "number": "6", "team": "RB"},
        {"code": "OCO", "name": "Esteban Ocon", "number": "31", "team": "Haas F1 Team"},
        {"code": "BEA", "name": "Oliver Bearman", "number": "87", "team": "Haas F1 Team"},
        {"code": "HUL", "name": "Nico Hulkenberg", "number": "27", "team": "Kick Sauber"},
        {"code": "BOR", "name": "Gabriel Bortoleto", "number": "5", "team": "Kick Sauber"}
    ]
}

FEATURED_GRAND_PRIX = [
    "Monza", "Monaco", "Silverstone", "Spa", "Bahrain", "Baku",
    "Singapore", "Suzuka", "Austin", "Melbourne", "Interlagos",
    "Zandvoort", "Spielberg", "Barcelona", "Hungaroring", "Las Vegas",
    "Miami", "Jeddah", "Qatar", "Shanghai", "Imola", "Montreal"
]

async def seed_driver_lineups():
    client = await get_qdrant_client()
    if not client:
        print("[ERROR] Qdrant client is not configured or unavailable.")
        return

    print("[INFO] Starting Qdrant Driver Lineups Seeding Process...")
    await ensure_collection_exists(client)

    tasks = []
    for year, drivers in SEASON_DRIVER_LINEUPS.items():
        for gp in FEATURED_GRAND_PRIX:
            for session in ["R", "Q"]:
                tasks.append(
                    cache_driver_lineup_in_qdrant(
                        client=client,
                        year=year,
                        grand_prix=gp,
                        session_type=session,
                        drivers=drivers
                    )
                )

    results = await asyncio.gather(*tasks)
    total_driver_points = sum(results)
    total_inserted_sessions = sum(1 for r in results if r > 0)

    print(f"[SUCCESS] Seeded {total_driver_points} driver records across {total_inserted_sessions} sessions into Qdrant driver_lineups collection.")

if __name__ == "__main__":
    asyncio.run(seed_driver_lineups())
