#!/usr/bin/env python3
"""
CLI Evaluation Runner for PitWall AI RAG Pipeline.
Usage:
    python evaluate_rag.py [--limit N]
"""

import sys
import json
import argparse
from app.eval.eval_runner import run_rag_evaluation_suite

def main():
    parser = argparse.ArgumentParser(description="PitWall AI RAG Evaluation Suite")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of test cases to evaluate")
    args = parser.parse_args()

    print(f"🏎️ Running PitWall AI RAG Evaluation Suite (Limit: {args.limit or 'ALL'})...")
    scorecard = run_rag_evaluation_suite(limit=args.limit)

    print("\n" + "=" * 60)
    print("🏆 PITWALL AI RAG QUALITY SCORECARD")
    print("=" * 60)
    print(f"Timestamp:                 {scorecard['timestamp']}")
    print(f"Total Test Cases Evaluated: {scorecard['total_test_cases']}")
    print(f"Pass Rate (>=60% Score):    {scorecard['pass_rate_pct']}%")
    print(f"Mean Context Precision:    {scorecard['mean_context_precision']:.4f}")
    print(f"Mean Faithfulness:         {scorecard['mean_faithfulness']:.4f}")
    print(f"Mean Answer Relevance:     {scorecard['mean_answer_relevance']:.4f}")
    print(f"OVERALL RAG QUALITY SCORE: {scorecard['overall_rag_quality_score']:.4f}")
    print(f"Average Latency:           {scorecard['average_latency_sec']:.3f}s")
    print("=" * 60 + "\n")

    print(json.dumps(scorecard["detailed_results"], indent=2))

if __name__ == "__main__":
    main()
