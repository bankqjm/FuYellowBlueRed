from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.models import User
from app.schemas.auth import UserInfo, UpdateUserRequest
from app.schemas.base import ResponseSchema
from app.deps.auth import get_current_user

router = APIRouter(prefix="/users", tags=["用户"])


@router.get("/me", response_model=ResponseSchema[UserInfo])
async def get_me(current_user: User = Depends(get_current_user)):
    return ResponseSchema(
        code=0,
        message="success",
        data=UserInfo.model_validate(current_user),
    )


@router.put("/me", response_model=ResponseSchema[UserInfo])
async def update_me(
    request: UpdateUserRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if request.nickname is not None:
        current_user.nickname = request.nickname
    if request.avatar is not None:
        current_user.avatar = request.avatar

    await db.commit()
    await db.refresh(current_user)

    return ResponseSchema(
        code=0,
        message="更新成功",
        data=UserInfo.model_validate(current_user),
    )
