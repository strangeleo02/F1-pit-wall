import groq
from app.config import settings

def get_groq_client() -> groq.Groq | None:
    """Initializes the Groq client."""
    if not settings.GROQ_API_KEY:
        print("Warning: GROQ_API_KEY is not set. LLM features will be disabled.")
        return None
    return groq.Groq(api_key=settings.GROQ_API_KEY)

client = get_groq_client()

def generate_strategy_insight(query: str, telemetry_context: dict, radio_context: list[dict]) -> str:
    """
    Uses the Groq API to generate a strategy answer based on context.

    Args:
        query (str): The user's strategy question.
        telemetry_context (dict): Telemetry data fetched from FastF1.
        radio_context (list[dict]): Relevant radio transcripts from Qdrant.

    Returns:
        str: The LLM's generated response.
    """
    if not client:
        return "Error: Groq client is not configured."

    system_prompt = """You are a senior F1 race strategist.
    You will be provided with telemetry data and relevant team radio communications.
    Use this information to answer the user's question clearly and accurately.
    """

    # Construct the user prompt with context
    user_prompt = f"Question: {query}\n\n"
    user_prompt += f"Telemetry Data:\n{telemetry_context}\n\n"
    user_prompt += "Team Radio Communications:\n"
    for transcript in radio_context:
        user_prompt += f"- {transcript.get('text', 'No text available')}\n"

    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama3-8b-8192", # Example model, can be updated
            temperature=0.5,
            max_tokens=1024
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Failed to generate insight: {str(e)}"
