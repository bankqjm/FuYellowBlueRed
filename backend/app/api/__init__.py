from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.upload import router as upload_router
from app.api.shop import router as shop_router
from app.api.admin import router as admin_router
from app.api.orders import router as orders_router
from app.api.rider import router as rider_router
from app.api.review import router as review_router

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
