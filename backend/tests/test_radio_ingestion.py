import asyncio
import pytest
from unittest.mock import patch, AsyncMock
from app.ingestion.radio_ingestion import RadioIngestionPipeline

def test_radio_ingestion_pipeline():
    mock_radio = [
        {"driver_number": 1, "date": "2023-09-03T13:15:00Z", "transcript": "Radio check"}
    ]
    mock_race_control = []
    mock_drivers = [{"driver_number": 1, "name_acronym": "VER", "team_name": "Red Bull Racing"}]
    mock_laps = [{"driver_number": 1, "lap_number": 1, "date_start": "2023-09-03T13:14:50Z"}]

    with patch("app.services.openf1_service.OpenF1Service.get_team_radio", return_value=mock_radio), \
         patch("app.services.openf1_service.OpenF1Service.get_race_control", return_value=mock_race_control), \
         patch("app.services.openf1_service.OpenF1Service.get_drivers", return_value=mock_drivers), \
         patch("app.services.openf1_service.OpenF1Service.get_laps", return_value=mock_laps), \
         patch("app.ingestion.radio_ingestion.generate_embeddings_batch_async", new_callable=AsyncMock) as mock_embed:

        mock_embed.return_value = [[0.1] * 384]

        mock_qdrant_client = AsyncMock()

        pipeline = RadioIngestionPipeline(qdrant_client=mock_qdrant_client)
        result = asyncio.run(pipeline.ingest_session(year=2023, grand_prix="Monza", session_type="R"))

        assert result["status"] == "success"
        assert result["processed_count"] == 1
        mock_embed.assert_called_once_with(["Radio check"])
