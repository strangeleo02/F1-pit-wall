from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field

from app.services.tyre_service import calculate_tyre_degradation_async
from app.services.simulation_service import simulate_undercut_overcut_async
from app.services.weather_service import calculate_weather_crossover_async

router = APIRouter(prefix="/simulation", tags=["Strategy Simulation Engine"])

class UndercutSimulationRequest(BaseModel):
    target_driver: str = Field(default="VER", description="Target driver code")
    rival_driver: str = Field(default="HAM", description="Rival driver code")
    grand_prix: str = Field(default="monza", description="Grand Prix circuit key")
    current_lap: int = Field(default=15, ge=1, le=80)
    target_pit_lap: int = Field(default=18, ge=1, le=80)
    initial_gap_sec: float = Field(default=1.8, description="Gap to rival in seconds")
    stationary_pit_duration: float = Field(default=2.4, ge=1.0, le=15.0)
    pit_lane_loss_sec: Optional[float] = Field(default=None, description="Optional override for pit lane loss seconds")
    target_current_tyre: str = Field(default="MEDIUM")
    target_new_tyre: str = Field(default="HARD")
    rival_current_tyre: str = Field(default="MEDIUM")
    target_tyre_age: int = Field(default=15, ge=0)
    rival_tyre_age: int = Field(default=15, ge=0)
    base_lap_time: float = Field(default=90.0, ge=45.0)
    track_temp_celsius: float = Field(default=38.0, ge=10.0, le=60.0)

@router.post("/undercut")
async def run_undercut_simulation(req: UndercutSimulationRequest):
    """
    Simulates Undercut vs Overcut strategic battle calibrated to track asphalt abrasion & pit loss.
    """
    try:
        return await simulate_undercut_overcut_async(**req.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Undercut simulation error: {str(e)}")

@router.get("/tyre-deg")
async def get_tyre_degradation(
    compound: str = Query("MEDIUM", description="Pirelli compound: SOFT, MEDIUM, HARD, C1-C5, INTERMEDIATE, WET"),
    grand_prix: str = Query("monza", description="Grand Prix circuit key"),
    stint_laps: int = Query(25, ge=1, le=60),
    base_lap_time: float = Query(90.0, ge=45.0),
    track_temp_celsius: float = Query(38.0, ge=10.0, le=60.0)
):
    """
    Returns lap-by-lap track-calibrated tyre degradation wear curves for Pirelli compounds.
    """
    try:
        return await calculate_tyre_degradation_async(
            compound=compound,
            grand_prix=grand_prix,
            stint_laps=stint_laps,
            base_lap_time=base_lap_time,
            track_temp_celsius=track_temp_celsius
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tyre deg calculation error: {str(e)}")

@router.get("/crossover")
async def get_weather_crossover(
    rainfall_mm_per_min: float = Query(0.0, ge=0.0, le=50.0),
    track_moisture_pct: float = Query(0.0, ge=0.0, le=100.0),
    ambient_temp_celsius: float = Query(24.0, ge=-5.0, le=50.0),
    track_temp_celsius: float = Query(34.0, ge=0.0, le=70.0)
):
    """
    Returns dynamic compound crossover thresholds (Slick ↔ Intermediate ↔ Full Wet).
    """
    try:
        return await calculate_weather_crossover_async(
            rainfall_mm_per_min=rainfall_mm_per_min,
            track_moisture_pct=track_moisture_pct,
            ambient_temp_celsius=ambient_temp_celsius,
            track_temp_celsius=track_temp_celsius
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weather crossover error: {str(e)}")

@router.get("/session-weather")
async def get_session_weather_endpoint(
    year: int = Query(2024, ge=1950, le=2026),
    grand_prix: str = Query("Monza"),
    session_type: str = Query("Race")
):
    """
    Returns real historical session weather telemetry (TrackTemp, AirTemp, Humidity, Rainfall)
    and total race laps from FastF1 API for a specific Year & Grand Prix.
    """
    try:
        from app.services.f1_service import get_session_weather_and_laps_async
        return await get_session_weather_and_laps_async(year=year, grand_prix=grand_prix, session_type=session_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session weather fetch error: {str(e)}")
