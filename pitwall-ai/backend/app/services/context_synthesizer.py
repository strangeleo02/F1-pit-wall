import numpy as np
from typing import Any
from app.services.intent_router import QueryIntent

class ContextSynthesizer:
    """
    Multi-modal context synthesizer engine.
    Computes lap time delta anomalies, correlates radio transcripts with lap drops/spikes,
    and constructs token-efficient prompt schemas.
    """

    @staticmethod
    def detect_lap_anomalies(laps: list[dict[str, Any]], delta_threshold_sec: float = 1.5) -> list[dict[str, Any]]:
        """
        Scans driver laps to detect lap time spikes and anomaly lap numbers.
        """
        valid_laps = [
            lap for lap in laps
            if isinstance(lap.get("LapTime"), (int, float)) and lap["LapTime"] > 0
        ]
        if not valid_laps:
            return []

        lap_times = [lap["LapTime"] for lap in valid_laps]
        median_time = float(np.median(lap_times))

        anomalies = []
        for lap in valid_laps:
            lap_num = lap.get("LapNumber")
            lap_time = lap.get("LapTime")
            delta = lap_time - median_time

            if delta >= delta_threshold_sec:
                anomalies.append({
                    "lap_number": lap_num,
                    "lap_time_seconds": lap_time,
                    "delta_from_median_sec": round(delta, 3),
                    "type": "spike"
                })
            elif lap_time == min(lap_times):
                anomalies.append({
                    "lap_number": lap_num,
                    "lap_time_seconds": lap_time,
                    "delta_from_median_sec": round(delta, 3),
                    "type": "fastest"
                })

        return anomalies

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

    @classmethod
    def synthesize_prompt(
        cls,
        query: str,
        intent: QueryIntent,
        telemetry_data: dict[str, Any],
        radio_transcripts: list[dict[str, Any]]
    ) -> tuple[str, str]:
        """
        Synthesizes system and user prompts tailored to query intent and multi-modal context.

        Returns:
            tuple[str, str]: (system_prompt, user_prompt)
        """
        system_prompt = (
            "You are a senior F1 pit-wall race strategist and telemetry engineer.\n"
            "Analyze the provided F1 data and answer the user's question clearly, concisely, and accurately."
        )

        laps = telemetry_data.get("laps", [])
        anomalies = cls.detect_lap_anomalies(laps) if laps else []
        correlated_transcripts = cls.correlate_anomalies_with_transcripts(anomalies, radio_transcripts)

        user_prompt = f"Intent: {intent.value.upper()}\nQuestion: {query}\n\n"

        if intent in (QueryIntent.TELEMETRY_ONLY, QueryIntent.MULTI_MODAL_RAG):
            telemetry_summary = {k: v for k, v in telemetry_data.items() if k != "telemetry_stream"}
            if "laps" in telemetry_summary and isinstance(telemetry_summary["laps"], list) and len(telemetry_summary["laps"]) > 10:
                telemetry_summary["total_laps"] = len(telemetry_summary["laps"])
                telemetry_summary["sample_laps"] = telemetry_summary["laps"][:3] + telemetry_summary["laps"][-3:]
                del telemetry_summary["laps"]

            user_prompt += f"Telemetry Statistical Summary:\n{telemetry_summary}\n\n"

            if anomalies:
                user_prompt += f"Detected Lap Time Anomalies / Spikes:\n{anomalies}\n\n"

        if intent in (QueryIntent.RADIO_ONLY, QueryIntent.MULTI_MODAL_RAG):
            user_prompt += "Team Radio Communications & Race Control:\n"
            if correlated_transcripts:
                for t in correlated_transcripts:
                    driver = t.get("driver", "UNK")
                    lap = t.get("lap_start")
                    lap_str = f" [Lap {lap}]" if lap else ""
                    text = t.get("transcript_text") or t.get("text", "")
                    corr_flag = " ⭐ [Correlated Anomaly]" if t.get("correlated_anomaly") else ""
                    user_prompt += f"- {driver}{lap_str}: {text}{corr_flag}\n"
            else:
                user_prompt += "No team radio messages available for this query.\n"

        return system_prompt, user_prompt
