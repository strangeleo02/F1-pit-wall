from typing import Any
from qdrant_client import AsyncQdrantClient
from app.services.openf1_service import OpenF1Service
from app.services.embedding_service import generate_embeddings_batch_async
from app.services.vector_db import upsert_radio_transcripts

class RadioIngestionPipeline:
    """
    Automated pipeline to ingest driver radio transcripts and race control messages,
    generate vector embeddings, and store indexed payload objects in Qdrant.
    """

    def __init__(self, qdrant_client: AsyncQdrantClient | None = None):
        self.qdrant_client = qdrant_client

    async def ingest_session(
        self,
        year: int,
        grand_prix: str,
        session_type: str = "R",
        session_key: int | None = None,
        driver_number: int | None = None
    ) -> dict[str, Any]:
        """
        Orchestrates fetching, normalizing, embedding, and indexing radio transcripts for a session.
        Auto-resolves session_key via OpenF1 /sessions endpoint if not provided.
        """
        if session_key is None:
            sessions = OpenF1Service.get_sessions(year=year)
            if not isinstance(sessions, list):
                sessions = []
            gp_query = grand_prix.lower().strip()

            # First pass: try matching location/country AND session_name
            for s in sessions:
                if not isinstance(s, dict):
                    continue
                country = (s.get("country_name") or "").lower()
                location = (s.get("location") or "").lower()
                s_name = (s.get("session_name") or s.get("session_type") or "").lower()

                matches_gp = (gp_query in location or location in gp_query or
                              gp_query in country or country in gp_query)

                matches_session = False
                if session_type.upper() == "R" and ("race" in s_name or s_name == "r"):
                    matches_session = True
                elif session_type.upper() == "Q" and ("qualifying" in s_name or s_name == "q"):
                    matches_session = True
                elif session_type.upper() in s_name:
                    matches_session = True

                if matches_gp and matches_session:
                    session_key = s.get("session_key")
                    break

            # Fallback pass: match location and pick race session
            if session_key is None:
                for s in sessions:
                    if not isinstance(s, dict):
                        continue
                    location = (s.get("location") or "").lower()
                    country = (s.get("country_name") or "").lower()
                    s_name = (s.get("session_name") or "").lower()
                    if (gp_query in location or location in gp_query or gp_query in country) and "race" in s_name:
                        session_key = s.get("session_key")
                        break

        session_meta = {
            "year": year,
            "grand_prix": grand_prix,
            "session_type": session_type,
            "session_key": session_key
        }

        # Fetch OpenF1 multi-modal data
        radio_raw = OpenF1Service.get_team_radio(session_key=session_key, driver_number=driver_number, year=year if not session_key else None)
        race_control_raw = OpenF1Service.get_race_control(session_key=session_key, driver_number=driver_number, year=year if not session_key else None)
        drivers_raw = OpenF1Service.get_drivers(session_key=session_key)
        laps_raw = OpenF1Service.get_laps(session_key=session_key, driver_number=driver_number)

        # Normalize into standardized transcript objects
        transcripts = OpenF1Service.normalize_transcripts(
            radio_data=radio_raw,
            race_control_data=race_control_raw,
            drivers_data=drivers_raw,
            laps_data=laps_raw,
            session_meta=session_meta
        )

        if not transcripts:
            return {
                "status": "success",
                "session": session_meta,
                "processed_count": 0,
                "indexed_count": 0,
                "message": "No transcripts or race control messages found for session."
            }

        # Batch embed transcript texts
        texts = [t["transcript_text"] for t in transcripts]
        embeddings = await generate_embeddings_batch_async(texts)

        # Index points in Qdrant vector store if client configured
        indexed_count = 0
        if self.qdrant_client:
            indexed_count = await upsert_radio_transcripts(
                client=self.qdrant_client,
                transcripts=transcripts,
                embeddings=embeddings
            )

        return {
            "status": "success",
            "session": session_meta,
            "processed_count": len(transcripts),
            "indexed_count": indexed_count
        }
