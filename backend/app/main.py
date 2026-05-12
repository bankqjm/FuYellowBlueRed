from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
import os
import traceback

from app.config import settings
from app.database import init_db
from app.api import (
    auth_router,
    users_router,
    upload_router,
    shop_router,
    admin_router,
    orders_router,
    rider_router,
    review_router,
)
from app.core import BaseAPIException, RequestLoggingMiddleware, get_logger

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

limiter = Limiter(key_func=get_remote_address)
logger = get_logger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("Application started")
    yield
    logger.info("Application shutdown")


app = FastAPI(
    title="FuYellowBlueRed API",
    description="开源外卖配送平台 API",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLoggingMiddleware)


@app.exception_handler(BaseAPIException)
async def api_exception_handler(request: Request, exc: BaseAPIException):
    logger.warning(f"API Exception: {exc.error_code} - {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "error_code": exc.error_code,
            "message": exc.message,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": 500,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "服务器内部错误",
        },
    )


app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(upload_router, prefix="/api")
app.include_router(shop_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(orders_router, prefix="/api")
app.include_router(rider_router, prefix="/api")
app.include_router(review_router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "FuYellowBlueRed API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
