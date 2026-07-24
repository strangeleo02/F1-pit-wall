import os
import threading
from sentence_transformers import SentenceTransformer
from fastapi.concurrency import run_in_threadpool
from app.config import settings

# Global singleton instance & thread lock
_model = None
_model_lock = threading.Lock()

def get_embedding_model() -> SentenceTransformer:
    """
    Returns the pre-loaded SentenceTransformer embedding model instance.
    Guaranteed thread-safe singleton: Loads model weights exactly ONCE into memory.
    """
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                print(f"📦 Loading embedding model '{settings.EMBEDDING_MODEL_NAME}' into memory (ONCE)...")
                if settings.HF_TOKEN:
                    os.environ["HF_TOKEN"] = settings.HF_TOKEN
                    os.environ["HUGGINGFACE_HUB_TOKEN"] = settings.HF_TOKEN
                    _model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME, use_auth_token=settings.HF_TOKEN)
                else:
                    _model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
                print("✅ Embedding model loaded successfully.")
    return _model

def generate_embedding(text: str) -> list[float]:
    """
    Generates a vector embedding for the given text (synchronous).

    Args:
        text (str): The text to embed.

    Returns:
        list[float]: The generated embedding vector.
    """
    model = get_embedding_model()
    embedding = model.encode(text).tolist()
    return embedding

async def generate_embedding_async(text: str) -> list[float]:
    """
    Asynchronously generates a vector embedding by running in a worker threadpool.

    Args:
        text (str): The text to embed.

    Returns:
        list[float]: The generated embedding vector.
    """
    return await run_in_threadpool(generate_embedding, text)

def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Generates vector embeddings for a list of texts in batch (synchronous).

    Args:
        texts (list[str]): List of texts to embed.

    Returns:
        list[list[float]]: List of embedding vectors.
    """
    if not texts:
        return []
    model = get_embedding_model()
    embeddings = model.encode(texts)
    return [emb.tolist() for emb in embeddings]

async def generate_embeddings_batch_async(texts: list[str]) -> list[list[float]]:
    """
    Asynchronously generates batch vector embeddings by running in a worker threadpool.

    Args:
        texts (list[str]): List of texts to embed.

    Returns:
        list[list[float]]: List of embedding vectors.
    """
    return await run_in_threadpool(generate_embeddings_batch, texts)
