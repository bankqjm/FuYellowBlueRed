from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.models import User
from app.schemas.base import ResponseSchema
from app.deps.auth import get_current_user
from app.core import ForbiddenException, BadRequestException, get_logger
from app.services.config import ConfigService, DEFAULT_CONFIGS

router = APIRouter(prefix="/admin/config", tags=["平台配置"])
logger = get_logger("config")


@router.get("", response_model=ResponseSchema[dict])
async def get_all_configs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "ADMIN":
        raise ForbiddenException("仅管理员可访问")

    configs = await ConfigService.get_all_configs(db)
    config_list = []
    for key, value in configs.items():
        config_list.append({
            "key": key,
            "value": value,
            "description": _get_config_description(key),
        })

    return ResponseSchema(code=0, data={
        "configs": config_list,
        "defaults": DEFAULT_CONFIGS,
    })


@router.get("/{key}", response_model=ResponseSchema[dict])
async def get_config(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "ADMIN":
        raise ForbiddenException("仅管理员可访问")

    value = await ConfigService.get_config(db, key)
    if value is None:
        raise BadRequestException(f"配置项 {key} 不存在")

    return ResponseSchema(code=0, data={
        "key": key,
        "value": value,
        "description": _get_config_description(key),
    })


@router.put("/{key}", response_model=ResponseSchema[dict])
async def update_config(
    key: str,
    value: str = Body(..., embed=True),
    description: str = Body(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "ADMIN":
        raise ForbiddenException("仅管理员可访问")

    valid_keys = list(DEFAULT_CONFIGS.keys())
    if key not in valid_keys:
        raise BadRequestException(f"无效的配置项: {key}")

    if key in ["SHOP_COMMISSION_RATE", "RIDER_SERVICE_FEE_RATE"]:
        try:
            rate = float(value)
            if not 0 <= rate <= 1:
                raise ValueError()
        except ValueError:
            raise BadRequestException("费率必须是0到1之间的数字")

    await ConfigService.set_config(db, key, value, description)
    await db.commit()

    logger.info(f"Config updated: {key} = {value}")

    return ResponseSchema(code=0, message="配置更新成功", data={
        "key": key,
        "value": value,
    })


def _get_config_description(key: str) -> str:
    descriptions = {
        "SHOP_COMMISSION_RATE": "商家抽成比例（商品金额）",
        "RIDER_SERVICE_FEE_RATE": "骑手服务费比例（配送费）",
        "MIN_WITHDRAWAL_AMOUNT": "最低提现金额",
        "PLATFORM_NAME": "平台名称",
        "PLATFORM_CONTACT": "平台联系方式",
    }
    return descriptions.get(key, "")
