from app.services.anomaly_service import detect_telemetry_anomalies

def test_detect_telemetry_anomalies_lockup():
    telemetry_stream = [
        {"distance": 100, "speed": 310.0, "throttle": 100, "brake": False},
        {"distance": 120, "speed": 310.0, "throttle": 100, "brake": False},
        {"distance": 140, "speed": 280.0, "throttle": 0, "brake": True},
        {"distance": 160, "speed": 250.0, "throttle": 0, "brake": True}, # 30kmh drop
        {"distance": 180, "speed": 220.0, "throttle": 0, "brake": True},
    ]

    anomalies = detect_telemetry_anomalies(telemetry_stream)
    assert len(anomalies) > 0
    assert any(a["type"] == "LOCKUP" for a in anomalies)
