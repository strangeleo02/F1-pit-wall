import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from qdrant_client import AsyncQdrantClient
from app.config import settings
from app.ingestion.radio_ingestion import RadioIngestionPipeline
from app.services.vector_db import ensure_collection_exists

async def main():
    if not settings.QDRANT_URL or not settings.QDRANT_API_KEY:
        print("[ERROR] Qdrant credentials missing.")
        return

    client = AsyncQdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
    await ensure_collection_exists(client)

    pipeline = RadioIngestionPipeline(qdrant_client=client)
    print("[INFO] Ingesting 2023 Monza Race transcripts...")
    res = await pipeline.ingest_session(year=2023, grand_prix="Monza", session_type="R")
    print(f"[RESULT] Processed: {res.get('processed_count')} | Indexed into Qdrant: {res.get('indexed_count')}")

    info = await client.get_collection("radio_transcripts")
    print(f"[QDRANT COUNT] Total Points in Qdrant: {info.points_count}")
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
