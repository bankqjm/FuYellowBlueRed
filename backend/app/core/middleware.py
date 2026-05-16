import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logger import get_logger

logger = get_logger("http")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        request_id = request.headers.get("X-Request-ID", f"{int(start_time * 1000)}")

        logger.info(
            f"Request started | "
            f"id={request_id} | "
            f"method={request.method} | "
            f"path={request.url.path} | "
            f"client={request.client.host if request.client else 'unknown'}"
        )

        try:
            response = await call_next(request)

            process_time = (time.time() - start_time) * 1000

            logger.info(
                f"Request completed | "
                f"id={request_id} | "
                f"method={request.method} | "
                f"path={request.url.path} | "
                f"status={response.status_code} | "
                f"time={process_time:.2f}ms"
            )

            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.2f}ms"

            return response

        except Exception as e:
            process_time = (time.time() - start_time) * 1000

            logger.error(
                f"Request failed | "
                f"id={request_id} | "
                f"method={request.method} | "
                f"path={request.url.path} | "
                f"error={str(e)} | "
                f"time={process_time:.2f}ms"
            )
            raise
