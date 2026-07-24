import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.llm_service import stream_strategy_insight

def test_stream_strategy_insight():
    mock_client = AsyncMock()
    mock_chunk1 = MagicMock()
    mock_chunk1.choices = [MagicMock(delta=MagicMock(content="Pit "))]
    mock_chunk2 = MagicMock()
    mock_chunk2.choices = [MagicMock(delta=MagicMock(content="now!"))]

    async def mock_generator():
        yield mock_chunk1
        yield mock_chunk2

    mock_client.chat.completions.create.return_value = mock_generator()

    async def run_test():
        collected = []
        async for token in stream_strategy_insight(mock_client, "System prompt", "User prompt"):
            collected.append(token)
        return "".join(collected)

    result = asyncio.run(run_test())
    assert result == "Pit now!"
