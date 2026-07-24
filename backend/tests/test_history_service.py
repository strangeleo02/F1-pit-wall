import pytest
from app.services.history_service import fetch_pitstops_sync, fetch_standings_sync, clear_history_cache

def setup_function():
    clear_history_cache()

def test_fetch_pitstops_sync(mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "MRData": {
            "RaceTable": {
                "Races": [
                    {
                        "raceName": "Italian Grand Prix",
                        "Circuit": {"circuitName": "Autodromo Nazionale di Monza"},
                        "PitStops": [
                            {"driverId": "max_verstappen", "lap": "24", "stop": "1", "duration": "2.410", "time": "15:32:01"}
                        ]
                    }
                ]
            }
        }
    }
    mocker.patch("httpx.Client.get", return_value=mock_response)

    stops = fetch_pitstops_sync(2023, 14)
    assert len(stops) == 1
    assert stops[0]["driver_id"] == "max_verstappen"
    assert stops[0]["duration"] == "2.410"

def test_fetch_standings_sync(mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "MRData": {
            "StandingsTable": {
                "StandingsLists": [
                    {
                        "DriverStandings": [
                            {
                                "position": "1",
                                "points": "575",
                                "wins": "19",
                                "Driver": {"code": "VER", "givenName": "Max", "familyName": "Verstappen"},
                                "Constructors": [{"name": "Red Bull"}]
                            }
                        ]
                    }
                ]
            }
        }
    }
    mocker.patch("httpx.Client.get", return_value=mock_response)

    standings = fetch_standings_sync(2023, "driver")
    assert len(standings) == 1
    assert standings[0]["driver_code"] == "VER"
    assert standings[0]["points"] == 575.0
