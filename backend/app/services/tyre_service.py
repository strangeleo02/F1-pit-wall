from typing import Any, Optional
from fastapi.concurrency import run_in_threadpool

# Official Circuit Total Race Laps Database
CIRCUIT_TOTAL_LAPS_DATABASE: dict[str, int] = {
    "monza": 53,
    "monaco": 78,
    "spa": 44,
    "silverstone": 52,
    "bahrain": 57,
    "sakhir": 57,
    "baku": 51,
    "singapore": 62,
    "suzuka": 53,
    "austin": 56,
    "cota": 56,
    "melbourne": 58,
    "interlagos": 71,
    "zandvoort": 72,
    "austria": 71,
    "spielberg": 71,
    "barcelona": 66,
    "hungaroring": 70,
    "las vegas": 50,
    "miami": 57,
    "jeddah": 50,
    "qatar": 57,
    "lusail": 57,
    "shanghai": 56,
    "imola": 63,
    "mexico": 71,
    "abu dhabi": 58
}

# Curated Circuit Tyre Severity & Pit Lane Loss Database
CIRCUIT_TYRE_SEVERITY_DATABASE: dict[str, dict] = {
    "bahrain": {"abrasion_factor": 1.40, "pit_loss_sec": 22.5, "severity": "HIGH_ABRASION", "total_laps": 57},
    "sakhir": {"abrasion_factor": 1.40, "pit_loss_sec": 22.5, "severity": "HIGH_ABRASION", "total_laps": 57},
    "monaco": {"abrasion_factor": 0.55, "pit_loss_sec": 19.0, "severity": "ULTRA_LOW_WEAR", "total_laps": 78},
    "monza": {"abrasion_factor": 0.85, "pit_loss_sec": 24.0, "severity": "MEDIUM_LOW_WEAR", "total_laps": 53},
    "silverstone": {"abrasion_factor": 1.30, "pit_loss_sec": 28.0, "severity": "HIGH_LATERAL_WEAR", "total_laps": 52},
    "spa": {"abrasion_factor": 1.25, "pit_loss_sec": 21.5, "severity": "HIGH_ENERGY_WEAR", "total_laps": 44},
    "baku": {"abrasion_factor": 0.65, "pit_loss_sec": 20.5, "severity": "LOW_STREET_WEAR", "total_laps": 51},
    "singapore": {"abrasion_factor": 1.15, "pit_loss_sec": 29.5, "severity": "HIGH_TRACTION_HEAT", "total_laps": 62},
    "suzuka": {"abrasion_factor": 1.35, "pit_loss_sec": 22.0, "severity": "HIGH_ABRASION", "total_laps": 53},
    "austin": {"abrasion_factor": 1.20, "pit_loss_sec": 20.0, "severity": "MEDIUM_HIGH_WEAR", "total_laps": 56},
    "cota": {"abrasion_factor": 1.20, "pit_loss_sec": 20.0, "severity": "MEDIUM_HIGH_WEAR", "total_laps": 56},
    "melbourne": {"abrasion_factor": 0.75, "pit_loss_sec": 21.0, "severity": "MEDIUM_LOW_WEAR", "total_laps": 58},
    "interlagos": {"abrasion_factor": 1.10, "pit_loss_sec": 21.0, "severity": "MEDIUM_WEAR", "total_laps": 71},
    "zandvoort": {"abrasion_factor": 1.25, "pit_loss_sec": 21.5, "severity": "HIGH_BANKING_WEAR", "total_laps": 72},
    "austria": {"abrasion_factor": 0.90, "pit_loss_sec": 19.5, "severity": "MEDIUM_WEAR", "total_laps": 71},
    "barcelona": {"abrasion_factor": 1.35, "pit_loss_sec": 22.0, "severity": "HIGH_FRONT_LEFT_WEAR", "total_laps": 66},
    "hungaroring": {"abrasion_factor": 1.10, "pit_loss_sec": 20.5, "severity": "MEDIUM_HIGH_WEAR", "total_laps": 70},
    "las vegas": {"abrasion_factor": 0.50, "pit_loss_sec": 21.5, "severity": "ULTRA_LOW_WEAR", "total_laps": 50},
    "miami": {"abrasion_factor": 0.80, "pit_loss_sec": 20.0, "severity": "MEDIUM_WEAR", "total_laps": 57},
    "jeddah": {"abrasion_factor": 0.70, "pit_loss_sec": 20.5, "severity": "MEDIUM_LOW_WEAR", "total_laps": 50},
    "qatar": {"abrasion_factor": 1.45, "pit_loss_sec": 24.5, "severity": "EXTREME_KERB_WEAR", "total_laps": 57},
    "lusail": {"abrasion_factor": 1.45, "pit_loss_sec": 24.5, "severity": "EXTREME_KERB_WEAR", "total_laps": 57}
}

