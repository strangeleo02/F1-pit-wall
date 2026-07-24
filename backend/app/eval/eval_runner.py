import time
from typing import Any, Optional
from fastapi.concurrency import run_in_threadpool
from app.eval.golden_dataset import GOLDEN_BENCHMARK_DATASET
from app.eval.metrics import evaluate_rag_response
from app.services.intent_router import IntentRouter, QueryIntent
from app.services.context_synthesizer import ContextSynthesizer
from app.services.llm_service import generate_strategy_insight
from app.services.f1_service import get_telemetry

# Memory cache for latest evaluation scorecard
_LATEST_EVALUATION_SCORECARD: Optional[dict[str, Any]] = None

def get_latest_scorecard() -> Optional[dict[str, Any]]:
    """Returns the most recent evaluation scorecard."""
    return _LATEST_EVALUATION_SCORECARD

def run_rag_evaluation_suite(limit: Optional[int] = None) -> dict[str, Any]:
    """
    Executes the full RAG evaluation benchmark across the golden test dataset.
    Calculates Context Precision, Faithfulness/Groundedness, Answer Relevance, and Latency.
    """
    global _LATEST_EVALUATION_SCORECARD
    test_cases = GOLDEN_BENCHMARK_DATASET[:limit] if limit else GOLDEN_BENCHMARK_DATASET

    eval_results = []
    total_latency = 0.0

    for item in test_cases:
        t0 = time.time()

        try:
            intent = IntentRouter.classify_intent(item["query"])

            # 1. Fetch telemetry context
            try:
                telemetry = get_telemetry(item["year"], item["grand_prix"], "Race", item["driver_code"])
            except Exception:
                telemetry = {}

            # 2. Synthesize prompt
            system_prompt, user_prompt = ContextSynthesizer.synthesize_prompt(
                item["query"], intent, telemetry, []
            )

            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            contexts = [user_prompt[:400], f"F1 Session: {item['year']} {item['grand_prix']} Driver: {item['driver_code']}"]

            # 3. Generate LLM Insight
            answer = generate_strategy_insight(full_prompt)

            t1 = time.time()
            elapsed = t1 - t0
            total_latency += elapsed

            # 4. Evaluate Metrics
            eval_metrics = evaluate_rag_response(
                query=item["query"],
                answer=answer,
                retrieved_contexts=contexts,
                latency_sec=elapsed
            )

            eval_results.append({
                "test_case_id": item["id"],
                "category": item["category"],
                **eval_metrics,
                "answer_snippet": answer[:150] + "..." if len(answer) > 150 else answer
            })

        except Exception as e:
            eval_results.append({
                "test_case_id": item["id"],
                "category": item["category"],
                "query": item["query"],
                "context_precision": 0.0,
                "faithfulness": 0.0,
                "answer_relevance": 0.0,
                "overall_rag_score": 0.0,
                "latency_sec": round(time.time() - t0, 3),
                "num_contexts_retrieved": 0,
                "error": str(e)
            })

    # Calculate Aggregate Statistics
    precisions = [r["context_precision"] for r in eval_results if "error" not in r]
    faithfulnesses = [r["faithfulness"] for r in eval_results if "error" not in r]
    relevances = [r["answer_relevance"] for r in eval_results if "error" not in r]
    overalls = [r["overall_rag_score"] for r in eval_results if "error" not in r]
    latencies = [r["latency_sec"] for r in eval_results]

    mean_precision = round(float(sum(precisions) / len(precisions)), 4) if precisions else 0.0
    mean_faithfulness = round(float(sum(faithfulnesses) / len(faithfulnesses)), 4) if faithfulnesses else 0.0
    mean_relevance = round(float(sum(relevances) / len(relevances)), 4) if relevances else 0.0
    mean_overall = round(float(sum(overalls) / len(overalls)), 4) if overalls else 0.0
    avg_latency = round(float(sum(latencies) / len(latencies)), 3) if latencies else 0.0

    passed_tests = sum(1 for r in eval_results if r.get("overall_rag_score", 0) >= 0.60)
    pass_rate_pct = round((passed_tests / len(eval_results)) * 100.0, 1) if eval_results else 0.0

    scorecard = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_test_cases": len(eval_results),
        "passed_test_cases": passed_tests,
        "pass_rate_pct": pass_rate_pct,
        "mean_context_precision": mean_precision,
        "mean_faithfulness": mean_faithfulness,
        "mean_answer_relevance": mean_relevance,
        "overall_rag_quality_score": mean_overall,
        "average_latency_sec": avg_latency,
        "detailed_results": eval_results
    }

    _LATEST_EVALUATION_SCORECARD = scorecard
    return scorecard

async def run_rag_evaluation_suite_async(limit: Optional[int] = None) -> dict[str, Any]:
    """Asynchronously runs full RAG evaluation benchmark."""
    return await run_in_threadpool(run_rag_evaluation_suite, limit)
