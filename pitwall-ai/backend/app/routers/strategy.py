from fastapi import APIRouter, HTTPException
from app.schemas import StrategyQueryRequest, StrategyQueryResponse
from app.services.f1_service import get_telemetry
from app.services.embedding_service import generate_embedding
from app.services.vector_db import search_radio_transcripts
from app.services.llm_service import generate_strategy_insight

router = APIRouter(
    prefix="/strategy",
    tags=["Strategy"]
)

@router.post("/query", response_model=StrategyQueryResponse)
def query_strategy(request: StrategyQueryRequest):
    """
    Main endpoint for PitWall AI.
    Fetches F1 telemetry, retrieves relevant team radios via vector search,
    and generates an insight using Groq LLM.
    """
    # 1. Fetch Telemetry
    telemetry_data = get_telemetry(
        year=request.year,
        grand_prix=request.grand_prix,
        session_type=request.session_type,
        driver_code=request.driver_code
    )

    if "error" in telemetry_data:
        raise HTTPException(status_code=400, detail=telemetry_data["error"])

    # 2. Vector Search for Radio Transcripts
    try:
        query_embedding = generate_embedding(request.query)
        radio_context = search_radio_transcripts(query_embedding)
    except Exception as e:
        print(f"Embedding/Vector DB Error: {e}")
        # Gracefully handle vector db failure if not configured
        radio_context = [{"text": "Radio transcript search failed or is unavailable."}]

    # 3. Generate Insight with Groq
    insight = generate_strategy_insight(
        query=request.query,
        telemetry_context=telemetry_data,
        radio_context=radio_context
    )

    return StrategyQueryResponse(
        insight=insight,
        telemetry=telemetry_data,
        radio_transcripts=radio_context
    )
