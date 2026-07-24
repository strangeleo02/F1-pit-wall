from fastapi import APIRouter, Query
from typing import Optional
from app.services.history_service import fetch_pitstops_async, fetch_standings_async

router = APIRouter(tags=["History"])

@router.get("/history/pitstops", summary="Get historical pit stop duration benchmarks")
async def get_pitstops(
    year: int = Query(2023, ge=1950, le=2026),
    round_num: Optional[int] = Query(None, ge=1, le=25)
):
    """
    Fetches historical pit stop durations and timestamps via Jolpica/Ergast API.
    """
    stops = await fetch_pitstops_async(year, round_num)
    return {"year": year, "round": round_num, "count": len(stops), "pitstops": stops}

@router.get("/history/standings", summary="Get World Championship standings")
async def get_standings(
    year: int = Query(2023, ge=1950, le=2026),
    category: str = Query("driver", pattern="^(driver|constructor)$")
):
    """
    Fetches historical Driver or Constructor Championship standings.
    """
    standings = await fetch_standings_async(year, category)
    return {"year": year, "category": category, "count": len(standings), "standings": standings}
