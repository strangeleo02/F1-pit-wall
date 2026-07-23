import sys
import asyncio
from pathlib import Path

# Ensure backend directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from qdrant_client import AsyncQdrantClient
from app.config import settings
from app.services.vector_db import ensure_collection_exists, upsert_telemetry_records, TELEMETRY_COLLECTION_NAME
from app.services.f1_service import get_telemetry
from app.services.embedding_service import generate_embeddings_batch_async

POPULAR_GRAND_PRIX_LOCATIONS = [
    "Monza", "Silverstone", "Monaco", "Spa", "Abu Dhabi",
    "Austrian", "Bahrain", "Spanish", "Japanese", "Singapore",
    "Austin", "Brazilian", "Canadian", "Hungarian", "Australian"
]

YEARS = [2023, 2024, 2025, 2026]
DRIVERS = ["VER", "HAM", "LEC", "NOR", "PIA", "SAI", "RUS", "PER", "ALO", "TSU"]

async def main():
    print("🏎️ Initializing PitWall AI Qdrant Telemetry Collection Population Script...")
    if not settings.QDRANT_URL or not settings.QDRANT_API_KEY:
        print("❌ Error: QDRANT_URL or QDRANT_API_KEY missing from environment variables.")
        return

    client = AsyncQdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)

    print("📦 Ensuring Qdrant 'race_telemetry' and 'radio_transcripts' collections exist...")
    await ensure_collection_exists(client)
    print("✅ Collections verified/created.")

    total_indexed = 0

    for year in YEARS:
        print(f"\n🗓️ --- Ingesting Telemetry for Season {year} ---")
        for gp in POPULAR_GRAND_PRIX_LOCATIONS:
            records = []
            summary_texts = []
            for driver in DRIVERS:
                try:
                    t = get_telemetry(year=year, grand_prix=gp, session_type="R", driver_code=driver)
                    lap_num = t.get("fastest_lap_number")
                    lap_time = t.get("fastest_lap_time_seconds")
                    max_speed = t.get("max_speed_kph")
                    throttle = t.get("avg_throttle_percentage")
                    brakes = t.get("braking_zones_count")

                    summary_text = (
                        f"{year} {gp} Grand Prix (Race) - Driver {driver}: "
                        f"Fastest Lap {lap_num} with lap time {lap_time}s, top speed {max_speed} km/h, "
                        f"average throttle {throttle}%, {brakes} braking zones."
                    )

                    payload = {
                        "year": year,
                        "grand_prix": gp,
                        "session": "R",
                        "driver": driver,
                        "fastest_lap_number": lap_num,
                        "fastest_lap_time_seconds": lap_time,
                        "max_speed_kph": max_speed,
                        "avg_throttle_percentage": throttle,
                        "braking_zones_count": brakes,
                        "summary_text": summary_text
                    }
                    records.append(payload)
                    summary_texts.append(summary_text)
                except Exception:
                    continue

            if records:
                print(f"📡 Indexing telemetry for {year} {gp} ({len(records)} drivers)...")
                embeddings = await generate_embeddings_batch_async(summary_texts)
                count = await upsert_telemetry_records(client, records, embeddings)
                total_indexed += count
                print(f"   ↳ Indexed {count} telemetry vectors into '{TELEMETRY_COLLECTION_NAME}'.")

    print("\n==================================================")
    print(f"🎉 Telemetry Collection Ingestion Complete! Total Points Indexed: {total_indexed}")
    print("==================================================")
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
