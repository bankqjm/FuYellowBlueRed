from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.models.models import PlatformConfig, ConfigKey

DEFAULT_CONFIGS = {
    ConfigKey.SHOP_COMMISSION_RATE.value: "0.10",
    ConfigKey.RIDER_SERVICE_FEE_RATE.value: "0.20",
    ConfigKey.MIN_WITHDRAWAL_AMOUNT.value: "10.0",
    ConfigKey.PLATFORM_NAME.value: "FuYellowBlueRed",
    ConfigKey.PLATFORM_CONTACT.value: "400-888-8888",
}


class ConfigService:

    @staticmethod
    async def get_config(db: AsyncSession, key: str) -> Optional[str]:
        result = await db.execute(
            select(PlatformConfig).where(PlatformConfig.key == key)
        )
        config = result.scalar_one_or_none()
        if config:
            return config.value
        return DEFAULT_CONFIGS.get(key)

    @staticmethod
    async def get_config_float(db: AsyncSession, key: str, default: float = 0.0) -> float:
        value = await ConfigService.get_config(db, key)
        if value:
            try:
                return float(value)
            except ValueError:
                pass
        return default

    @staticmethod
    async def set_config(db: AsyncSession, key: str, value: str, description: str = None) -> PlatformConfig:
        result = await db.execute(
            select(PlatformConfig).where(PlatformConfig.key == key)
        )
        config = result.scalar_one_or_none()
        if config:
            config.value = value
            if description:
                config.description = description
        else:
            config = PlatformConfig(key=key, value=value, description=description)
            db.add(config)
        await db.flush()
        return config

    @staticmethod
    async def get_all_configs(db: AsyncSession) -> dict:
        result = await db.execute(select(PlatformConfig))
        configs = result.scalars().all()
        all_configs = dict(DEFAULT_CONFIGS)
        for config in configs:
            all_configs[config.key] = config.value
        return all_configs

    @staticmethod
    async def init_default_configs(db: AsyncSession):
        for key, value in DEFAULT_CONFIGS.items():
            result = await db.execute(
                select(PlatformConfig).where(PlatformConfig.key == key)
            )
            config = result.scalar_one_or_none()
            if not config:
                config = PlatformConfig(key=key, value=value)
                db.add(config)
        await db.flush()
