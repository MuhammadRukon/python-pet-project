from fastapi import APIRouter, HTTPException, Response

from app.core import (
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_refresh_token,
    verify_password,
)
from app.crud import create_user, get_user_by_email
from app.schemas import TokenPayload, UserCreate, UserLogin, UserRead

router = APIRouter()


@router.post("/login")
def login(payload: UserLogin, response: Response):
    user = get_user_by_email(payload.email)

    if not user:
        raise HTTPException(status_code=400, detail="user does not exist")

    is_match = verify_password(payload.password, user.password_hash)

    if not is_match:
        raise HTTPException(status_code=401, detail="Invalid password")

    token_payload = TokenPayload(sub=str(user.id))
    # default time is 15 minutes
    access_token = create_access_token(data=token_payload)
    refresh_token = create_refresh_token(str(user.id))

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # set to True for HTTPS
        samesite="lax",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return {
        "access_token": access_token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "is_verified": user.is_verified,
        },
    }


# Auth related api
@router.post("/register", response_model=UserRead)
def register(payload: UserCreate):

    exists = get_user_by_email(payload.email)

    if exists:
        raise HTTPException(status_code=400, detail="User already exists")

    user = create_user(payload)
    return user
