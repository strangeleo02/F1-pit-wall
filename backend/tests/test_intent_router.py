import pytest
from app.services.intent_router import IntentRouter, QueryIntent

def test_intent_router_telemetry_only():
    q1 = "What was Verstappen's top speed and max RPM in Monza?"
    intent1 = IntentRouter.classify_intent(q1)
    assert intent1 == QueryIntent.TELEMETRY_ONLY

def test_intent_router_radio_only():
    q2 = "What did Leclerc complain about on team radio to the pit wall?"
    intent2 = IntentRouter.classify_intent(q2)
    assert intent2 == QueryIntent.RADIO_ONLY

def test_intent_router_multi_modal_rag():
    q3 = "Why did Norris lose lap time on lap 25 and what did he tell his engineer on radio?"
    intent3 = IntentRouter.classify_intent(q3)
    assert intent3 == QueryIntent.MULTI_MODAL_RAG

def test_intent_router_default_hybrid():
    q4 = "What was Hamilton's overall race strategy?"
    intent4 = IntentRouter.classify_intent(q4)
    assert intent4 == QueryIntent.MULTI_MODAL_RAG
