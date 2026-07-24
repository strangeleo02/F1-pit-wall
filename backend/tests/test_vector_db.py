import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.vector_db import search_radio_transcripts, ensure_collection_exists, upsert_radio_transcripts
from app.exceptions import VectorDBUnavailableError

def test_search_radio_transcripts_success():
    mock_qdrant_client = AsyncMock()
    mock_point1 = MagicMock()
    mock_point1.payload = {"driver": "VER", "text": "Push now"}
    mock_point2 = MagicMock()
    mock_point2.payload = {"driver": "HAM", "text": "Box this lap"}

    mock_res = MagicMock()
    mock_res.points = [mock_point1, mock_point2]
    mock_qdrant_client.query_points.return_value = mock_res

    results = asyncio.run(search_radio_transcripts(mock_qdrant_client, [0.1, 0.2], limit=2, driver="VER"))

    assert len(results) == 2
    assert results[0]["driver"] == "VER"
    assert results[1]["driver"] == "HAM"

def test_search_radio_transcripts_no_client():
    with pytest.raises(VectorDBUnavailableError) as exc_info:
        asyncio.run(search_radio_transcripts(None, [0.1, 0.2]))

    assert "not configured" in str(exc_info.value)

def test_search_radio_transcripts_exception():
    mock_qdrant_client = AsyncMock()
    mock_qdrant_client.query_points.side_effect = Exception("DB error")
    mock_qdrant_client.search.side_effect = Exception("DB error")

    with pytest.raises(VectorDBUnavailableError) as exc_info:
        asyncio.run(search_radio_transcripts(mock_qdrant_client, [0.1, 0.2]))

    assert "Failed to search Qdrant" in str(exc_info.value)

def test_upsert_radio_transcripts_success():
    mock_qdrant_client = AsyncMock()
    mock_collections = MagicMock()
    mock_collections.collections = []
    mock_qdrant_client.get_collections.return_value = mock_collections

    transcripts = [{"driver": "VER", "transcript_text": "Push"}]
    embeddings = [[0.1] * 384]

    count = asyncio.run(upsert_radio_transcripts(mock_qdrant_client, transcripts, embeddings))
    assert count == 1
    mock_qdrant_client.upsert.assert_called_once()
