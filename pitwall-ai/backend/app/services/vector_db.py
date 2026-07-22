from qdrant_client import QdrantClient
from app.config import settings

# Initialize Qdrant client
# In production/deployment, ensure QDRANT_URL and QDRANT_API_KEY are properly set
def get_qdrant_client() -> QdrantClient | None:
    if not settings.QDRANT_URL or not settings.QDRANT_API_KEY:
        print("Warning: Qdrant configuration missing. Vector search will be disabled.")
        return None

    return QdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY
    )

qdrant_client = get_qdrant_client()
COLLECTION_NAME = "radio_transcripts" # Example collection name

def search_radio_transcripts(query_embedding: list[float], limit: int = 5):
    """
    Searches for relevant team radio transcripts in Qdrant.

    Args:
        query_embedding (list[float]): The vector representation of the search query.
        limit (int): Maximum number of results to return.

    Returns:
        list[dict]: A list of relevant transcripts with their metadata.
    """
    if not qdrant_client:
        return [{"error": "Qdrant client is not configured."}]

    try:
        search_results = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            limit=limit
        )

        # Extract payload/metadata from results
        results = []
        for point in search_results:
            results.append(point.payload)

        return results
    except Exception as e:
        return [{"error": f"Failed to search Qdrant: {str(e)}"}]
