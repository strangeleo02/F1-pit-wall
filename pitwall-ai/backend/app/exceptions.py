from fastapi import Request, status
from fastapi.responses import JSONResponse

class PitWallException(Exception):
    """Base exception class for PitWall AI errors."""
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class TelemetryNotFoundError(PitWallException):
    """Raised when telemetry data is not found for a given session/driver."""
    def __init__(self, message: str = "Telemetry data not found"):
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND)

class TelemetryFetchError(PitWallException):
    """Raised when telemetry data fetching fails due to an external error."""
    def __init__(self, message: str = "Failed to fetch telemetry data"):
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST)

class VectorDBUnavailableError(PitWallException):
    """Raised when vector search is unconfigured or fails."""
    def __init__(self, message: str = "Vector DB search is unavailable"):
        super().__init__(message=message, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

class LLMGenerationError(PitWallException):
    """Raised when LLM insight generation fails."""
    def __init__(self, message: str = "Failed to generate LLM insight"):
        super().__init__(message=message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

async def pitwall_exception_handler(request: Request, exc: PitWallException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "error_type": exc.__class__.__name__}
    )
