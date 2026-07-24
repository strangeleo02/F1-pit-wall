import pytest
from app.services.tyre_service import calculate_tyre_degradation

def test_calculate_tyre_degradation_medium():
    res = calculate_tyre_degradation(compound="MEDIUM", stint_laps=20, base_lap_time=90.0, track_temp_celsius=38.0)
    assert res["compound"] == "MEDIUM"
    assert res["stint_laps"] == 20
    assert len(res["lap_predictions"]) == 20
    assert res["lap_predictions"][0]["stint_lap"] == 1
    # Check that linear tyre wear increases from lap 1 to lap 20
    assert res["lap_predictions"][19]["linear_wear_sec"] > 0.5

def test_calculate_tyre_degradation_soft_cliff():
    res = calculate_tyre_degradation(compound="SOFT", stint_laps=20, base_lap_time=90.0, track_temp_celsius=42.0)
    assert res["compound"] == "SOFT"
    assert res["cliff_threshold_lap"] > 0
    # Post-cliff lap should have cliff wear penalty > 0
    assert res["lap_predictions"][18]["cliff_wear_sec"] > 0.0