# Base pace deltas (seconds relative to Medium compound baseline)
COMPOUND_BASE_DELTAS: dict[str, float] = {
    "SOFT": -0.55,
    "C5": -0.65,
    "C4": -0.55,
    "C3": -0.20,
    "MEDIUM": 0.00,
    "C2": 0.25,
    "HARD": 0.45,
    "C1": 0.55,
    "INTERMEDIATE": 4.50,
    "WET": 12.00
}

# Base degradation rates (seconds lost per lap per stint age)
COMPOUND_DEG_RATES: dict[str, float] = {
    "SOFT": 0.095,
    "C5": 0.110,
    "C4": 0.095,
    "C3": 0.075,
    "MEDIUM": 0.055,
    "C2": 0.045,
    "HARD": 0.035,
    "C1": 0.028,
    "INTERMEDIATE": 0.060,
    "WET": 0.040
}

# Baseline cliff lap ages where exponential thermal degradation triggers
COMPOUND_CLIFF_LAPS: dict[str, int] = {
    "SOFT": 14,
    "C5": 12,
    "C4": 14,
    "C3": 18,
    "MEDIUM": 24,
    "C2": 28,
    "HARD": 34,
    "C1": 40,
    "INTERMEDIATE": 22,
    "WET": 30
}

def get_circuit_tyre_profile(grand_prix: str) -> dict[str, Any]:
    """Returns circuit-specific tyre abrasion factor, pit loss time, total race laps, and severity profile."""
    gp_key = grand_prix.lower().replace(" grand prix", "").replace("gp", "").strip()
    total_laps = CIRCUIT_TOTAL_LAPS_DATABASE.get(gp_key, 57)

    profile = CIRCUIT_TYRE_SEVERITY_DATABASE.get(gp_key, {
        "abrasion_factor": 1.0,
        "pit_loss_sec": 21.5,
        "severity": "MEDIUM_STANDARD_WEAR",
        "total_laps": total_laps
    })
    for k, v in CIRCUIT_TYRE_SEVERITY_DATABASE.items():
        if k in gp_key:
            return {**v, "circuit_key": gp_key, "total_laps": v.get("total_laps", total_laps)}
    return {**profile, "circuit_key": gp_key, "total_laps": total_laps}

