import pytest
from unittest.mock import patch, MagicMock
from app.services.llm_service import generate_strategy_insight

@patch('app.services.llm_service.client')
def test_generate_strategy_insight_success(mock_client):
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Because his tires were degrading."
    mock_response.choices = [mock_choice]

    mock_client.chat.completions.create.return_value = mock_response

    insight = generate_strategy_insight(
        "Why pit?",
        {"max_speed_kph": 300},
        [{"text": "Tires are gone"}]
    )

    assert insight == "Because his tires were degrading."
    mock_client.chat.completions.create.assert_called_once()

@patch('app.services.llm_service.client', None)
def test_generate_strategy_insight_no_client():
    insight = generate_strategy_insight("query", {}, [])
    assert "not configured" in insight

@patch('app.services.llm_service.client')
def test_generate_strategy_insight_exception(mock_client):
    mock_client.chat.completions.create.side_effect = Exception("API limit reached")

    insight = generate_strategy_insight("query", {}, [])

    assert "Failed to generate insight" in insight
