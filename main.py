from datetime import timedelta
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import engine, session
from database_models import Base, UserModel
from models import TokenPayload, UserCreate, UserLogin, UserRead
from security import (
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


# Dependency to get a DB session per request
def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "server is running"}


DB = Annotated[Session, Depends(get_db)]


@app.get("/users")
def get_users(db: DB):
    users = db.query(UserModel).all()
    return users


@app.get("/users/{id}")
def get_single_user(id: int, db: DB):
    user = db.query(UserModel).get(id)
    if user is None:
        return {"error": "user not found"}
    return user


# Auth related api
@app.post("/auth/register", response_model=UserRead)
def register(payload: UserCreate, db: DB):

    exists = db.query(UserModel).filter(UserModel.email == payload.email).first()

    if exists:
        raise HTTPException(status_code=400, detail="User already exists")

    hash = get_password_hash(payload.password)

    user_dict = payload.model_dump(exclude={"password"})
    user_dict["password_hash"] = hash

    user = UserModel(**user_dict)
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@app.post("/auth/login")
def login(payload: UserLogin, db: DB, response: Response):
    user = db.query(UserModel).filter(UserModel.email == payload.email).first()

    if not user:
        raise HTTPException(status_code=400, detail="user does not exist")

    is_match = verify_password(payload.password, user.password_hash)

    if not is_match:
        raise HTTPException(status_code=401, detail="Invalid password")

    token_payload = TokenPayload(sub=str(user.id))

    access_token = create_access_token(
        data=token_payload, expires_delta=timedelta(minutes=15)
    )
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
