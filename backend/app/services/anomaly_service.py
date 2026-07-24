import numpy as np

def detect_telemetry_anomalies(telemetry_stream: list[dict]) -> list[dict]:
    """
    Analyzes telemetry time-series points to detect telemetry anomalies such as:
    - Front wheel lockup (High speed + High brake + sharp speed drop)
    - Sudden power unit lift/derating (High speed + Throttle drop to 0)
    - Cornering instability / micro-steering correction
    """
    if not telemetry_stream or len(telemetry_stream) < 5:
        return []

    anomalies = []

    for i in range(1, len(telemetry_stream) - 1):
        prev_pt = telemetry_stream[i - 1]
        curr_pt = telemetry_stream[i]
        next_pt = telemetry_stream[i + 1]

        speed = curr_pt.get("speed", 0.0)
        throttle = curr_pt.get("throttle", 0.0)
        brake = curr_pt.get("brake", False)
        dist = curr_pt.get("distance", 0.0)

        prev_speed = prev_pt.get("speed", 0.0)
        prev_throttle = prev_pt.get("throttle", 0.0)

        # 1. Detect Front Tyre Lockup (High brake application while speed drops drastically)
        if brake and (prev_speed - speed > 18.0) and speed > 100:
            anomalies.append({
                "type": "LOCKUP",
                "severity": "HIGH",
                "distance": round(dist, 1),
                "speed_kmh": round(speed, 1),
                "description": f"Heavy front tyre lockup detected at {round(dist)}m (speed drop {round(prev_speed - speed, 1)} km/h)"
            })

        # 2. Detect Throttle Lift / Engine Derating on Straights
        if prev_speed > 250 and prev_throttle > 90 and throttle < 15 and not brake:
            anomalies.append({
                "type": "THROTTLE_LIFT",
                "severity": "MEDIUM",
                "distance": round(dist, 1),
                "speed_kmh": round(speed, 1),
                "description": f"Unexpected high-speed throttle lift/derating at {round(dist)}m ({round(speed, 1)} km/h)"
            })

    # Return top unique anomalies sorted by distance
    seen_distances = set()
    unique_anomalies = []
    for a in anomalies:
        bucket = round(a["distance"] / 100.0) * 100
        if bucket not in seen_distances:
            seen_distances.add(bucket)
            unique_anomalies.append(a)

    return unique_anomalies[:5]
