import pytest
from app.services.weather_service import calculate_weather_crossover

def test_calculate_weather_crossover_dry():
    res = calculate_weather_crossover(rainfall_mm_per_min=0.0, track_moisture_pct=5.0)
    assert res["recommended_compound"] == "DRY_SLICK"
    assert res["slick_usable"] == True

def test_calculate_weather_crossover_inter():
    res = calculate_weather_crossover(rainfall_mm_per_min=0.6, track_moisture_pct=30.0)
    assert res["recommended_compound"] == "INTERMEDIATE"
    assert res["crossover_state"] == "SLICK_TO_INTER_CROSSOVER"

def test_calculate_weather_crossover_wet():
    res = calculate_weather_crossover(rainfall_mm_per_min=2.5, track_moisture_pct=80.0)
    assert res["recommended_compound"] == "FULL_WET"
    assert res["full_wet_required"] == True
