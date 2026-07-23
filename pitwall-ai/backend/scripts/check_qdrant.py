import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from qdrant_client import AsyncQdrantClient
from app.config import settings

async def main():
    if not settings.QDRANT_URL or not settings.QDRANT_API_KEY:
        print("[ERROR] Qdrant credentials missing.")
        return

    client = AsyncQdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
    try:
        info = await client.get_collection("radio_transcripts")
        points_count = info.points_count
        status = info.status
        print(f"[STATUS] Qdrant Collection Status: {status}")
        print(f"[COUNT] Total Vector Points Currently Indexed: {points_count}")
    except Exception as e:
        print(f"[ERROR] Error checking collection: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
