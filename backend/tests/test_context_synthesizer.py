import pytest
from app.services.context_synthesizer import ContextSynthesizer
from app.services.intent_router import QueryIntent

def test_detect_lap_anomalies():
    laps = [
        {"LapNumber": 1, "LapTime": 81.0},
        {"LapNumber": 2, "LapTime": 81.2},
        {"LapNumber": 3, "LapTime": 81.1},
        {"LapNumber": 4, "LapTime": 85.5},  # Spike
        {"LapNumber": 5, "LapTime": 80.5}   # Fastest
    ]

    anomalies = ContextSynthesizer.detect_lap_anomalies(laps, delta_threshold_sec=1.5)
    assert len(anomalies) >= 2

    spike = next(a for a in anomalies if a["type"] == "spike")
    assert spike["lap_number"] == 4

    fastest = next(a for a in anomalies if a["type"] == "fastest")
    assert fastest["lap_number"] == 5

def test_correlate_anomalies_with_transcripts():
    anomalies = [{"lap_number": 10, "type": "spike"}]
    transcripts = [
        {"driver": "VER", "lap_start": 10, "transcript_text": "Tires are dead"},
        {"driver": "HAM", "lap_start": 40, "transcript_text": "Copy"}
    ]

    correlated = ContextSynthesizer.correlate_anomalies_with_transcripts(anomalies, transcripts)
    assert correlated[0]["correlated_anomaly"] is True
    assert correlated[1]["correlated_anomaly"] is False

def test_synthesize_prompt():
    telemetry = {"driver": "VER", "max_speed_kph": 350.0}
    transcripts = [{"driver": "VER", "lap_start": 10, "transcript_text": "No grip"}]

    system_prompt, user_prompt = ContextSynthesizer.synthesize_prompt(
        query="Why no grip?",
        intent=QueryIntent.MULTI_MODAL_RAG,
        telemetry_data=telemetry,
        radio_transcripts=transcripts
    )

    assert "MULTI_MODAL_RAG" in user_prompt
    assert "No grip" in user_prompt
    assert "Telemetry Statistical Summary" in user_prompt
