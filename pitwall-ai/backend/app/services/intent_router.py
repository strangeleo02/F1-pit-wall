import re
from enum import Enum

class QueryIntent(str, Enum):
    TELEMETRY_ONLY = "telemetry_only"
    RADIO_ONLY = "radio_only"
    MULTI_MODAL_RAG = "multi_modal_rag"

class IntentRouter:
    """
    Intelligent query intent classifier module.
    Detects user intent to determine retrieval requirements (telemetry-only, radio-only, or multi-modal RAG).
    """

    TELEMETRY_KEYWORDS = {
        "speed", "max speed", "top speed", "lap time", "throttle", "brake", "braking",
        "gear", "rpm", "drs", "telemetry", "speed trace", "delta", "fastest lap", "kph"
    }

    RADIO_KEYWORDS = {
        "radio", "team radio", "complain", "complaint", "pit wall", "message", "said",
        "audio", "yellow flag", "red flag", "safety car", "vsc", "penalty", "investigation",
        "steward", "race control", "warned", "warning", "box box", "tires gone", "debris"
    }

    @classmethod
    def classify_intent(cls, query: str) -> QueryIntent:
        """
        Classifies a user query string into a QueryIntent.

        Args:
            query (str): User prompt/question.

        Returns:
            QueryIntent: Enum indicating TELEMETRY_ONLY, RADIO_ONLY, or MULTI_MODAL_RAG.
        """
        clean_query = query.lower()

        has_telemetry = any(kw in clean_query for kw in cls.TELEMETRY_KEYWORDS)
        has_radio = any(kw in clean_query for kw in cls.RADIO_KEYWORDS)

        # Hybrid strategy questions or both keywords present
        if (has_telemetry and has_radio) or not (has_telemetry or has_radio):
            return QueryIntent.MULTI_MODAL_RAG

        if has_telemetry and not has_radio:
            return QueryIntent.TELEMETRY_ONLY

        if has_radio and not has_telemetry:
            return QueryIntent.RADIO_ONLY

        return QueryIntent.MULTI_MODAL_RAG
