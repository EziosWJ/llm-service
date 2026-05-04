from __future__ import annotations


class AppError(Exception):
    status_code: int = 500
    error: str = "internal_error"

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class ValidationError(AppError):
    status_code = 400
    error = "validation_error"


class BusinessError(AppError):
    status_code = 422
    error = "business_error"


class UpstreamError(Exception):
    """Raised when upstream LLM service is unavailable or times out."""

    status_code = 502
    error = "upstream_error"

    def __init__(self, detail: str = "Upstream service failed") -> None:
        super().__init__(detail)
        self.detail = detail
