from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.models import User, Wallet
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserInfo, UpdateUserRequest
from app.schemas.base import ResponseSchema
from app.utils.auth import hash_password, verify_password, create_access_token
from app.utils.exceptions import BadRequestException, UnauthorizedException
from app.deps.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=ResponseSchema[UserInfo])
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.phone == request.phone))
    existing_user = result.scalar_one_or_none()

    if existing_user:
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

    return ResponseSchema(
        code=0,
        message="注册成功",
        data=UserInfo.model_validate(user),
    )


@router.post("/login", response_model=ResponseSchema[TokenResponse])
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.phone == request.phone))
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.password_hash):
        raise BadRequestException("手机号或密码错误")

    if user.status == 0:
        raise UnauthorizedException("账号已被禁用")

    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )

    return ResponseSchema(
        code=0,
        message="登录成功",
        data=TokenResponse(
            access_token=access_token,
            user_id=user.id,
            role=user.role,
            nickname=user.nickname,
            avatar=user.avatar,
        ),
    )
