import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.eval.metrics import (
    calculate_context_precision,
    calculate_faithfulness,
    calculate_answer_relevance,
    evaluate_rag_response
)
from app.eval.golden_dataset import GOLDEN_BENCHMARK_DATASET

client = TestClient(app)

def test_context_precision():
    query = "Verstappen top speed Monza 2024"
    contexts = [
        "Verstappen hit 352 kph top speed down Monza main straight on lap 12.",
        "Leclerc had good traction out of Parabolica."
    ]
    precision = calculate_context_precision(query, contexts)
    assert precision > 0.3

def test_faithfulness_scoring():
    contexts = ["Norris telemetry shows 340 kph speed on lap 15."]
    grounded_answer = "Norris recorded a top speed of 340 kph on lap 15."
    ungrounded_answer = "Norris recorded a top speed of 385 kph on lap 45."

    score_grounded = calculate_faithfulness(grounded_answer, contexts)
    score_ungrounded = calculate_faithfulness(ungrounded_answer, contexts)

    assert score_grounded > score_ungrounded

def test_answer_relevance():
    query = "Should Leclerc pit for soft tyres at Monaco?"
    relevant_answer = "Leclerc should maintain track position at Monaco as pit stops cost 19 seconds."
    irrelevant_answer = "The weather in Tokyo is sunny today."

    rel_score = calculate_answer_relevance(query, relevant_answer)
    irrel_score = calculate_answer_relevance(query, irrelevant_answer)

    assert rel_score > irrel_score

def test_evaluate_rag_response_summary():
    res = evaluate_rag_response(
        query="Compare Norris and Verstappen Monza Sector 1",
        answer="Norris was 0.120s faster than Verstappen in Sector 1 at Monza.",
        retrieved_contexts=["Norris Sector 1 time was 26.1s vs Verstappen 26.22s."]
    )

    assert "context_precision" in res
    assert "faithfulness" in res
    assert "answer_relevance" in res
    assert "overall_rag_score" in res
    assert res["overall_rag_score"] > 0.0

def test_golden_dataset_endpoint():
    response = client.get("/api/v1/eval/golden-dataset")
    assert response.status_code == 200
    data = response.json()
    assert "total_cases" in data
    assert data["total_cases"] >= 8
    assert len(data["test_cases"]) > 0

@patch("app.routers.eval.run_rag_evaluation_suite_async")
def test_evaluation_scorecard_endpoint(mock_eval):
    mock_eval.return_value = {
        "timestamp": "2026-07-24T00:00:00Z",
        "total_test_cases": 2,
        "passed_test_cases": 2,
        "pass_rate_pct": 100.0,
        "mean_context_precision": 0.85,
        "mean_faithfulness": 0.90,
        "mean_answer_relevance": 0.88,
        "overall_rag_quality_score": 0.87,
        "average_latency_sec": 0.45,
        "detailed_results": []
    }
    response = client.get("/api/v1/eval/scorecard")
    assert response.status_code == 200
    data = response.json()
    assert "total_test_cases" in data
    assert "overall_rag_quality_score" in data
