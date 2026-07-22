from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Will import routers here
# from app.routers import strategy

app = FastAPI(
    title="PitWall AI Backend",
    description="Backend API for PitWall AI: an interactive F1 telemetry and radio transcript RAG application.",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from app.routers import strategy
app.include_router(strategy.router, prefix="/api/v1")

@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify the API is running."""
    return {"status": "ok"}
