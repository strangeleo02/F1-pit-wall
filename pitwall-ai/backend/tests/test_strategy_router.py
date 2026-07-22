import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@patch('app.routers.strategy.get_telemetry')
@patch('app.routers.strategy.generate_embedding')
@patch('app.routers.strategy.search_radio_transcripts')
@patch('app.routers.strategy.generate_strategy_insight')
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

@patch('app.routers.strategy.get_telemetry')
def test_query_strategy_telemetry_error(mock_get_telemetry):
    mock_get_telemetry.return_value = {"error": "Telemetry not found"}

    payload = {
        "year": 2023,
        "grand_prix": "Monza",
        "session_type": "R",
        "driver_code": "VER",
        "query": "Strategy?"
    }

    response = client.post("/api/v1/strategy/query", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "Telemetry not found"
