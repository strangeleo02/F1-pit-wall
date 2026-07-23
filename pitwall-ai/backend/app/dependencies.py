from typing import AsyncGenerator
from qdrant_client import AsyncQdrantClient
import groq
from app.config import settings

async def get_qdrant_client() -> AsyncQdrantClient | None:
    """FastAPI dependency for AsyncQdrantClient instance."""
    if not settings.QDRANT_URL or not settings.QDRANT_API_KEY:
        return None
    return AsyncQdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY
    )

async def get_groq_client() -> groq.AsyncGroq | None:
    """FastAPI dependency for AsyncGroq client instance."""
    if not settings.GROQ_API_KEY:
        return None
    return groq.AsyncGroq(api_key=settings.GROQ_API_KEY)
