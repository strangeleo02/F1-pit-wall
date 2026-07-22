from pydantic import BaseModel

class StrategyQueryRequest(BaseModel):
    year: int
    grand_prix: str
    session_type: str
    driver_code: str
    query: str

class StrategyQueryResponse(BaseModel):
    insight: str
    telemetry: dict
    radio_transcripts: list[dict]
