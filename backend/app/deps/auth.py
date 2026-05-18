from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.database import get_db
from app.models.models import User
from app.utils.auth import verify_token, is_token_valid
from app.utils.exceptions import UnauthorizedException

ALGORITHM = "HS256"


async def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = request.cookies.get("access_token")
    if not token and authorization:
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                raise UnauthorizedException("认证格式错误")
        except ValueError:
            raise UnauthorizedException("认证格式错误")

    if not token:
        raise UnauthorizedException("缺少认证信息")

    if not await is_token_valid(token):
        raise UnauthorizedException("Token 已过期或无效")

    payload = verify_token(token)
    if not payload:
        raise UnauthorizedException("Token 解析失败")

    token_type = payload.get("type")
    if token_type != "access":
        raise UnauthorizedException("请使用access token")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("Token 解析失败")

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise UnauthorizedException("用户不存在")

    if user.status == 0:
        raise UnauthorizedException("账号已被禁用")

    return user


def require_role(*roles: str):
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise UnauthorizedException("权限不足")
        return current_user
    return role_checker


require_admin = require_role("ADMIN")