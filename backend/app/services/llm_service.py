from typing import AsyncGenerator
import groq
from app.config import settings
from app.exceptions import LLMGenerationError

async def generate_strategy_insight(
    client: groq.AsyncGroq | None,
    query: str | None = None,
    telemetry_context: dict | None = None,
    radio_context: list[dict] | None = None,
    system_prompt: str | None = None,
    user_prompt: str | None = None
) -> str:
    """
    Asynchronously uses the Groq API to generate a strategy answer based on synthesized context.
    """
    if not client:
        raise LLMGenerationError("Groq client is not configured.")

    if not system_prompt or not user_prompt:
        system_prompt = system_prompt or "You are a senior F1 race strategist on the pit wall."
        telemetry_summary = {k: v for k, v in (telemetry_context or {}).items() if k != "telemetry_stream"}
        user_prompt = f"Question: {query}\n\nTelemetry Summary:\n{telemetry_summary}\n\nRadio Transcripts:\n{radio_context}"

    try:
        response = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=settings.GROQ_MODEL_NAME,
            temperature=0.5,
            max_tokens=1024
        )
        return response.choices[0].message.content
    except LLMGenerationError:
        raise
    except Exception as e:
        raise LLMGenerationError(f"Failed to generate insight: {str(e)}")

async def stream_strategy_insight(
    client: groq.AsyncGroq | None,
    system_prompt: str,
    user_prompt: str
) -> AsyncGenerator[str, None]:
    """
    Asynchronously streams strategy response tokens from Groq API via an AsyncGenerator.
    """
    if not client:
        raise LLMGenerationError("Groq client is not configured.")

    try:
        response_stream = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=settings.GROQ_MODEL_NAME,
            temperature=0.5,
            max_tokens=1024,
            stream=True
        )

        async for chunk in response_stream:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except LLMGenerationError:
        raise
    except Exception as e:
        raise LLMGenerationError(f"Failed to stream insight: {str(e)}")
