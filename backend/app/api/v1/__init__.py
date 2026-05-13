from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.upload import router as upload_router
from app.api.v1.shop import router as shop_router
from app.api.v1.admin import router as admin_router
from app.api.v1.orders import router as orders_router
from app.api.v1.rider import router as rider_router
from app.api.v1.review import router as review_router

__all__ = [
    "auth_router",
    "users_router",
    "upload_router",
    "shop_router",
    "admin_router",
    "orders_router",
    "rider_router",
    "review_router",
]
