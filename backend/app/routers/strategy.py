import asyncio
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
    Helper function to perform Intent Classification, parallelized data retrieval,
    on-demand OpenF1/Qdrant transcript auto-population, and multi-modal context synthesis.
    """
    intent = IntentRouter.classify_intent(request.query)

    async def fetch_primary_telemetry():
        try:
            return await get_telemetry_async(
                year=request.year,
                grand_prix=request.grand_prix,
                session_type=request.session_type,
                driver_code=request.driver_code,
                qdrant_client=qdrant_client
            )
        except PitWallException:
            raise
        except Exception as e:
            print(f"Primary telemetry retrieval warning: {e}")
            return {}

    async def fetch_comp_telemetry():
        if request.comparison_driver_code and request.comparison_driver_code.upper() != request.driver_code.upper():
            try:
                return await get_telemetry_async(
                    year=request.year,
                    grand_prix=request.grand_prix,
                    session_type=request.session_type,
                    driver_code=request.comparison_driver_code,
                    qdrant_client=qdrant_client
                )
            except Exception as ce:
                print(f"Comparison driver telemetry warning: {ce}")
                return None
        return None

    async def fetch_radio_context():
        try:
            query_embedding = await generate_embedding_async(request.query)
            radio = await search_radio_transcripts(
                client=qdrant_client,
                query_embedding=query_embedding,
                driver=request.driver_code,
                year=request.year,
                session=request.session_type,
                grand_prix=request.grand_prix
            )
            if not radio and qdrant_client:
                pipeline = RadioIngestionPipeline(qdrant_client=qdrant_client)
                await pipeline.ingest_session(
                    year=request.year,
                    grand_prix=request.grand_prix,
                    session_type=request.session_type
                )
                radio = await search_radio_transcripts(
                    client=qdrant_client,
                    query_embedding=query_embedding,
                    driver=request.driver_code,
                    year=request.year,
                    session=request.session_type,
                    grand_prix=request.grand_prix
                )
            return radio
        except Exception as e:
            print(f"Radio context search warning: {e}")
            return []

    # Execute primary telemetry, comparison telemetry, and radio search concurrently in parallel!
    primary_telemetry, comp_telemetry, radio_context = await asyncio.gather(
        fetch_primary_telemetry(),
        fetch_comp_telemetry(),
        fetch_radio_context()
    )

    telemetry_data = dict(primary_telemetry) if primary_telemetry else {}
    if comp_telemetry:
        telemetry_data["comparison_driver"] = comp_telemetry

    synthesis_intent = QueryIntent.MULTI_MODAL_RAG if (telemetry_data or radio_context) else intent

    system_prompt, user_prompt = ContextSynthesizer.synthesize_prompt(
        query=request.query,
        intent=synthesis_intent,
        telemetry_data=telemetry_data,
        radio_transcripts=radio_context or []
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
