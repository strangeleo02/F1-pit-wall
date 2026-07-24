import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app
from app.exceptions import TelemetryNotFoundError

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@patch('app.routers.strategy.get_telemetry_async', new_callable=AsyncMock)
@patch('app.routers.strategy.generate_embedding_async', new_callable=AsyncMock)
@patch('app.routers.strategy.search_radio_transcripts', new_callable=AsyncMock)
@patch('app.routers.strategy.generate_strategy_insight', new_callable=AsyncMock)
def test_query_strategy_success(
    mock_generate_insight,
    mock_search_radio,
    mock_generate_embedding,
    mock_get_telemetry
):
    mock_get_telemetry.return_value = {"driver": "VER", "max_speed_kph": 320.5}
    mock_generate_embedding.return_value = [0.1, 0.2]
    mock_search_radio.return_value = [{"text": "Push"}]
    mock_generate_insight.return_value = "Box next lap."

    payload = {
        "year": 2023,
        "grand_prix": "Monza",
        "session_type": "R",
        "driver_code": "VER",
        "query": "Strategy?"
    }

    response = client.post("/api/v1/strategy/query", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["insight"] == "Box next lap."
    assert data["telemetry"]["driver"] == "VER"
    assert data["radio_transcripts"][0]["text"] == "Push"

@patch('app.routers.strategy.get_telemetry_async', new_callable=AsyncMock)
def test_query_strategy_telemetry_not_found(mock_get_telemetry):
    mock_get_telemetry.side_effect = TelemetryNotFoundError("No laps found for VER")

    payload = {
        "year": 2023,
        "grand_prix": "Monza",
        "session_type": "R",
        "driver_code": "VER",
        "query": "Strategy?"
    }

    response = client.post("/api/v1/strategy/query", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "No laps found for VER"

def test_query_strategy_validation_error():
    payload = {
        "year": 1800,  # invalid year < 1950
        "grand_prix": "Monza",
        "session_type": "INVALID",  # invalid session
        "driver_code": "VERSTAPPEN",  # invalid len > 3
        "query": ""
    }

    response = client.post("/api/v1/strategy/query", json=payload)
    assert response.status_code == 422

@patch('app.routers.strategy.get_telemetry_async', new_callable=AsyncMock)
@patch('app.routers.strategy.generate_embedding_async', new_callable=AsyncMock)
@patch('app.routers.strategy.search_radio_transcripts', new_callable=AsyncMock)
@patch('app.routers.strategy.stream_strategy_insight')
def test_stream_strategy_endpoint(
    mock_stream_insight,
    mock_search_radio,
    mock_generate_embedding,
    mock_get_telemetry
):
    mock_get_telemetry.return_value = {"driver": "VER", "max_speed_kph": 320.5}
    mock_generate_embedding.return_value = [0.1, 0.2]
    mock_search_radio.return_value = [{"text": "Push"}]

    async def mock_tokens(*args, **kwargs):
        yield "Box "
        yield "now."

    mock_stream_insight.side_effect = mock_tokens

    payload = {
        "year": 2023,
        "grand_prix": "Monza",
        "session_type": "R",
        "driver_code": "VER",
        "query": "Strategy?"
    }

    response = client.post("/api/v1/strategy/stream", json=payload)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    body = response.text
    assert "data: {" in body
    assert "[DONE]" in body

