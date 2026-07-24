from fastapi import APIRouter, Query, Depends
from qdrant_client import AsyncQdrantClient
from app.dependencies import get_qdrant_client
from app.services.f1_service import get_season_schedule_async, get_session_drivers_async

router = APIRouter(tags=["Metadata"])

@router.get("/meta/seasons", summary="Get supported F1 season years")
async def get_seasons():
    """
    Returns list of supported F1 season years.
    """
    return {"seasons": [2026, 2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018]}

@router.get("/meta/schedule", summary="Get official F1 calendar schedule for a season")
async def get_schedule(year: int = Query(2023, ge=2018, le=2026)):
    """
    Dynamically fetches the official F1 Grand Prix calendar schedule for the selected year.
    """
    events = await get_season_schedule_async(year)
    return {"year": year, "events": events}

@router.get("/meta/drivers", summary="Get participating driver lineup for a session")
async def get_drivers(
    year: int = Query(2023, ge=2018, le=2026),
    grand_prix: str = Query("Monza"),
    session_type: str = Query("R"),
    qdrant_client: AsyncQdrantClient | None = Depends(get_qdrant_client)
):
    """
    Dynamically fetches the actual driver lineup participating in a specific race session,
    using Qdrant vector collection caching.
    """
    drivers = await get_session_drivers_async(year, grand_prix, session_type, qdrant_client=qdrant_client)
    return {"year": year, "grand_prix": grand_prix, "session_type": session_type, "drivers": drivers}

@router.get("/meta/circuit", summary="Get track layout geometry and landmark turn annotations")
async def get_circuit(grand_prix: str = Query("Monza")):
    """
    Returns 2D vector geometry coordinates and landmark corner markers for the specified circuit.
    """
    from app.services.circuit_service import get_circuit_layout_async
    return await get_circuit_layout_async(grand_prix)

@router.get("/meta/weather", summary="Get session weather metrics")
async def get_weather(
    year: int = Query(2023, ge=2018, le=2026),
    grand_prix: str = Query("Monza"),
    session_type: str = Query("R")
):
    """
    Returns real or ambient session weather data (track temp, air temp, humidity, rainfall).
    """
    from app.services.weather_service import get_session_weather_async
    return await get_session_weather_async(year, grand_prix, session_type)


