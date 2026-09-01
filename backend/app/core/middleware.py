import time
import logging
from collections import defaultdict
from typing import Dict, List
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.core.config import settings

logger = logging.getLogger("uvicorn.error")


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        # Store timestamps per IP per endpoint group: { f"{ip}:{endpoint_type}": [timestamp1, timestamp2, ...] }
        self.request_history: Dict[str, List[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        client_ip = request.client.host if request.client else "127.0.0.1"

        # Check X-Forwarded-For header if behind reverse proxy
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()

        now = time.time()
        window_seconds = 60.0

        # Determine rate limit threshold for request path
        max_requests = None
        limit_key = None

        if path.endswith("/api/auth/login") and request.method == "POST":
            max_requests = settings.RATE_LIMIT_LOGIN_PER_MINUTE
            limit_key = f"{client_ip}:login"
        elif "/api/face/recognize" in path and request.method == "POST":
            max_requests = settings.RATE_LIMIT_FACE_PER_MINUTE
            limit_key = f"{client_ip}:face"
        elif path.startswith("/api/reports") and request.method == "POST":
            max_requests = settings.RATE_LIMIT_REPORT_PER_MINUTE
            limit_key = f"{client_ip}:reports"

        if max_requests and limit_key:
            # Clean history outside 60-second window
            history = self.request_history[limit_key]
            recent_requests = [t for t in history if now - t < window_seconds]
            self.request_history[limit_key] = recent_requests

            if len(recent_requests) >= max_requests:
                logger.warning(
                    f"Rate limit exceeded for IP '{client_ip}' on endpoint '{path}' ({len(recent_requests)} requests in 60s)"
                )
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests. Please try again later."},
                    headers={"Retry-After": "60"},
                )

            # Record current request timestamp
            self.request_history[limit_key].append(now)

        return await call_next(request)
