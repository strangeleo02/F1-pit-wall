from sentence_transformers import SentenceTransformer
from app.config import settings

# Load the model lazily or at startup
_model = None

def get_embedding_model():
    """Lazily loads the sentence transformer model."""
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
    return _model

def generate_embedding(text: str) -> list[float]:
    """
    Generates a vector embedding for the given text.

    Args:
        text (str): The text to embed.

    Returns:
        list[float]: The generated embedding vector.
    """
    model = get_embedding_model()
    # Ensure it returns a list of floats (Qdrant expects this)
    embedding = model.encode(text).tolist()
    return embedding
