import json
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from qdrant_client import AsyncQdrantClient

from app.config import settings
from app.exceptions import PitWallException, pitwall_exception_handler
from app.routers import strategy, meta, history, simulation, eval
from app.services.vector_db import ensure_collection_exists

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan handler for startup initialization and graceful shutdown.
    """
    print("🏎️ Starting PitWall AI Backend...")
    print("ℹ️ Embedding model will load lazily on first request to stay within memory limits.")

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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_cors_origins(settings.CORS_ORIGINS),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
