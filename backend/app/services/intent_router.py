import re
from enum import Enum

class QueryIntent(str, Enum):
    TELEMETRY_ONLY = "telemetry_only"
    RADIO_ONLY = "radio_only"
    STEWARD_DECISION = "steward_decision"
    MULTI_MODAL_RAG = "multi_modal_rag"

class IntentRouter:
    """
    Intelligent query intent classifier module.
    Detects user intent to determine retrieval requirements (telemetry-only, radio-only, steward decisions, or multi-modal RAG).
    """

    TELEMETRY_KEYWORDS = {
        "speed", "max speed", "top speed", "lap time", "throttle", "brake", "braking",
        "gear", "rpm", "drs", "telemetry", "speed trace", "delta", "fastest lap", "kph"
    }

    RADIO_KEYWORDS = {
        "radio", "team radio", "complain", "complaint", "pit wall", "message", "said",
        "audio", "yellow flag", "red flag", "safety car", "vsc", "race control", "warned", "warning", "box box", "tires gone", "debris"
    }

    STEWARD_KEYWORDS = {
        "steward", "penalty", "investigation", "track limits", "offence", "infringement", "deleted", "grid penalty", "fia"
    }

    @classmethod
    def classify_intent(cls, query: str) -> QueryIntent:
        """
        Classifies a user query string into a QueryIntent.
        """
        clean_query = query.lower()

        has_telemetry = any(kw in clean_query for kw in cls.TELEMETRY_KEYWORDS)
        has_radio = any(kw in clean_query for kw in cls.RADIO_KEYWORDS)
        has_steward = any(kw in clean_query for kw in cls.STEWARD_KEYWORDS)

        if has_steward and not (has_telemetry and has_radio):
            return QueryIntent.STEWARD_DECISION

        # Hybrid strategy questions or multiple keywords present
        if (has_telemetry and has_radio) or not (has_telemetry or has_radio or has_steward):
            return QueryIntent.MULTI_MODAL_RAG

        if has_telemetry:
            return QueryIntent.TELEMETRY_ONLY

        if has_radio:
            return QueryIntent.RADIO_ONLY

        return QueryIntent.MULTI_MODAL_RAG

