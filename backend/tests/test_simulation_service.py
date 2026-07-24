import pytest
from app.services.simulation_service import simulate_undercut_overcut

def test_simulate_undercut_overcut_success():
    res = simulate_undercut_overcut(
        target_driver="VER",
        rival_driver="HAM",
        current_lap=15,
        target_pit_lap=18,
        initial_gap_sec=1.2,
        stationary_pit_duration=2.2,
        target_current_tyre="MEDIUM",
        target_new_tyre="HARD"
    )
    assert res["target_driver"] == "VER"
    assert res["rival_driver"] == "HAM"
    assert "outcome_summary" in res
    assert len(res["pit_window_recommendations"]) > 0

def test_simulate_undercut_overcut_overcut_risk():
    res = simulate_undercut_overcut(
        target_driver="VER",
        rival_driver="HAM",
        current_lap=15,
        target_pit_lap=18,
        initial_gap_sec=15.0, # Huge gap trailing rival
        stationary_pit_duration=4.5
    )
    assert res["is_successful_undercut"] == False
    assert res["projected_gap_after_pits_sec"] > 0
