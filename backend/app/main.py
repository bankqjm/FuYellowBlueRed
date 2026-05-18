from fastapi import FastAPI, Request, status, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
from collections import defaultdict
import os
import asyncio
import traceback
import json

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
    wallet_router,
    earnings_router,
    config_router,
    favorites_router,
    coupons_router,
    audit_router,
)
from app.core import BaseAPIException, RequestLoggingMiddleware, get_logger
from app.core.security_middleware import SecurityHeadersMiddleware
from app.database import AsyncSessionLocal
from app.services.config import ConfigService
from app.tasks import run_order_timeout_task
from app.utils.redis_client import redis_client

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

limiter = Limiter(key_func=get_remote_address)
logger = get_logger("app")

active_connections: dict[str, list[WebSocket]] = defaultdict(list)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with AsyncSessionLocal() as db:
        await ConfigService.init_default_configs(db)
        await db.commit()

    try:
        await redis_client.connect()
        logger.info("Redis connected successfully")
    except Exception as e:
        logger.warning(f"Redis connection failed, some features may be disabled: {e}")

    scheduler_task = asyncio.create_task(run_scheduler())

    yield

    scheduler_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        pass

    await redis_client.close()
    logger.info("Application shutdown")


async def run_scheduler():
    while True:
        try:
            async with AsyncSessionLocal() as db:
                await run_order_timeout_task(db)
            await asyncio.sleep(60)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            await asyncio.sleep(60)


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
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)


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


async def broadcast_message(channel: str, message: dict):
    message_str = json.dumps(message)
    for connection in active_connections.get(channel, []):
        try:
            await connection.send_text(message_str)
        except Exception as e:
            logger.error(f"Failed to send message to connection: {e}")


@app.websocket("/ws/{channel}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, channel: str, user_id: str):
    await websocket.accept()
    connection_key = f"{channel}:{user_id}"
    active_connections[channel].append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                message["user_id"] = user_id
                await broadcast_message(channel, message)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON message from {connection_key}")
    except WebSocketDisconnect:
        active_connections[channel].remove(websocket)
        logger.info(f"WebSocket disconnected: {connection_key}")
    except Exception as e:
        logger.error(f"WebSocket error for {connection_key}: {e}")
        if websocket in active_connections[channel]:
            active_connections[channel].remove(websocket)


app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(upload_router, prefix="/api/v1")
app.include_router(shop_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(orders_router, prefix="/api/v1")
app.include_router(rider_router, prefix="/api/v1")
app.include_router(review_router, prefix="/api/v1")
app.include_router(wallet_router, prefix="/api/v1")
app.include_router(earnings_router, prefix="/api/v1")
app.include_router(config_router, prefix="/api/v1")
app.include_router(favorites_router, prefix="/api/v1")
app.include_router(coupons_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "FuYellowBlueRed API", "version": "1.0.0"}


@app.get("/health")
async def health():
    redis_status = "connected" if redis_client._client else "disconnected"
    return {"status": "ok", "redis": redis_status}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)