from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import bcrypt
from jose import JWTError, jwt
from app.config import settings
from app.utils.redis_client import redis_client


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": now, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "iat": now, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


async def is_token_valid(token: str) -> bool:
    if await redis_client.is_blacklisted(token):
        return False
    payload = verify_token(token)
    if not payload:
        return False
    exp = payload.get("exp")
    if exp and datetime.fromtimestamp(exp, timezone.utc) < datetime.now(timezone.utc):
        return False
    return True


async def logout_token(token: str):
    payload = verify_token(token)
    if payload:
        exp = payload.get("exp")
        if exp:
            await redis_client.add_to_blacklist(token, exp)


def generate_tokens(user_id: int, role: str) -> Tuple[str, str]:
    access_token = create_access_token({"sub": str(user_id), "role": role})
    refresh_token = create_refresh_token({"sub": str(user_id), "role": role})
    return access_token, refresh_token