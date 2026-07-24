from typing import Any, Optional
from fastapi.concurrency import run_in_threadpool
from app.services.tyre_service import calculate_tyre_degradation, get_circuit_tyre_profile

def simulate_undercut_overcut(
    target_driver: str = "VER",
    rival_driver: str = "HAM",
    current_lap: int = 15,
    target_pit_lap: int = 18,
    initial_gap_sec: float = 1.8,
    stationary_pit_duration: float = 2.4,
    pit_lane_loss_sec: Optional[float] = None,
    target_current_tyre: str = "MEDIUM",
    target_new_tyre: str = "HARD",
    rival_current_tyre: str = "MEDIUM",
    target_tyre_age: int = 15,
    rival_tyre_age: int = 15,
    base_lap_time: float = 90.0,
    track_temp_celsius: float = 38.0,
    grand_prix: str = "monza"
) -> dict[str, Any]:
    """
    Simulates Undercut vs Overcut strategic battle between Target Driver and Rival Driver,
    dynamically calibrated to the real circuit pit lane loss and track asphalt degradation.
    """
    circuit_profile = get_circuit_tyre_profile(grand_prix)
    effective_pit_loss = pit_lane_loss_sec if pit_lane_loss_sec is not None else circuit_profile["pit_loss_sec"]
    total_pit_loss = effective_pit_loss + stationary_pit_duration

    # Compute degradation profiles for current and new tyres on this track
    target_curr_deg = calculate_tyre_degradation(target_current_tyre, 10, base_lap_time, track_temp_celsius, grand_prix)
    target_new_deg = calculate_tyre_degradation(target_new_tyre, 10, base_lap_time, track_temp_celsius, grand_prix)
    rival_curr_deg = calculate_tyre_degradation(rival_current_tyre, 10, base_lap_time, track_temp_celsius, grand_prix)

    # Calculate pace for target in-lap
    target_in_lap_age = target_tyre_age + (target_pit_lap - current_lap)
    target_in_lap_time = base_lap_time + (target_curr_deg["adjusted_deg_rate_per_lap"] * target_in_lap_age) + 0.35

    # Target out-lap time on fresh tyres (cold tyre warming penalty +0.8s)
    target_out_lap_time = base_lap_time + target_new_deg["base_compound_delta"] + 0.80

    # Rival pace staying out on old tyres
    rival_stay_out_lap_age = rival_tyre_age + (target_pit_lap - current_lap)
    rival_stay_out_pace = base_lap_time + (rival_curr_deg["adjusted_deg_rate_per_lap"] * rival_stay_out_lap_age)

    # Fresh tyre delta advantage on out-lap vs rival old tyre
    fresh_tyre_advantage_sec = round(rival_stay_out_pace - target_out_lap_time, 3)

    # Net pit window calculation
    net_undercut_gain = round(fresh_tyre_advantage_sec * 1.6 - (stationary_pit_duration - 2.5), 3)
    projected_gap_after_pits = round(initial_gap_sec - net_undercut_gain, 3)

    is_successful_undercut = projected_gap_after_pits < 0.0

    # Generate optimal pit window recommendations
    recommended_window = []
    for lap_offset in range(-2, 4):
        p_lap = target_pit_lap + lap_offset
        if p_lap > current_lap:
            prob = min(98.0, max(5.0, 75.0 + (net_undercut_gain * 12.0) - (lap_offset * 8.0)))
            recommended_window.append({
                "pit_lap": p_lap,
                "undercut_probability_pct": round(prob, 1),
                "is_optimal": lap_offset == 0
            })

    return {
        "target_driver": target_driver,
        "rival_driver": rival_driver,
        "grand_prix": grand_prix,
        "circuit_profile": circuit_profile,
        "current_lap": current_lap,
        "target_pit_lap": target_pit_lap,
        "initial_gap_sec": initial_gap_sec,
        "stationary_pit_duration": stationary_pit_duration,
        "total_pit_loss_sec": round(total_pit_loss, 3),
        "target_out_lap_time_sec": round(target_out_lap_time, 3),
        "fresh_tyre_advantage_per_lap_sec": fresh_tyre_advantage_sec,
        "net_undercut_gain_sec": net_undercut_gain,
        "projected_gap_after_pits_sec": projected_gap_after_pits,
        "is_successful_undercut": is_successful_undercut,
        "outcome_summary": (
            f"UNDERCUT SUCCESS ({grand_prix}): {target_driver} projects to emerge -{abs(projected_gap_after_pits):.2f}s ahead of {rival_driver}"
            if is_successful_undercut else
            f"OVERCUT RISK ({grand_prix}): {target_driver} projects to emerge +{projected_gap_after_pits:.2f}s behind {rival_driver}"
        ),
        "pit_window_recommendations": recommended_window
    }

async def simulate_undercut_overcut_async(**kwargs) -> dict[str, Any]:
    """Asynchronously runs undercut simulation."""
    return await run_in_threadpool(simulate_undercut_overcut, **kwargs)
