import json
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from qdrant_client import AsyncQdrantClient

from app.config import settings
from app.exceptions import PitWallException, pitwall_exception_handler
from app.routers import strategy, meta, history, simulation, eval
from app.services.vector_db import ensure_collection_exists

def _background_warmup():
    """
    Pre-import heavy libraries in a background thread AFTER the server port binds.
    This eliminates the lazy-import tax on the first real API request:
    - fastf1 + pandas + numpy  (~150MB, ~5-8s)
    - sentence_transformers + PyTorch (~300MB, ~10-15s)
    Called once from the lifespan startup handler.
    """
    try:
        print("🔥 [warmup] Pre-importing fastf1 + pandas + numpy...")
        from app.services.f1_service import _ensure_f1_libs, get_season_schedule
        _ensure_f1_libs()
        print("✅ [warmup] fastf1 ready. Pre-loading season schedule caches...")
        try:
            get_season_schedule(2023)
            get_season_schedule(2024)
            print("✅ [warmup] 2023 & 2024 schedules pre-cached in memory.")
        except Exception as sc_err:
            print(f"⚠️ [warmup] Schedule pre-load warning: {sc_err}")
    except Exception as e:
        print(f"⚠️ [warmup] fastf1 import warning: {e}")

    try:
        print("🔥 [warmup] Pre-importing sentence_transformers + PyTorch...")
        from app.services.embedding_service import get_embedding_model
        get_embedding_model()
        print("✅ [warmup] Embedding model ready.")
    except Exception as e:
        print(f"⚠️ [warmup] Embedding import warning: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan handler for startup initialization and graceful shutdown.
    """
    print("🏎️ Starting PitWall AI Backend...")

    if settings.QDRANT_URL and settings.QDRANT_API_KEY:
        try:
            client = AsyncQdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
            print("📦 Verifying Qdrant 'radio_transcripts' vector collection...")
            await ensure_collection_exists(client)
            from app.ingestion.fia_ingestion import ensure_fia_collection_exists
            await ensure_fia_collection_exists(client)
            await client.close()
            print("✅ Qdrant collections initialized.")
        except Exception as e:
            print(f"⚠️ Qdrant startup warning: {e}")
    else:
        print("⚠️ Qdrant credentials not configured in environment.")

    # Kick off heavy-library warmup in a daemon thread so it doesn't block
    # the port from binding. First real requests will be fast once this completes.
    warmup_thread = threading.Thread(target=_background_warmup, daemon=True, name="lib-warmup")
    warmup_thread.start()

    yield
    print("🛑 Shutting down PitWall AI Backend...")

app = FastAPI(
    title="PitWall AI Backend",
    description="Backend API for PitWall AI: an interactive F1 telemetry and radio transcript RAG application.",
    version="1.0.0",
    lifespan=lifespan
)

def _parse_cors_origins(raw: str) -> list[str]:
    """Parse CORS_ORIGINS env var — handles JSON array, comma-separated, or plain '*'."""
    raw = raw.strip()
    if raw.startswith("["):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
    return [o.strip() for o in raw.split(",") if o.strip()]

from fastapi.middleware.gzip import GZipMiddleware

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_cors_origins(settings.CORS_ORIGINS),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enable GZip compression for responses > 500 bytes (compresses telemetry & transcripts by ~85%)
app.add_middleware(GZipMiddleware, minimum_size=500)

import os
from fastapi.staticfiles import StaticFiles

# Register Exception Handlers
app.add_exception_handler(PitWallException, pitwall_exception_handler)

# Include routers
app.include_router(strategy.router, prefix="/api/v1")
app.include_router(meta.router, prefix="/api/v1")
app.include_router(history.router, prefix="/api/v1")
app.include_router(simulation.router, prefix="/api/v1")
app.include_router(eval.router, prefix="/api/v1")


@app.get("/", tags=["API Info"])
async def root():
    """Root API status endpoint for decoupled backend."""
    return {
        "service": "PitWall AI Backend API",
        "status": "online",
        "docs_url": "/docs",
        "health_url": "/health",
        "version": "1.0.0"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint to verify the API is running."""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
