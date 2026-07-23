import pytest
from unittest.mock import patch, MagicMock
from app.services.openf1_service import OpenF1Service

def test_normalize_transcripts():
    radio_raw = [
        {
            "driver_number": 1,
            "date": "2023-09-03T13:15:00.000Z",
            "transcript": "Tires are starting to feel a bit hot."
        }
    ]
    race_control_raw = [
        {
            "driver_number": 44,
            "date": "2023-09-03T13:16:00.000Z",
            "category": "Flag",
            "flag": "YELLOW",
            "message": "Yellow flag in sector 2",
            "lap_number": 12
        }
    ]
    drivers_raw = [
        {"driver_number": 1, "name_acronym": "VER", "team_name": "Red Bull Racing"},
        {"driver_number": 44, "name_acronym": "HAM", "team_name": "Mercedes"}
    ]
    laps_raw = [
        {"driver_number": 1, "lap_number": 10, "date_start": "2023-09-03T13:14:30.000Z"}
    ]
    session_meta = {"year": 2023, "grand_prix": "Monza", "session_type": "R"}

    normalized = OpenF1Service.normalize_transcripts(
        radio_data=radio_raw,
        race_control_data=race_control_raw,
        drivers_data=drivers_raw,
        laps_data=laps_raw,
        session_meta=session_meta
    )

    assert len(normalized) == 2

    # Check team radio entry
    radio_entry = next(item for item in normalized if item["source"] == "team_radio")
    assert radio_entry["driver"] == "VER"
    assert radio_entry["team"] == "Red Bull Racing"
    assert radio_entry["transcript_text"] == "Tires are starting to feel a bit hot."
    assert radio_entry["lap_start"] == 10

    # Check race control entry
    rc_entry = next(item for item in normalized if item["source"] == "race_control")
    assert rc_entry["driver"] == "HAM"
    assert rc_entry["team"] == "Mercedes"
    assert rc_entry["lap_start"] == 12
    assert "[FLAG - YELLOW] Yellow flag in sector 2" in rc_entry["transcript_text"]

@patch("httpx.Client.get")
def test_openf1_service_api_fetch(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = [{"driver_number": 1, "name_acronym": "VER"}]
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    drivers = OpenF1Service.get_drivers(session_key=9158)
    assert len(drivers) == 1
    assert drivers[0]["name_acronym"] == "VER"
