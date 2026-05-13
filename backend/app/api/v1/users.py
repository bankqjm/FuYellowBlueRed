from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.models import User, UserAddress
from app.schemas.auth import UserInfo, UpdateUserRequest
from app.schemas.address import AddressCreate, AddressUpdate, AddressResponse
from app.schemas.base import ResponseSchema
from app.deps.auth import get_current_user
from app.core import BadRequestException, get_logger

router = APIRouter(prefix="/users", tags=["用户"])
logger = get_logger("users")


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


@router.get("/addresses", response_model=ResponseSchema[list[AddressResponse]])
async def get_addresses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserAddress).where(UserAddress.user_id == current_user.id)
    )
    addresses = result.scalars().all()
    return ResponseSchema(
        code=0,
        data=[AddressResponse.model_validate(a) for a in addresses],
    )


@router.post("/addresses", response_model=ResponseSchema[AddressResponse])
async def create_address(
    request: AddressCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if request.is_default:
        result = await db.execute(
            select(UserAddress).where(
                UserAddress.user_id == current_user.id,
                UserAddress.is_default == 1,
            )
        )
        existing_default = result.scalars().first()
        if existing_default:
            existing_default.is_default = 0

    address = UserAddress(
        user_id=current_user.id,
        **request.model_dump(),
    )
    db.add(address)
    await db.commit()
    await db.refresh(address)

    return ResponseSchema(
        code=0,
        message="创建成功",
        data=AddressResponse.model_validate(address),
    )


@router.put("/addresses/{address_id}", response_model=ResponseSchema[AddressResponse])
async def update_address(
    address_id: int,
    request: AddressUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserAddress).where(
            UserAddress.id == address_id,
            UserAddress.user_id == current_user.id,
        )
    )
    address = result.scalar_one_or_none()
    if not address:
        raise BadRequestException("地址不存在")

    if request.is_default:
        result = await db.execute(
            select(UserAddress).where(
                UserAddress.user_id == current_user.id,
                UserAddress.is_default == 1,
                UserAddress.id != address_id,
            )
        )
        existing_default = result.scalars().first()
        if existing_default:
            existing_default.is_default = 0

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(address, field, value)

    await db.commit()
    await db.refresh(address)

    return ResponseSchema(
        code=0,
        message="更新成功",
        data=AddressResponse.model_validate(address),
    )


@router.delete("/addresses/{address_id}", response_model=ResponseSchema)
async def delete_address(
    address_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserAddress).where(
            UserAddress.id == address_id,
            UserAddress.user_id == current_user.id,
        )
    )
    address = result.scalar_one_or_none()
    if not address:
        raise BadRequestException("地址不存在")

    await db.delete(address)
    await db.commit()

    return ResponseSchema(code=0, message="删除成功")
