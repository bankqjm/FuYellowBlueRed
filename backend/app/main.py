from fastapi import FastAPI, Request, status, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
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
    payment_router,
)
from app.core import BaseAPIException, RequestLoggingMiddleware, get_logger
from app.core.security_middleware import SecurityHeadersMiddleware
from app.core.csrf_middleware import CSRFMiddleware
from app.core.metrics import ACTIVE_WEBSOCKET_CONNECTIONS
from app.core.websocket_manager import websocket_manager
from app.database import AsyncSessionLocal
from app.services.config import ConfigService
from app.tasks import run_order_timeout_task
from app.utils.redis_client import redis_client
from app.utils.auth import verify_token, is_token_valid
from prometheus_fastapi_instrumentator import Instrumentator

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

limiter = Limiter(key_func=get_remote_address)
logger = get_logger("app")


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

Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    excluded_handlers=["/health", "/metrics"],
).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

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
app.add_middleware(CSRFMiddleware)


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
    await websocket_manager.send_to_channel(channel, message)


async def send_to_user(user_id: int, message: dict):
    await websocket_manager.send_to_user(user_id, message)


@app.websocket("/ws/{channel}/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    channel: str,
    user_id: str,
    token: str = Query(default=None),
):
    # SEC-REFORM-03: JWT authentication for WebSocket
    if not token:
        await websocket.accept()
        await websocket.close(code=4001, reason="Unauthorized")
        logger.warning(f"WebSocket connection rejected: no token, channel={channel}, user_id={user_id}")
        return

    payload = verify_token(token)
    if not payload:
        await websocket.accept()
        await websocket.close(code=4001, reason="Unauthorized")
        logger.warning(f"WebSocket connection rejected: invalid token, channel={channel}, user_id={user_id}")
        return

    if not await is_token_valid(token):
        await websocket.accept()
        await websocket.close(code=4001, reason="Unauthorized")
        logger.warning(f"WebSocket connection rejected: token expired/revoked, channel={channel}, user_id={user_id}")
        return

    token_type = payload.get("type")
    if token_type != "access":
        await websocket.accept()
        await websocket.close(code=4001, reason="Unauthorized")
        logger.warning(f"WebSocket connection rejected: not access token, channel={channel}, user_id={user_id}")
        return

    token_user_id = payload.get("sub")
    if str(token_user_id) != str(user_id):
        await websocket.accept()
        await websocket.close(code=4001, reason="Unauthorized")
        logger.warning(
            f"WebSocket connection rejected: user_id mismatch, "
            f"token_user_id={token_user_id}, url_user_id={user_id}, channel={channel}"
        )
        return

    await websocket.accept()
    int_user_id = int(user_id)
    await websocket_manager.connect(websocket, int_user_id, channel)
    ACTIVE_WEBSOCKET_CONNECTIONS.inc()

    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                message["user_id"] = user_id
                message["channel"] = channel
                if "target_user_id" in message:
                    target_user_id = int(message["target_user_id"])
                    await websocket_manager.send_to_user(target_user_id, message)
                else:
                    await websocket_manager.send_to_channel(channel, message)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON message from user {user_id}, channel {channel}")
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
        ACTIVE_WEBSOCKET_CONNECTIONS.dec()
        logger.info(f"WebSocket disconnected: user_id={user_id}, channel={channel}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}, channel {channel}: {e}")
        websocket_manager.disconnect(websocket)
        ACTIVE_WEBSOCKET_CONNECTIONS.dec()


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
app.include_router(payment_router, prefix="/api/v1")

app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.get("/")
async def root():
    return {"message": "FuYellowBlueRed API", "version": "1.0.0"}


@app.get("/health")
async def health():
    redis_status = "connected" if redis_client._client else "disconnected"
    db_status = "ok"
    try:
        async with AsyncSessionLocal() as db:
            from sqlalchemy import text
            await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"
    return {
        "status": "ok",
        "redis": redis_status,
        "database": db_status,
        "version": "1.0.0",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
