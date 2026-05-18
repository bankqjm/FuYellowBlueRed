from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.upload import router as upload_router
from app.api.v1.shop import router as shop_router
from app.api.v1.admin import router as admin_router
from app.api.v1.orders import router as orders_router
from app.api.v1.rider import router as rider_router
from app.api.v1.review import router as review_router
from app.api.v1.wallet import router as wallet_router
from app.api.v1.earnings import router as earnings_router
from app.api.v1.config import router as config_router
from app.api.v1.favorites import router as favorites_router
from app.api.v1.coupons import router as coupons_router

__all__ = [
    "auth_router",
    "users_router",
    "upload_router",
    "shop_router",
    "admin_router",
    "orders_router",
    "rider_router",
    "review_router",
    "wallet_router",
    "earnings_router",
    "config_router",
    "favorites_router",
    "coupons_router",
]
