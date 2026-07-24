from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from app.eval.eval_runner import run_rag_evaluation_suite_async, get_latest_scorecard
from app.eval.golden_dataset import GOLDEN_BENCHMARK_DATASET

router = APIRouter(prefix="/eval", tags=["RAG Evaluation System"])

@router.post("/run")
async def run_evaluation_suite(
    limit: Optional[int] = Query(None, ge=1, le=50, description="Optional limit on number of golden test cases to run")
):
    """
    Triggers the automated RAG evaluation benchmark across the golden dataset.
    Calculates Context Precision, Faithfulness (Groundedness), Answer Relevance, and Latency.
    """
    try:
        return await run_rag_evaluation_suite_async(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG Evaluation failed: {str(e)}")

@router.get("/scorecard")
async def get_evaluation_scorecard():
    """
    Returns the most recent RAG evaluation scorecard and detailed metric breakdown.
    """
    scorecard = get_latest_scorecard()
    if not scorecard:
        # Run a quick 2-case mini benchmark if no scorecard exists yet
        scorecard = await run_rag_evaluation_suite_async(limit=2)
    return scorecard

@router.get("/golden-dataset")
async def get_golden_benchmark_dataset():
    """
    Returns the curated golden benchmark dataset used for RAG evaluation.
    """
    return {
        "total_cases": len(GOLDEN_BENCHMARK_DATASET),
        "test_cases": GOLDEN_BENCHMARK_DATASET
    }
