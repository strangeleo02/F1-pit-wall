import numpy as np
from typing import Any
from app.services.intent_router import QueryIntent

class ContextSynthesizer:
    """
    Multi-modal context synthesizer engine.
    Computes lap time delta anomalies, correlates radio transcripts with lap drops/spikes,
    and constructs token-efficient prompt schemas tailored for LLM rate-limits.
    """

    @staticmethod
    def detect_lap_anomalies(laps: list[dict[str, Any]], delta_threshold_sec: float = 1.5) -> list[dict[str, Any]]:
        """
        Scans driver laps to detect lap time spikes and anomaly lap numbers.
        """
        valid_laps = [
            lap for lap in laps
            if isinstance(lap.get("LapTime") or lap.get("lap_time_seconds"), (int, float))
            and (lap.get("LapTime") or lap.get("lap_time_seconds")) > 0
        ]
        if not valid_laps:
            return []

        lap_times = [lap.get("LapTime") or lap.get("lap_time_seconds") for lap in valid_laps]
        median_time = float(np.median(lap_times))

        anomalies = []
        for lap in valid_laps:
            lap_num = lap.get("LapNumber") or lap.get("lap_number")
            lap_time = lap.get("LapTime") or lap.get("lap_time_seconds")
            delta = lap_time - median_time

            if delta >= delta_threshold_sec:
                anomalies.append({
                    "lap_number": int(lap_num) if lap_num else 0,
                    "lap_time_seconds": round(float(lap_time), 3),
                    "delta_from_median_sec": round(float(delta), 3),
                    "type": "spike"
                })
            elif lap_time == min(lap_times):
                anomalies.append({
                    "lap_number": int(lap_num) if lap_num else 0,
                    "lap_time_seconds": round(float(lap_time), 3),
                    "delta_from_median_sec": round(float(delta), 3),
                    "type": "fastest"
                })

        return anomalies[:10]  # Return top 10 anomalies max for token efficiency

    @staticmethod
    def correlate_anomalies_with_transcripts(
        anomalies: list[dict[str, Any]],
        transcripts: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Matches lap time anomaly lap numbers with radio transcripts and race control messages.
        """
        correlated = []
        anomaly_laps = {a["lap_number"] for a in anomalies if "lap_number" in a}

        for t in transcripts:
            lap = t.get("lap_start")
            item = dict(t)

            if lap in anomaly_laps or any(abs(lap - al) <= 1 for al in anomaly_laps if lap and al):
                item["correlated_anomaly"] = True
            else:
                item["correlated_anomaly"] = False

            correlated.append(item)

        return correlated

    @staticmethod
    def _compact_telemetry_summary(telemetry_data: dict[str, Any]) -> dict[str, Any]:
        """
        Creates a token-efficient compact summary of telemetry data without verbose dict structures.
        """
        if not telemetry_data:
            return {}

        compact = {}
        for key in ["driver", "max_speed_kph", "avg_throttle_percentage", "fastest_lap_number", "fastest_lap_time_seconds"]:
            if key in telemetry_data and telemetry_data[key] is not None:
                compact[key] = telemetry_data[key]

        laps = telemetry_data.get("laps", [])
        if laps:
            compact_laps = []
            for l in laps:
                num = l.get("LapNumber") or l.get("lap_number")
                t = l.get("LapTime") or l.get("lap_time_seconds")
                compound = l.get("Compound") or l.get("compound")
                if num and t:
                    lap_entry: dict[str, Any] = {
                        "L": int(num),
                        "t": round(float(t), 3) if isinstance(t, (int, float)) else t
                    }
                    if compound:
                        lap_entry["c"] = str(compound)
                    compact_laps.append(lap_entry)
            compact["laps"] = compact_laps[:45]  # Cap at 45 compact lap entries

        if "comparison_driver" in telemetry_data and isinstance(telemetry_data["comparison_driver"], dict):
            compact["comparison_driver"] = ContextSynthesizer._compact_telemetry_summary(telemetry_data["comparison_driver"])

        return compact

    @classmethod
    def synthesize_prompt(
        cls,
        query: str,
        intent: QueryIntent,
        telemetry_data: dict[str, Any],
        radio_transcripts: list[dict[str, Any]]
    ) -> tuple[str, str]:
        """
        Synthesizes system and user prompts tailored to query intent and multi-modal context
        with strict token-budget limits to respect Groq rate limits.
        """
        system_prompt = (
            "You are a senior F1 pit-wall race strategist and telemetry engineer.\n"
            "CRITICAL DIRECTIVE: Always prioritize hard numerical telemetry metrics, lap time deltas, speed traces, throttle percentages, and braking statistics as your PRIMARY ground-truth evidence.\n"
            "Treat team radio transcripts as secondary supplemental context. Ground your primary conclusions strictly in the hard telemetry metrics."
        )

        laps = telemetry_data.get("laps", [])
        anomalies = cls.detect_lap_anomalies(laps) if laps else []
        correlated_transcripts = cls.correlate_anomalies_with_transcripts(anomalies, radio_transcripts)

        user_prompt = f"Intent: {intent.value.upper()}\nQuestion: {query}\n\n"

        if intent in (QueryIntent.TELEMETRY_ONLY, QueryIntent.MULTI_MODAL_RAG):
            compact_telemetry = cls._compact_telemetry_summary(telemetry_data)
            user_prompt += f"Telemetry Statistical Summary & Lap Timing:\n{compact_telemetry}\n\n"

            if anomalies:
                user_prompt += f"Detected Lap Time Anomalies / Spikes:\n{anomalies}\n\n"

        if intent in (QueryIntent.RADIO_ONLY, QueryIntent.MULTI_MODAL_RAG, QueryIntent.STEWARD_DECISION):
            user_prompt += "Team Radio Communications & Race Control:\n"
            valid_items = [
                t for t in correlated_transcripts
                if (t.get("transcript_text") or t.get("text"))
            ][:15]  # Cap at 15 radio transcripts max

            if valid_items:
                for t in valid_items:
                    driver = t.get("driver", "UNK")
                    lap = t.get("lap_start")
                    lap_str = f" [Lap {lap}]" if lap else ""
                    text = t.get("transcript_text") or t.get("text", "")
                    gp = t.get("grand_prix") or ""
                    year_val = t.get("year") or ""
                    gp_str = f" ({year_val} {gp})" if gp and year_val else ""
                    corr_flag = " ⭐ [Anomaly Correlation]" if t.get("correlated_anomaly") else ""
                    user_prompt += f"- {driver}{lap_str}{gp_str}: {text}{corr_flag}\n"
            else:
                user_prompt += "No team radio messages available for this query.\n"

        # Safety truncation: Ensure prompt length stays under ~12,000 characters (~3000 tokens)
        if len(user_prompt) > 12000:
            user_prompt = user_prompt[:11800] + "\n\n... [Context Truncated for Rate-Limit Efficiency]"

        return system_prompt, user_prompt
