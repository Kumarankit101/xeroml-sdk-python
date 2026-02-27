"""XeroML SDK error classes — maps API error responses to typed exceptions."""

from __future__ import annotations

from typing import Any


class XeroMLError(Exception):
    """Base exception for all XeroML SDK errors."""

    def __init__(
        self,
        code: str,
        status: int,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        self.code = code
        self.status = status
        self.message = message
        self.details = details
        super().__init__(message)


class InvalidAPIKeyError(XeroMLError):
    def __init__(self, message: str = "Invalid or revoked API key.", **kwargs: Any):
        super().__init__(code="invalid_api_key", status=401, message=message, **kwargs)


class CreditsExhaustedError(XeroMLError):
    def __init__(
        self, message: str = "Credits exhausted.", details: dict[str, Any] | None = None
    ):
        super().__init__(code="credits_exhausted", status=402, message=message, details=details)


class RateLimitedError(XeroMLError):
    def __init__(self, message: str = "Rate limit exceeded.", **kwargs: Any):
        super().__init__(code="rate_limited", status=429, message=message, **kwargs)


class ParseFailedError(XeroMLError):
    def __init__(self, message: str = "Parse failed.", **kwargs: Any):
        super().__init__(code="parse_failed", status=422, message=message, **kwargs)


class SessionNotFoundError(XeroMLError):
    def __init__(self, message: str = "Session not found.", **kwargs: Any):
        super().__init__(code="session_not_found", status=404, message=message, **kwargs)


class SessionEndedError(XeroMLError):
    def __init__(self, message: str = "Session is already completed.", **kwargs: Any):
        super().__init__(code="session_ended", status=409, message=message, **kwargs)


_ERROR_MAP: dict[int, type[XeroMLError]] = {
    401: InvalidAPIKeyError,
    402: CreditsExhaustedError,
    429: RateLimitedError,
    422: ParseFailedError,
    404: SessionNotFoundError,
    409: SessionEndedError,
}


def raise_for_status(status_code: int, body: dict[str, Any]) -> None:
    """Parse an API error response and raise the appropriate typed error."""
    error_data = body.get("error", body)
    message = error_data.get("message", "Unknown error")
    details = error_data.get("details")

    error_cls = _ERROR_MAP.get(status_code, XeroMLError)
    if error_cls is XeroMLError:
        raise XeroMLError(
            code=error_data.get("code", "unknown"),
            status=status_code,
            message=message,
            details=details,
        )
    raise error_cls(message=message, details=details)
