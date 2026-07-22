from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application configuration via environment variables.
    Pydantic will automatically read from .env if present.
    """
    GROQ_API_KEY: str = ""
    QDRANT_URL: str = ""
    QDRANT_API_KEY: str = ""

    # FastF1 Settings
    FASTF1_CACHE_DIR: str = "cache/"

    # Embedding Settings
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

# Global settings instance
settings = Settings()
