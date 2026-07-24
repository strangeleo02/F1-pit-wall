import pytest
from app.ingestion.fia_ingestion import ingest_fia_documents

@pytest.mark.asyncio
async def test_ingest_fia_documents(mocker):
    mock_client = mocker.AsyncMock()
    mock_client.get_collections.return_value.collections = []

    mock_model = mocker.Mock()
    mock_model.encode.return_value.tolist.return_value = [0.1] * 384
    mocker.patch("app.ingestion.fia_ingestion.get_embedding_model", return_value=mock_model)

    count = await ingest_fia_documents(mock_client)
    assert count == 3
    assert mock_client.upsert.called