def calculate_tyre_degradation(
    compound: str = "MEDIUM",
    stint_laps: int = 25,
    base_lap_time: float = 90.0,
    track_temp_celsius: float = 38.0,
    grand_prix: str = "monza"
) -> dict[str, Any]:
    """
    Computes track-specific lap-by-lap pace degradation curves for Pirelli compounds.
    Adjusts degradation rates & thermal cliff thresholds dynamically based on real circuit asphalt abrasion and total race distance.
    """
    compound_upper = compound.upper().strip()
    circuit_profile = get_circuit_tyre_profile(grand_prix)
    abrasion_factor = circuit_profile["abrasion_factor"]

    base_delta = COMPOUND_BASE_DELTAS.get(compound_upper, 0.0)
    base_deg = COMPOUND_DEG_RATES.get(compound_upper, 0.055)
    
    # Scale cliff lap inversely with circuit abrasion (high abrasion = earlier cliff)
    base_cliff_lap = COMPOUND_CLIFF_LAPS.get(compound_upper, 22)
    cliff_lap = max(6, int(base_cliff_lap / max(0.5, (abrasion_factor ** 0.8))))

    # Track temp degradation factor: +1.5% wear rate for every degree above 35°C
    temp_penalty_factor = 1.0 + max(0.0, (track_temp_celsius - 35.0) * 0.015)
    adjusted_deg_rate = base_deg * temp_penalty_factor * abrasion_factor

    lap_predictions = []
    total_stint_time = 0.0

    for lap in range(1, stint_laps + 1):
        lap_pace = base_lap_time + base_delta
        linear_wear = (lap - 1) * adjusted_deg_rate

        cliff_wear = 0.0
        if lap > cliff_lap:
            excess = lap - cliff_lap
            cliff_wear = 0.14 * (excess ** 1.85)

        fuel_gain = (lap - 1) * 0.060

        net_lap_time = round(lap_pace + linear_wear + cliff_wear - fuel_gain, 3)
        lap_delta_to_fresh = round(net_lap_time - (base_lap_time + base_delta), 3)
        health_pct = max(0, min(100, int(100.0 - ((linear_wear + cliff_wear * 2.0) / 3.0) * 100.0)))

        lap_predictions.append({
            "stint_lap": lap,
            "predicted_lap_time": net_lap_time,
            "delta_from_fresh": lap_delta_to_fresh,
            "linear_wear_sec": round(linear_wear, 3),
            "cliff_wear_sec": round(cliff_wear, 3),
            "fuel_gain_sec": round(fuel_gain, 3),
            "tyre_health_pct": health_pct
        })

        total_stint_time += net_lap_time

    avg_lap_time = round(total_stint_time / max(1, stint_laps), 3)

    # Multi-compound side-by-side comparison array (SOFT, MEDIUM, HARD) scaled to circuit
    multi_comparison = []
    for lap in range(1, stint_laps + 1):
        row: dict[str, Any] = {"stint_lap": lap}
        for comp in ["SOFT", "MEDIUM", "HARD"]:
            c_delta = COMPOUND_BASE_DELTAS[comp]
            c_deg = COMPOUND_DEG_RATES[comp] * temp_penalty_factor * abrasion_factor
            c_cliff = max(6, int(COMPOUND_CLIFF_LAPS[comp] / max(0.5, (abrasion_factor ** 0.8))))

            lin = (lap - 1) * c_deg
            clf = 0.14 * ((lap - c_cliff) ** 1.85) if lap > c_cliff else 0.0
            fuel_g = (lap - 1) * 0.060

            lap_t = round(base_lap_time + c_delta + lin + clf - fuel_g, 3)
            health = max(0, min(100, int(100.0 - ((lin + clf * 2.0) / 3.0) * 100.0)))

            row[f"{comp}_pace"] = lap_t
            row[f"{comp}_health"] = health
            row[f"{comp}_deg"] = round(lin + clf, 3)

        multi_comparison.append(row)

    return {
        "compound": compound_upper,
        "grand_prix": grand_prix,
        "circuit_profile": circuit_profile,
        "stint_laps": stint_laps,
        "base_lap_time": base_lap_time,
        "track_temp_celsius": track_temp_celsius,
        "base_compound_delta": base_delta,
        "adjusted_deg_rate_per_lap": round(adjusted_deg_rate, 4),
        "cliff_threshold_lap": cliff_lap,
        "total_stint_time_sec": round(total_stint_time, 3),
        "average_lap_time_sec": avg_lap_time,
        "lap_predictions": lap_predictions,
        "multi_compound_comparison": multi_comparison
    }

async def calculate_tyre_degradation_async(
    compound: str = "MEDIUM",
    stint_laps: int = 25,
    base_lap_time: float = 90.0,
    track_temp_celsius: float = 38.0,
    grand_prix: str = "monza"
) -> dict[str, Any]:
    """Asynchronously calculates track-specific tyre degradation curve."""
    return await run_in_threadpool(
        calculate_tyre_degradation, compound, stint_laps, base_lap_time, track_temp_celsius, grand_prix
    )
