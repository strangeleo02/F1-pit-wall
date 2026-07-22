import pytest
from unittest.mock import patch, MagicMock
from app.services.embedding_service import generate_embedding

@patch('app.services.embedding_service.get_embedding_model')
def test_generate_embedding(mock_get_embedding_model):
    mock_model = MagicMock()
    mock_get_embedding_model.return_value = mock_model

    mock_encoded = MagicMock()
    mock_encoded.tolist.return_value = [0.1, 0.2, 0.3]
    mock_model.encode.return_value = mock_encoded

    embedding = generate_embedding("Test transcript")

    assert embedding == [0.1, 0.2, 0.3]
    mock_model.encode.assert_called_once_with("Test transcript")
