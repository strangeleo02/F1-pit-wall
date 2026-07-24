import os
import sys
import asyncio
from pathlib import Path

# Ensure backend path is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import fastf1
from app.config import settings
from app.services.f1_service import prewarm_session_cache

POPULAR_GRAND_PRIX_LOCATIONS = [
    "Monza", "Silverstone", "Monaco", "Spa", "Abu Dhabi",
    "Austrian", "Bahrain", "Spanish", "Japanese", "Singapore",
    "Austin", "Brazilian", "Canadian", "Hungarian", "Australian",
    "Saudi Arabia", "Miami", "Las Vegas", "Qatar", "Emilia Romagna",
    "Netherlands", "Azerbaijan", "China", "Mexico"
]

YEARS = [2023, 2024, 2025, 2026]
SESSION_TYPES = ["R", "Q"]

def main():
    print("🏎️ Initializing PitWall AI FastF1 Race Timings & Telemetry Pre-caching Script...")
    if not os.path.exists(settings.FASTF1_CACHE_DIR):
        os.makedirs(settings.FASTF1_CACHE_DIR)
    fastf1.Cache.enable_cache(settings.FASTF1_CACHE_DIR)
    print(f"📁 FastF1 Cache Directory: {os.path.abspath(settings.FASTF1_CACHE_DIR)}")

    success_count = 0
    skipped_count = 0
    error_count = 0

    for year in YEARS:
        print(f"\n🗓️ --- Pre-caching Race Timings for Season {year} ---")
        for gp in POPULAR_GRAND_PRIX_LOCATIONS:
            for s_type in SESSION_TYPES:
                session_label = f"{year} {gp} ({'Race' if s_type == 'R' else 'Qualifying'})"
                print(f"⏱️ Pre-warming timing cache for {session_label}...")
                try:
                    prewarm_session_cache(year=year, grand_prix=gp, session_type=s_type)
                    success_count += 1
                    print(f"   ↳ [OK] Cached {session_label}")
                except Exception as e:
                    error_count += 1
                    print(f"   ↳ [NOTICE] Could not cache {session_label}: {e}")

    print("\n==================================================")
    print(f"🎉 FastF1 Pre-caching Complete! Successfully Cached: {success_count} sessions | Notices: {error_count}")
    print("==================================================")

if __name__ == "__main__":
    main()
