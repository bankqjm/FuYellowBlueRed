from fastapi import APIRouter, Depends, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from app.database import get_db
from app.models.models import User, Wallet
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserInfo
from app.schemas.base import ResponseSchema
from app.utils.auth import hash_password, verify_password, generate_tokens, logout_token, verify_token
from app.core import BadRequestException, UnauthorizedException, get_logger
from app.config import settings

router = APIRouter(prefix="/auth", tags=["认证"])
logger = get_logger("auth")

MAX_LOGIN_ATTEMPTS = 5
LOCK_DURATION_MINUTES = 15


@router.post("/register", response_model=ResponseSchema[UserInfo])
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    logger.info(f"Register request for phone: {mask_phone(request.phone)}")

    result = await db.execute(select(User).where(User.phone == request.phone))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        logger.warning(f"Phone already registered: {mask_phone(request.phone)}")
        raise BadRequestException("手机号已被注册")

    user = User(
        phone=request.phone,
        password_hash=hash_password(request.password),
        nickname=request.nickname or f"用户{request.phone[-4:]}",
        role=request.role,
        status=1,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    wallet = Wallet(user_id=user.id, balance=0.0, frozen_balance=0.0)
    db.add(wallet)
    await db.commit()

    logger.info(f"User registered successfully: {user.id}")
    return ResponseSchema(
        code=0,
        message="注册成功",
        data=UserInfo.model_validate(user),
    )


@router.post("/login", response_model=ResponseSchema[TokenResponse])
async def login(request: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    logger.info(f"Login request for phone: {mask_phone(request.phone)}")

    result = await db.execute(select(User).where(User.phone == request.phone))
    user = result.scalar_one_or_none()

    if not user:
        logger.warning(f"Login attempt for non-existent phone: {mask_phone(request.phone)}")
        raise BadRequestException("手机号或密码错误")

    if user.locked_until and user.locked_until > datetime.now():
        remaining = int((user.locked_until - datetime.now()).total_seconds() / 60)
        logger.warning(f"Locked account login attempt: {user.id}, remaining: {remaining}min")
        raise BadRequestException(f"账号已被锁定，请{remaining}分钟后再试")

    if user.locked_until and user.locked_until <= datetime.now():
        user.failed_login_count = 0
        user.locked_until = None

    if not verify_password(request.password, user.password_hash):
        user.failed_login_count = (user.failed_login_count or 0) + 1
        logger.warning(f"Invalid login attempt for user {user.id}, count: {user.failed_login_count}")

        if user.failed_login_count >= MAX_LOGIN_ATTEMPTS:
            user.locked_until = datetime.now() + timedelta(minutes=LOCK_DURATION_MINUTES)
            logger.warning(f"Account locked: {user.id}, until: {user.locked_until}")
            await db.commit()
            raise BadRequestException(f"登录失败次数过多，账号已被锁定{LOCK_DURATION_MINUTES}分钟")

        await db.commit()
        remaining_attempts = MAX_LOGIN_ATTEMPTS - user.failed_login_count
        raise BadRequestException(f"手机号或密码错误，还剩{remaining_attempts}次尝试机会")

    if user.status == 0:
        logger.warning(f"Disabled account login attempt: {user.id}")
        raise UnauthorizedException("账号已被禁用")

    user.failed_login_count = 0
    user.locked_until = None
    await db.commit()

    access_token, refresh_token = generate_tokens(user.id, user.role)

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )

    logger.info(f"User logged in successfully: {user.id}")
    return ResponseSchema(
        code=0,
        message="登录成功",
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user_id=user.id,
            role=user.role,
            nickname=user.nickname,
            avatar=user.avatar,
        ),
    )


@router.post("/refresh", response_model=ResponseSchema[TokenResponse])
async def refresh_token(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise UnauthorizedException("缺少refresh token")

    payload = verify_token(refresh_token)
    if not payload:
        raise UnauthorizedException("无效的refresh token")

    token_type = payload.get("type")
    if token_type != "refresh":
        raise UnauthorizedException("请使用refresh token")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("Token解析失败")

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if not user or user.status == 0:
        raise UnauthorizedException("用户不存在或账号已被禁用")

    access_token, new_refresh_token = generate_tokens(user.id, user.role)

    await logout_token(refresh_token)

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )

    logger.info(f"Token refreshed for user: {user.id}")
    return ResponseSchema(
        code=0,
        message="Token刷新成功",
        data=TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            user_id=user.id,
            role=user.role,
            nickname=user.nickname,
            avatar=user.avatar,
        ),
    )


@router.post("/logout", response_model=ResponseSchema[None])
async def logout(request: Request, response: Response):
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")

    if access_token:
        await logout_token(access_token)
    if refresh_token:
        await logout_token(refresh_token)

    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")

    logger.info("User logged out")
    return ResponseSchema(code=0, message="退出成功")


def mask_phone(phone: str) -> str:
    if len(phone) >= 11:
        return f"{phone[:3]}****{phone[7:]}"
    return phone