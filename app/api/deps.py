from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.core import get_token_payload
from app.db import session
from app.models import UserModel


def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()


DB = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DB, payload: Annotated[dict, Depends(get_token_payload)]
) -> UserModel:
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


current_user = Annotated[str, Depends(get_current_user)]
