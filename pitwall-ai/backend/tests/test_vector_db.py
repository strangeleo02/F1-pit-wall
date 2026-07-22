import pytest
from unittest.mock import patch, MagicMock
from app.services.vector_db import search_radio_transcripts

@patch('app.services.vector_db.qdrant_client')
def test_search_radio_transcripts_success(mock_qdrant_client):
    mock_point1 = MagicMock()
    mock_point1.payload = {"text": "Push now"}
    mock_point2 = MagicMock()
    mock_point2.payload = {"text": "Box this lap"}

    mock_qdrant_client.search.return_value = [mock_point1, mock_point2]

    results = search_radio_transcripts([0.1, 0.2], limit=2)

    assert len(results) == 2
    assert results[0]["text"] == "Push now"
    assert results[1]["text"] == "Box this lap"
    mock_qdrant_client.search.assert_called_once()

@patch('app.services.vector_db.qdrant_client', None)
def test_search_radio_transcripts_no_client():
    results = search_radio_transcripts([0.1, 0.2])

    assert len(results) == 1
    assert "error" in results[0]
    assert "not configured" in results[0]["error"]

@patch('app.services.vector_db.qdrant_client')
def test_search_radio_transcripts_exception(mock_qdrant_client):
    mock_qdrant_client.search.side_effect = Exception("DB error")

    results = search_radio_transcripts([0.1, 0.2])

    assert len(results) == 1
    assert "error" in results[0]
    assert "Failed to search Qdrant" in results[0]["error"]
