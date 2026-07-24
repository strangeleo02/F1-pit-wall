from pathlib import Path
from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json

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

    # CORS Settings — accepts: "*", ["*"], or "https://a.com,https://b.com"
    CORS_ORIGINS: list[str] = ["*"]

    # FastF1 Settings
    FASTF1_CACHE_DIR: str = "cache/"

    # Embedding Settings
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            v = v.strip()
            # Handle JSON array string: ["https://foo.com", "*"]
            if v.startswith("["):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Handle comma-separated: https://foo.com,https://bar.com
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=(".env", str(_BASE_DIR / ".env"), str(_BASE_DIR.parent / ".env")),
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Global settings instance
settings = Settings()
