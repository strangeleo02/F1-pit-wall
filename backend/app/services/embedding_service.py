import os
import threading
import httpx
from fastapi.concurrency import run_in_threadpool
from app.config import settings

# Global singleton instance & thread lock for local fallback
_model = None
_model_lock = threading.Lock()

def _generate_embedding_via_api(text: str) -> list[float] | None:
    """
    Attempts to generate 384-dim embedding via Hugging Face Inference API.
    Consumes 0 MB of local RAM, preventing PyTorch 400MB memory spikes on Render.
    """
    url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/{settings.EMBEDDING_MODEL_NAME}"
    headers = {}
    if settings.HF_TOKEN:
        headers["Authorization"] = f"Bearer {settings.HF_TOKEN}"

    try:
        with httpx.Client(timeout=8.0) as client:
            resp = client.post(url, json={"inputs": text, "options": {"wait_for_model": True}}, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                # If pipeline returns nested list [[...]], extract first list
                if isinstance(data, list):
                    if len(data) > 0 and isinstance(data[0], list):
                        return [float(x) for x in data[0]]
                    elif len(data) > 0 and isinstance(data[0], (int, float)):
                        return [float(x) for x in data]
    except Exception as e:
        print(f"ℹ️ HF Inference API embedding bypass info: {e}")

    return None

def get_embedding_model():
    """
    Returns local SentenceTransformer embedding model instance (fallback).
    Configured for minimal thread memory footprint.
    """
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                import torch
                torch.set_num_threads(1)  # Restrict PyTorch thread memory
                from sentence_transformers import SentenceTransformer
                print(f"📦 Loading local embedding model '{settings.EMBEDDING_MODEL_NAME}'...")
                if settings.HF_TOKEN:
                    os.environ["HF_TOKEN"] = settings.HF_TOKEN
                    os.environ["HUGGINGFACE_HUB_TOKEN"] = settings.HF_TOKEN
                    _model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME, use_auth_token=settings.HF_TOKEN)
                else:
                    _model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
                print("✅ Local embedding model loaded successfully.")
    return _model

def generate_embedding(text: str) -> list[float]:
    """
    Generates a vector embedding for text.
    First tries Hugging Face HTTP API (0 MB RAM), fallback to local model.
    """
    # Try 0-RAM HTTP API first
    api_emb = _generate_embedding_via_api(text)
    if api_emb:
        return api_emb

    # Local PyTorch model fallback
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
