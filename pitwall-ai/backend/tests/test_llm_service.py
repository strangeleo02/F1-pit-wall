import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.llm_service import generate_strategy_insight
from app.exceptions import LLMGenerationError

def test_generate_strategy_insight_success():
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Because his tires were degrading."
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response

    insight = asyncio.run(generate_strategy_insight(
        mock_client,
        "Why pit?",
        {"max_speed_kph": 300},
        [{"text": "Tires are gone"}]
    ))

    assert insight == "Because his tires were degrading."
    mock_client.chat.completions.create.assert_called_once()

def test_generate_strategy_insight_no_client():
    with pytest.raises(LLMGenerationError) as exc_info:
        asyncio.run(generate_strategy_insight(None, "query", {}, []))
    assert "not configured" in str(exc_info.value)

def test_generate_strategy_insight_exception():
    mock_client = AsyncMock()
    mock_client.chat.completions.create.side_effect = Exception("API limit reached")

    with pytest.raises(LLMGenerationError) as exc_info:
        asyncio.run(generate_strategy_insight(mock_client, "query", {}, []))

    assert "Failed to generate insight" in str(exc_info.value)
