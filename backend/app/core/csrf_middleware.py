"""CSRF protection middleware using Double Submit Cookie pattern.

For mutating requests (POST, PUT, DELETE, PATCH), the middleware verifies
that the csrf_token cookie value matches the X-CSRF-Token header value.
GET, HEAD, and OPTIONS requests are skipped.
WebSocket connections are also skipped.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.core.logger import get_logger
from app.config import settings

logger = get_logger("csrf")

# HTTP methods that are safe (idempotent, no side effects)
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


class CSRFMiddleware(BaseHTTPMiddleware):
    """Double Submit Cookie CSRF protection middleware.

    - Skips safe methods (GET, HEAD, OPTIONS)
    - Skips WebSocket upgrade requests
    - Skips in DEBUG mode (development convenience)
    - Compares csrf_token cookie with X-CSRF-Token header on mutating requests
    """

    async def dispatch(self, request: Request, call_next):
        # Skip safe methods
        if request.method in SAFE_METHODS:
            return await call_next(request)

        # Skip WebSocket upgrade requests
        if request.headers.get("upgrade", "").lower() == "websocket":
            return await call_next(request)

        # Skip in DEBUG mode for development convenience
        if settings.DEBUG:
            return await call_next(request)

        # Double Submit Cookie check
        cookie_token = request.cookies.get("csrf_token")
        header_token = request.headers.get("X-CSRF-Token")

        if not cookie_token or not header_token:
            logger.warning(
                f"CSRF validation failed: missing token. "
                f"cookie={'present' if cookie_token else 'missing'}, "
                f"header={'present' if header_token else 'missing'}, "
                f"path={request.url.path}"
            )
            return JSONResponse(
                status_code=403,
                content={"code": 403, "error_code": "CSRF_FAILED", "message": "CSRF验证失败"},
            )

        if cookie_token != header_token:
            logger.warning(
                f"CSRF validation failed: token mismatch. "
                f"path={request.url.path}"
            )
            return JSONResponse(
                status_code=403,
                content={"code": 403, "error_code": "CSRF_FAILED", "message": "CSRF验证失败"},
            )

        return await call_next(request)
