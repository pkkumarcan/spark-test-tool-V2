"""Gateway middleware: rate limiting, API key auth, body size limit."""

from __future__ import annotations

import logging
import time
from collections import defaultdict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

_HEALTH_PATHS = {"/health", "/docs", "/openapi.json"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory token bucket rate limiter."""

    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.rpm = requests_per_minute
        self._buckets: dict[str, list[float]] = defaultdict(list)

    def _client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in _HEALTH_PATHS:
            return await call_next(request)

        client_ip = self._client_ip(request)
        now = time.time()
        window_start = now - 60

        self._buckets[client_ip] = [
            t for t in self._buckets[client_ip] if t > window_start
        ]

        if len(self._buckets[client_ip]) >= self.rpm:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
            )

        self._buckets[client_ip].append(now)
        return await call_next(request)


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Validate SPARK_API_KEY header on non-health endpoints."""

    def __init__(self, app, api_key: str = ""):
        super().__init__(app)
        self.api_key = api_key

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not self.api_key:
            return await call_next(request)

        if request.url.path in _HEALTH_PATHS:
            return await call_next(request)

        if request.url.path.startswith("/output/"):
            return await call_next(request)

        key = request.headers.get("x-api-key", "")
        if key != self.api_key:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key."},
            )

        return await call_next(request)


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests exceeding max body size."""

    def __init__(self, app, max_bytes: int = 10 * 1024 * 1024):
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_bytes:
            return JSONResponse(
                status_code=413,
                content={"detail": f"Request body too large. Max: {self.max_bytes} bytes."},
            )

        return await call_next(request)
