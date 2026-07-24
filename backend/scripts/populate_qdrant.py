import asyncio
import os
import sys
from pathlib import Path

# Ensure backend path is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from qdrant_client import AsyncQdrantClient
from app.config import settings
from app.services.vector_db import ensure_collection_exists, COLLECTION_NAME
from app.ingestion.radio_ingestion import RadioIngestionPipeline
from app.services.openf1_service import OpenF1Service

# Major F1 Grand Prix locations for fallback/historical coverage
POPULAR_GRAND_PRIX_LOCATIONS = [
    "Monza", "Silverstone", "Monaco", "Spa", "Abu Dhabi",
    "Austrian", "Bahrain", "Spanish", "Japanese", "Singapore",
    "Austin", "Brazilian", "Canadian", "Hungarian", "Australian",
    "Saudi Arabia", "Miami", "Las Vegas", "Qatar", "Emilia Romagna",
    "Netherlands", "Azerbaijan", "China", "Mexico"
]

YEARS = list(range(2016, 2027))  # 2016 through 2026

async def get_indexed_sessions(client: AsyncQdrantClient) -> set[str]:
    """
    Retrieves set of keys representing already-indexed sessions in Qdrant.
    Matches session_key (e.g., 'key_9568') or year+gp combination (e.g., '2023_monza').
    """
    indexed = set()
    try:
        next_offset = None
        while True:
            records, next_offset = await client.scroll(
                collection_name=COLLECTION_NAME,
                limit=1000,
                offset=next_offset,
                with_payload=["year", "grand_prix", "session_key"],
                with_vectors=False
            )
            for r in records:
                if r.payload:
                    s_key = r.payload.get("session_key")
                    yr = r.payload.get("year")
                    gp = r.payload.get("grand_prix")
                    if s_key:
                        indexed.add(f"key_{s_key}")
                    if yr and gp:
                        indexed.add(f"{yr}_{str(gp).lower().strip()}")
            if not next_offset:
                break
    except Exception as e:
        print(f"⚠️ Notice reading existing Qdrant collection: {e}")
    return indexed

async def main():
    print("🏎️ Initializing PitWall AI Qdrant Bulk Ingestion & Resumption Script...")
    if not settings.QDRANT_URL or not settings.QDRANT_API_KEY:
        print("❌ Error: QDRANT_URL or QDRANT_API_KEY missing from environment variables.")
        return

    client = AsyncQdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)

    print("📦 Ensuring Qdrant 'radio_transcripts' collection exists...")
    await ensure_collection_exists(client)
    print("✅ Collection verified/created.")

    print("🔍 Inspecting existing points in Qdrant for auto-resumption...")
    already_indexed = await get_indexed_sessions(client)
    print(f"✅ Found data for {len(already_indexed)} indexed session references in Qdrant.")

    pipeline = RadioIngestionPipeline(qdrant_client=client)

    total_processed = 0
    total_indexed = 0

    print("\n📡 Querying OpenF1 API for dynamic session catalog...")
    openf1_sessions = OpenF1Service.get_sessions()
    race_sessions = []
    if isinstance(openf1_sessions, list):
        for s in openf1_sessions:
            if isinstance(s, dict):
                s_name = str(s.get("session_name") or s.get("session_type") or "").lower()
                if "race" in s_name or s_name == "r":
                    race_sessions.append(s)

    # Sort race sessions chronologically if date_start is present
    race_sessions.sort(key=lambda x: (x.get("year", 0), x.get("date_start", "")))

    processed_keys = set()

    if race_sessions:
        print(f"📋 Found {len(race_sessions)} Race sessions from OpenF1 up to latest race.")
        for s in race_sessions:
            session_key = s.get("session_key")
            year = s.get("year", 2024)
            gp = s.get("location") or s.get("country_name") or s.get("circuit_short_name") or "Race"
            gp_clean = str(gp).lower().strip()

            lookup_key = f"key_{session_key}" if session_key else f"{year}_{gp_clean}"
            if lookup_key in already_indexed or f"{year}_{gp_clean}" in already_indexed:
                print(f"⏭️ Skipping {year} {gp} (Session {session_key}) — already indexed.")
                continue

            print(f"📡 Ingesting {year} {gp} Grand Prix (Session {session_key})...")
            try:
                res = await pipeline.ingest_session(
                    year=year,
                    grand_prix=gp,
                    session_type="R",
                    session_key=session_key
                )
                processed = res.get("processed_count", 0)
                indexed = res.get("indexed_count", 0)
                total_processed += processed
                total_indexed += indexed
                if processed > 0:
                    print(f"   ↳ Processed: {processed} items | Indexed into Qdrant: {indexed} points.")
                    already_indexed.add(lookup_key)
                    already_indexed.add(f"{year}_{gp_clean}")
                processed_keys.add((year, gp_clean))
            except Exception as e:
                print(f"   ⚠️ Ingestion notice for {year} {gp}: {e}")

    # Fallback/historical loop for years & locations
    print("\n🗓️ Checking historical seasons (2016-2026) for remaining Grand Prix locations...")
    for year in YEARS:
        for gp in POPULAR_GRAND_PRIX_LOCATIONS:
            gp_clean = gp.lower().strip()
            if (year, gp_clean) in processed_keys or f"{year}_{gp_clean}" in already_indexed:
                continue

            print(f"📡 Ingesting historical {year} {gp} Grand Prix (Race)...")
            try:
                res = await pipeline.ingest_session(
                    year=year,
                    grand_prix=gp,
                    session_type="R"
                )
                processed = res.get("processed_count", 0)
                indexed = res.get("indexed_count", 0)
                total_processed += processed
                total_indexed += indexed
                if processed > 0:
                    print(f"   ↳ Processed: {processed} items | Indexed into Qdrant: {indexed} points.")
                    already_indexed.add(f"{year}_{gp_clean}")
            except Exception as e:
                print(f"   ⚠️ Ingestion notice for {year} {gp}: {e}")

    print("\n==================================================")
    print(f"🎉 Bulk Ingestion Complete! Total Transcripts Processed: {total_processed} | Total Qdrant Points Indexed: {total_indexed}")
    print("==================================================")
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
