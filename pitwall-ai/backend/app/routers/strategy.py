import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from qdrant_client import AsyncQdrantClient
import groq

from app.schemas import StrategyQueryRequest, StrategyQueryResponse, ErrorResponse
from app.dependencies import get_qdrant_client, get_groq_client
from app.services.intent_router import IntentRouter, QueryIntent
from app.services.context_synthesizer import ContextSynthesizer
from app.services.f1_service import get_telemetry_async
from app.services.embedding_service import generate_embedding_async
from app.services.vector_db import search_radio_transcripts
from app.services.llm_service import generate_strategy_insight, stream_strategy_insight
from app.ingestion.radio_ingestion import RadioIngestionPipeline
from app.exceptions import PitWallException, VectorDBUnavailableError, LLMGenerationError

router = APIRouter(
    prefix="/strategy",
    tags=["Strategy"]
)

async def _orchestrate_retrieval_and_synthesis(
    request: StrategyQueryRequest,
    qdrant_client: AsyncQdrantClient | None
):
    """
    Helper function to perform Intent Classification, conditional data retrieval,
    on-demand OpenF1/Qdrant transcript auto-population, and multi-modal context synthesis.
    """
    intent = IntentRouter.classify_intent(request.query)

    # 1. Always Fetch Telemetry using Qdrant telemetry cache
    telemetry_data = {}
    try:
        primary_telemetry = await get_telemetry_async(
            year=request.year,
            grand_prix=request.grand_prix,
            session_type=request.session_type,
            driver_code=request.driver_code,
            qdrant_client=qdrant_client
        )
        telemetry_data = dict(primary_telemetry)

        # If comparison driver specified, fetch secondary driver telemetry
        if request.comparison_driver_code and request.comparison_driver_code.upper() != request.driver_code.upper():
            try:
                comp_telemetry = await get_telemetry_async(
                    year=request.year,
                    grand_prix=request.grand_prix,
                    session_type=request.session_type,
                    driver_code=request.comparison_driver_code,
                    qdrant_client=qdrant_client
                )
                telemetry_data["comparison_driver"] = comp_telemetry
            except Exception as ce:
                print(f"Comparison driver telemetry warning: {ce}")
    except PitWallException:
        raise
    except Exception as e:
        print(f"Telemetry retrieval warning: {e}")

    # 2. Always Search Vector DB Radio Transcripts with On-Demand Auto-Ingestion
    radio_context = []
    try:
        query_embedding = await generate_embedding_async(request.query)
        radio_context = await search_radio_transcripts(
            client=qdrant_client,
            query_embedding=query_embedding,
            driver=request.driver_code,
            year=request.year,
            session=request.session_type,
            grand_prix=request.grand_prix
        )

        # If no transcripts found in Qdrant for this requested race/year, auto-populate on the fly!
        if not radio_context and qdrant_client:
            print(f"📡 On-Demand Ingestion triggered for {request.year} {request.grand_prix} ({request.session_type})...")
            pipeline = RadioIngestionPipeline(qdrant_client=qdrant_client)
            ingest_res = await pipeline.ingest_session(
                year=request.year,
                grand_prix=request.grand_prix,
                session_type=request.session_type
            )
            print(f"   ↳ Auto-populated {ingest_res.get('indexed_count', 0)} points in Qdrant.")

            # Retry search after auto-population
            radio_context = await search_radio_transcripts(
                client=qdrant_client,
                query_embedding=query_embedding,
                driver=request.driver_code,
                year=request.year,
                session=request.session_type,
                grand_prix=request.grand_prix
            )

    except VectorDBUnavailableError as ve:
        print(f"Embedding/Vector DB Warning: {ve}")
        radio_context = [{"text": "Radio transcript search is unavailable or unconfigured."}]
    except Exception as e:
        print(f"Embedding/Vector DB Error: {e}")
        radio_context = [{"text": "Radio transcript search failed."}]

    # Force multi-modal synthesis intent when telemetry or radio context is present
    synthesis_intent = QueryIntent.MULTI_MODAL_RAG if (telemetry_data or radio_context) else intent

    # 3. Synthesize Multi-Modal Context Prompts
    system_prompt, user_prompt = ContextSynthesizer.synthesize_prompt(
        query=request.query,
        intent=synthesis_intent,
        telemetry_data=telemetry_data,
        radio_transcripts=radio_context
    )

    return intent, telemetry_data, radio_context, system_prompt, user_prompt

@router.post(
    "/query",
    response_model=StrategyQueryResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        404: {"model": ErrorResponse, "description": "Telemetry Not Found"},
        503: {"model": ErrorResponse, "description": "Service Unavailable"}
    }
)
async def query_strategy(
    request: StrategyQueryRequest,
    qdrant_client: AsyncQdrantClient | None = Depends(get_qdrant_client),
    groq_client: groq.AsyncGroq | None = Depends(get_groq_client)
):
    """
    Main strategy query endpoint.
    Classifies intent, dynamically populates & retrieves multi-modal context, and generates an insight.
    """
    intent, telemetry_data, radio_context, system_prompt, user_prompt = await _orchestrate_retrieval_and_synthesis(
        request, qdrant_client
    )

    try:
        insight = await generate_strategy_insight(
            client=groq_client,
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
    except LLMGenerationError as le:
        insight = f"LLM Strategy Generation Unavailable: {le.message}"

    return StrategyQueryResponse(
        insight=insight,
        telemetry=telemetry_data,
        radio_transcripts=radio_context
    )

@router.post(
    "/stream",
    responses={
        200: {"description": "Server-Sent Events (SSE) Real-Time Token Stream"},
        400: {"model": ErrorResponse, "description": "Bad Request"}
    }
)
async def stream_strategy(
    request: StrategyQueryRequest,
    qdrant_client: AsyncQdrantClient | None = Depends(get_qdrant_client),
    groq_client: groq.AsyncGroq | None = Depends(get_groq_client)
):
    """
    Server-Sent Events (SSE) streaming endpoint for real-time strategy insight generation.
    """
    intent, telemetry_data, radio_context, system_prompt, user_prompt = await _orchestrate_retrieval_and_synthesis(
        request, qdrant_client
    )

    async def sse_event_generator():
        meta = {
            "intent": intent.value,
            "telemetry": telemetry_data,
            "radio_transcripts": radio_context
        }
        yield f"data: {json.dumps({'type': 'metadata', 'data': meta})}\n\n"

        try:
            async for token in stream_strategy_insight(groq_client, system_prompt, user_prompt):
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(sse_event_generator(), media_type="text/event-stream")
