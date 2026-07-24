import httpx
from datetime import datetime
from typing import Any
from fastapi.concurrency import run_in_threadpool

OPENF1_BASE_URL = "https://api.openf1.org/v1"

def fetch_openf1_endpoint(endpoint: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """
    Synchronous HTTP client call to OpenF1 REST API.
    """
    url = f"{OPENF1_BASE_URL}/{endpoint.lstrip('/')}"
    clean_params = {k: v for k, v in (params or {}).items() if v is not None}
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, params=clean_params)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list):
                return data
            return []
    except Exception:
        # Return empty list on connection/network issue or invalid query
        return []

async def fetch_openf1_endpoint_async(endpoint: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """
    Async wrapper for OpenF1 API requests.
    """
    return await run_in_threadpool(fetch_openf1_endpoint, endpoint, params)

class OpenF1Service:
    """
    Service layer for retrieving and normalizing driver radio transcripts,
    race control messages, driver mappings, and lap references from OpenF1 API.
    """

    @staticmethod
    def get_team_radio(session_key: int | None = None, driver_number: int | None = None, year: int | None = None) -> list[dict[str, Any]]:
        params = {"session_key": session_key, "driver_number": driver_number, "year": year}
        return fetch_openf1_endpoint("team_radio", params)

    @staticmethod
    def get_race_control(session_key: int | None = None, driver_number: int | None = None, year: int | None = None) -> list[dict[str, Any]]:
        params = {"session_key": session_key, "driver_number": driver_number, "year": year}
        return fetch_openf1_endpoint("race_control", params)

    @staticmethod
    def get_drivers(session_key: int | None = None) -> list[dict[str, Any]]:
        params = {"session_key": session_key}
        return fetch_openf1_endpoint("drivers", params)

    @staticmethod
    def get_laps(session_key: int | None = None, driver_number: int | None = None) -> list[dict[str, Any]]:
        params = {"session_key": session_key, "driver_number": driver_number}
        return fetch_openf1_endpoint("laps", params)

    @staticmethod
    def get_sessions(year: int | None = None, country_name: str | None = None, session_name: str | None = None) -> list[dict[str, Any]]:
        params = {"year": year, "country_name": country_name, "session_name": session_name}
        return fetch_openf1_endpoint("sessions", params)

    @classmethod
    def normalize_transcripts(
        cls,
        radio_data: list[dict[str, Any]],
        race_control_data: list[dict[str, Any]],
        drivers_data: list[dict[str, Any]],
        laps_data: list[dict[str, Any]],
        session_meta: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Normalizes raw OpenF1 data into standard PitWall radio transcript payload records.
        """
        # Map driver numbers to 3-letter driver codes and team names
        driver_code_map: dict[int, str] = {}
        driver_team_map: dict[int, str] = {}
        for d in drivers_data:
            num = d.get("driver_number")
            acronym = d.get("name_acronym") or d.get("broadcast_name", "UNK")[:3].upper()
            team = d.get("team_name", "Unknown Team")
            if num:
                driver_code_map[num] = acronym
                driver_team_map[num] = team

        # Helper to correlate ISO timestamp string with lap number from laps_data
        def find_lap_number(timestamp_str: str, driver_num: int | None) -> int | None:
            if not timestamp_str or not laps_data:
                return None
            try:
                msg_dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            except ValueError:
                return None

            for lap in laps_data:
                if driver_num and lap.get("driver_number") != driver_num:
                    continue
                date_start = lap.get("date_start")
                if not date_start:
                    continue
                try:
                    start_dt = datetime.fromisoformat(date_start.replace("Z", "+00:00"))
                    # If message timestamp is within 120 seconds after lap start
                    if 0 <= (msg_dt - start_dt).total_seconds() <= 120:
                        return lap.get("lap_number")
                except ValueError:
                    continue
            return None

        normalized: list[dict[str, Any]] = []

        year = session_meta.get("year", 2023)
        grand_prix = session_meta.get("grand_prix", "Unknown GP")
        session_type = session_meta.get("session_type", "R")

        # Process team radio messages
        for item in radio_data:
            num = item.get("driver_number")
            driver_code = driver_code_map.get(num, f"D{num}" if num else "ALL")
            team_name = driver_team_map.get(num, "PitWall")
            ts = item.get("date") or ""
            lap_num = find_lap_number(ts, num)

            recording_url = item.get("recording_url") or ""
            transcript_content = item.get("transcript") or item.get("text") or item.get("message")

            if transcript_content and not str(transcript_content).startswith("Team radio audio:") and not str(transcript_content).startswith("http"):
                text = str(transcript_content)
            else:
                text = f"Driver {driver_code} ({team_name}) team radio transmission"

            normalized.append({
                "driver": driver_code,
                "session": session_type,
                "year": year,
                "grand_prix": grand_prix,
                "session_key": session_meta.get("session_key"),
                "lap_start": lap_num,
                "lap_end": lap_num,
                "team": team_name,
                "transcript_text": text,
                "recording_url": recording_url,
                "timestamp": ts,
                "source": "team_radio"
            })

        # Process race control messages
        for rc in race_control_data:
            num = rc.get("driver_number")
            driver_code = driver_code_map.get(num, "RACE_CONTROL") if num else "ALL"
            team_name = driver_team_map.get(num, "FIA Race Control") if num else "FIA Race Control"
            ts = rc.get("date") or ""
            category = rc.get("category") or "Message"
            flag = rc.get("flag") or ""
            message = rc.get("message") or "Race Control notification"

            text = f"[{category.upper()}] {message}" if not flag else f"[{category.upper()} - {flag}] {message}"
            lap_num = rc.get("lap_number") or find_lap_number(ts, num)

            normalized.append({
                "driver": driver_code,
                "session": session_type,
                "year": year,
                "grand_prix": grand_prix,
                "session_key": session_meta.get("session_key"),
                "lap_start": lap_num,
                "lap_end": lap_num,
                "team": team_name,
                "transcript_text": text,
                "recording_url": "",
                "timestamp": ts,
                "source": "race_control"
            })

        return normalized
