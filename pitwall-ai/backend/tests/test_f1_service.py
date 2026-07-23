import pytest
from unittest.mock import patch, MagicMock
from app.services.f1_service import get_telemetry, get_telemetry_async, clear_telemetry_memory_cache
from app.exceptions import TelemetryNotFoundError, TelemetryFetchError

@patch('app.services.f1_service.fastf1.get_session')
def test_get_telemetry_success(mock_get_session):
    clear_telemetry_memory_cache()
    mock_session = MagicMock()
    mock_laps = MagicMock()
    mock_driver_laps = MagicMock()
    mock_fastest_lap = MagicMock()
    mock_telemetry = MagicMock()

    mock_get_session.return_value = mock_session
    mock_session.laps = mock_laps
    mock_laps.pick_driver.return_value = mock_driver_laps

    type(mock_driver_laps).empty = False

    mock_driver_laps.pick_fastest.return_value = mock_fastest_lap
    mock_fastest_lap.get_telemetry.return_value = mock_telemetry

    mock_speed = MagicMock()
    mock_speed.max.return_value = 320.5
    mock_telemetry.__getitem__.return_value = mock_speed
    type(mock_telemetry).empty = False

    mock_lap_time = MagicMock()
    mock_lap_time.total_seconds.return_value = 85.5

    def fastest_lap_getitem(key):
        if key == 'LapTime':
            return mock_lap_time
        return MagicMock()
    mock_fastest_lap.__getitem__.side_effect = fastest_lap_getitem

    mock_df = MagicMock()
    mock_df.dropna.return_value.to_dict.return_value = [{'LapNumber': 1, 'LapTime': mock_lap_time}]
    mock_driver_laps.__getitem__.return_value = mock_df

    result = get_telemetry(2023, 'Monza', 'R', 'VER')

    assert result['driver'] == 'VER'
    assert result['max_speed_kph'] == 320.5
    assert result['fastest_lap_time_seconds'] == 85.5
    assert len(result['laps']) == 1

@patch('app.services.f1_service.fastf1.get_session')
def test_get_telemetry_no_laps(mock_get_session):
    clear_telemetry_memory_cache()
    mock_session = MagicMock()
    mock_laps = MagicMock()
    mock_driver_laps = MagicMock()

    mock_get_session.return_value = mock_session
    mock_session.laps = mock_laps
    mock_laps.pick_driver.return_value = mock_driver_laps

    type(mock_driver_laps).empty = True

    with pytest.raises(TelemetryNotFoundError) as exc_info:
        get_telemetry(2023, 'Monza', 'R', 'VER')

    assert "No laps found" in str(exc_info.value)

@patch('app.services.f1_service.fastf1.get_session')
def test_get_telemetry_exception(mock_get_session):
    clear_telemetry_memory_cache()
    mock_get_session.side_effect = Exception("API failure")

    with pytest.raises(TelemetryFetchError) as exc_info:
        get_telemetry(2023, 'Monza', 'R', 'VER')

    assert "Failed to fetch telemetry" in str(exc_info.value)
