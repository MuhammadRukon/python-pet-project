from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from config import settings
from models import TokenPayload

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS


def get_password_hash(password: str) -> str:
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password_bytes, salt)

    return password_hash.decode("utf-8")


def verify_password(plain_password: str, hash_password: str) -> bool:
    password_bytes = plain_password.encode("utf-8")
    hash_bytes = hash_password.encode("utf-8")

    return bcrypt.checkpw(password_bytes, hash_bytes)


def create_access_token(
    data: TokenPayload, expires_delta: timedelta | None = None
) -> str:
    to_encode = data.model_dump()
    duration = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    if expires_delta:
        duration = expires_delta

    expire = datetime.now(timezone.utc) + duration

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def create_refresh_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {"sub": subject, "type": "refresh", "exp": expire}

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt
