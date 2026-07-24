import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from app.services.f1_service import get_telemetry, prewarm_session_cache, clear_telemetry_memory_cache

def test_telemetry_timeseries_extraction():
    clear_telemetry_memory_cache()
    mock_session = MagicMock()
    mock_laps = MagicMock()

    # Create mock fastest lap telemetry DataFrame
    telemetry_df = pd.DataFrame({
        'Time': [pd.Timedelta(seconds=0), pd.Timedelta(seconds=1), pd.Timedelta(seconds=2)],
        'Distance': [0.0, 50.0, 100.0],
        'Speed': [200.0, 310.0, 150.0],
        'Throttle': [100.0, 100.0, 0.0],
        'Brake': [False, False, True],
        'nGear': [6, 7, 4],
        'DRS': [0, 12, 0],
        'RPM': [11000, 12000, 9500]
    })

    fastest_lap = pd.Series({
        'LapNumber': 15,
        'LapTime': pd.Timedelta(seconds=85.432)
    })
    fastest_lap.get_telemetry = MagicMock(return_value=telemetry_df)

    laps_df = pd.DataFrame({
        'LapNumber': [1, 15],
        'LapTime': [pd.Timedelta(seconds=86.1), pd.Timedelta(seconds=85.432)]
    })

    mock_driver_laps = MagicMock()
    mock_driver_laps.empty = False
    mock_driver_laps.pick_fastest.return_value = fastest_lap
    mock_driver_laps.__getitem__.side_effect = lambda key: laps_df[key]

    mock_session.laps.pick_drivers.return_value = mock_driver_laps
    mock_session.laps.pick_driver.return_value = mock_driver_laps

    with patch("fastf1.get_session", return_value=mock_session):
        data = get_telemetry(2023, "Monza", "R", "VER")

        assert data["driver"] == "VER"
        assert data["fastest_lap_number"] == 15
        assert data["fastest_lap_time_seconds"] == 85.432
        assert data["max_speed_kph"] == 310.0
        assert data["avg_throttle_percentage"] == 66.67
        assert data["braking_zones_count"] == 1

        stream = data["telemetry_stream"]
        assert stream["speed_kph"] == [200.0, 310.0, 150.0]
        assert stream["brake"] == [False, False, True]
        assert stream["gear"] == [6, 7, 4]

def test_prewarm_session_cache():
    mock_session = MagicMock()
    with patch("fastf1.get_session", return_value=mock_session):
        prewarm_session_cache(2023, "Monza", "R")
        mock_session.load.assert_called_once_with(telemetry=True, weather=False, messages=False)
