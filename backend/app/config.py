from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Pre-load environment variables from all possible root paths
_BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(_BASE_DIR / ".env")
load_dotenv(_BASE_DIR.parent / ".env")
load_dotenv(_BASE_DIR.parent.parent / ".env")

class Settings(BaseSettings):
    """
    Application configuration via environment variables.
    Pydantic will automatically read from .env if present.
    """
    GROQ_API_KEY: str = ""
    QDRANT_URL: str = ""
    QDRANT_API_KEY: str = ""
    HF_TOKEN: str = ""

    # Groq Settings
    GROQ_MODEL_NAME: str = "llama-3.3-70b-versatile"

    # CORS Settings
    CORS_ORIGINS: list[str] = ["*"]

    # FastF1 Settings
    FASTF1_CACHE_DIR: str = "cache/"

    # Embedding Settings
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"

    model_config = SettingsConfigDict(
        env_file=(".env", str(_BASE_DIR / ".env"), str(_BASE_DIR.parent / ".env")),
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Global settings instance
settings = Settings()
