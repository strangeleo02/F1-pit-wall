import pytest
from app.services.circuit_service import get_circuit_layout, _GEOJSON_CACHE

def test_get_circuit_layout_monza(mocker):
    _GEOJSON_CACHE.clear()
    mock_res = mocker.Mock()
    mock_res.status_code = 200
    mock_res.json.return_value = {
        "features": [
            {
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[9.281, 45.618], [9.285, 45.620], [9.290, 45.625]]
                }
            }
        ]
    }
    mocker.patch("httpx.Client.get", return_value=mock_res)

    layout = get_circuit_layout("Monza")
    assert layout["grand_prix"] == "Monza"
    assert layout["circuit_id"] == "it-1922"
    assert len(layout["corners"]) >= 4
    assert len(layout["points"]) == 3
    assert layout["corners"][0]["name"] == "Variante del Rettifilo"

def test_get_circuit_layout_baku(mocker):
    _GEOJSON_CACHE.clear()
    mock_res = mocker.Mock()
    mock_res.status_code = 200
    mock_res.json.return_value = {
        "features": [
            {
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[49.853, 40.372], [49.855, 40.373], [49.854, 40.374]]
                }
            }
        ]
    }
    mocker.patch("httpx.Client.get", return_value=mock_res)

    layout = get_circuit_layout("Baku")
    assert layout["grand_prix"] == "Baku"
    assert layout["circuit_id"] == "az-2016"
    assert len(layout["points"]) == 3
