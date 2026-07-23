import asyncio
from unittest.mock import patch, MagicMock
from app.services.embedding_service import generate_embedding, generate_embedding_async, generate_embeddings_batch, generate_embeddings_batch_async

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

@patch('app.services.embedding_service.get_embedding_model')
def test_generate_embedding_async(mock_get_embedding_model):
    mock_model = MagicMock()
    mock_get_embedding_model.return_value = mock_model

    mock_encoded = MagicMock()
    mock_encoded.tolist.return_value = [0.1, 0.2, 0.3]
    mock_model.encode.return_value = mock_encoded

    embedding = asyncio.run(generate_embedding_async("Test transcript"))

    assert embedding == [0.1, 0.2, 0.3]

@patch('app.services.embedding_service.get_embedding_model')
def test_generate_embeddings_batch(mock_get_embedding_model):
    mock_model = MagicMock()
    mock_get_embedding_model.return_value = mock_model

    mock_emb1 = MagicMock()
    mock_emb1.tolist.return_value = [0.1, 0.2]
    mock_emb2 = MagicMock()
    mock_emb2.tolist.return_value = [0.3, 0.4]
    mock_model.encode.return_value = [mock_emb1, mock_emb2]

    results = generate_embeddings_batch(["text1", "text2"])
    assert results == [[0.1, 0.2], [0.3, 0.4]]
