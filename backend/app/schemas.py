from pydantic import BaseModel, Field

class StrategyQueryRequest(BaseModel):
    year: int = Field(..., ge=1950, le=2030, description="The race season year (e.g., 2023)")
    grand_prix: str = Field(..., min_length=2, max_length=100, description="Grand Prix name or location (e.g., Monza)")
    session_type: str = Field(..., pattern=r"^(R|Q|FP1|FP2|FP3|S|SQ)$", description="Session type: R, Q, FP1, FP2, FP3, S, SQ")
    driver_code: str = Field(..., pattern=r"^[A-Z0-9]{3}$", description="3-letter driver code (e.g., VER)")
    comparison_driver_code: str | None = Field(None, description="Optional comparison 3-letter driver code (e.g., HAM)")
    query: str = Field(..., min_length=1, max_length=1000, description="Strategy question")

class StrategyQueryResponse(BaseModel):
    insight: str
    telemetry: dict
    radio_transcripts: list[dict]

class ErrorResponse(BaseModel):
    detail: str
    error_type: str
