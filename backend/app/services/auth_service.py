from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import User, Wallet
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserInfo
from app.utils.auth import hash_password, verify_password, create_access_token
from app.core import BadRequestException, UnauthorizedException
from app.services.base import BaseService


class AuthService(BaseService):
    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def register(self, request: RegisterRequest) -> UserInfo:
        result = await self.db.execute(select(User).where(User.phone == request.phone))
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
        self.db.add(user)
        await self.commit()
        await self.refresh(user)

        wallet = Wallet(user_id=user.id, balance=0.0, frozen_balance=0.0)
        self.db.add(wallet)
        await self.commit()

        return UserInfo.model_validate(user)

    async def login(self, request: LoginRequest) -> TokenResponse:
        result = await self.db.execute(select(User).where(User.phone == request.phone))
        user = result.scalar_one_or_none()

        if not user or not verify_password(request.password, user.password_hash):
            raise BadRequestException("手机号或密码错误")

        if user.status == 0:
            raise UnauthorizedException("账号已被禁用")

        access_token = create_access_token(
            data={"sub": str(user.id), "role": user.role}
        )

        return TokenResponse(
            access_token=access_token,
            user_id=user.id,
            role=user.role,
            nickname=user.nickname,
            avatar=user.avatar,
        )
