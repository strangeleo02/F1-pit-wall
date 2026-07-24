import re
import numpy as np
from typing import Any
from app.services.embedding_service import get_embedding_model

def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """Computes cosine similarity between two 1D vectors."""
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(v1, v2) / (norm1 * norm2))

def calculate_context_precision(query: str, retrieved_contexts: list[str]) -> float:
    """
    Measures semantic relevance of retrieved context chunks relative to the user query.
    Returns float score between 0.0 and 1.0.
    """
    if not retrieved_contexts or not query.strip():
        return 0.0

    model = get_embedding_model()
    query_emb = model.encode(query, convert_to_numpy=True)
    context_embs = model.encode(retrieved_contexts, convert_to_numpy=True)

    sims = [max(0.0, cosine_similarity(query_emb, c_emb)) for c_emb in context_embs]
    return round(float(np.mean(sims)), 4) if sims else 0.0

def calculate_faithfulness(answer: str, retrieved_contexts: list[str]) -> float:
    """
    Measures Groundedness / Faithfulness: verifies whether numerical values and key strategy terms
    (lap times, speed, gaps, compounds) mentioned in the answer exist in the retrieved contexts.
    Returns float score between 0.0 and 1.0.
    """
    if not answer or not answer.strip():
        return 0.0
    if not retrieved_contexts:
        return 0.2  # Penalty for generating without context

    full_context_text = " ".join(retrieved_contexts).lower()
    
    # Extract numbers (lap numbers, speed in kph, gaps in seconds)
    numbers_in_answer = set(re.findall(r'\b\d+(?:\.\d+)?\b', answer))
    if not numbers_in_answer:
        return 0.90  # High groundedness if answer has no ungrounded specific metrics

    grounded_count = 0
    for num in numbers_in_answer:
        if num in full_context_text:
            grounded_count += 1

    grounded_ratio = grounded_count / len(numbers_in_answer)
    return round(float(min(1.0, 0.4 + 0.6 * grounded_ratio)), 4)

def calculate_answer_relevance(query: str, answer: str) -> float:
    """
    Measures semantic relevance between user query and generated LLM response.
    Returns float score between 0.0 and 1.0.
    """
    if not query.strip() or not answer.strip():
        return 0.0

    model = get_embedding_model()
    query_emb = model.encode(query, convert_to_numpy=True)
    answer_emb = model.encode(answer, convert_to_numpy=True)

    sim = cosine_similarity(query_emb, answer_emb)
    return round(float(max(0.0, min(1.0, sim))), 4)

def evaluate_rag_response(
    query: str,
    answer: str,
    retrieved_contexts: list[str],
    latency_sec: float = 0.0
) -> dict[str, Any]:
    """
    Evaluates a single RAG response across the RAG Triad:
    1. Context Precision (Retrieval Quality)
    2. Faithfulness / Groundedness (Hallucination Control)
    3. Answer Relevance (Intent Satisfaction)
    """
    context_precision = calculate_context_precision(query, retrieved_contexts)
    faithfulness = calculate_faithfulness(answer, retrieved_contexts)
    answer_relevance = calculate_answer_relevance(query, answer)

    overall_score = round(
        0.35 * context_precision + 0.40 * faithfulness + 0.25 * answer_relevance, 4
    )

    return {
        "query": query,
        "context_precision": context_precision,
        "faithfulness": faithfulness,
        "answer_relevance": answer_relevance,
        "overall_rag_score": overall_score,
        "latency_sec": round(latency_sec, 3),
        "num_contexts_retrieved": len(retrieved_contexts)
    }
