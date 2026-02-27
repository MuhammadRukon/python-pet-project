from pydantic import BaseModel, ConfigDict, EmailStr

from app.schemas import BaseEntity


class UserBase(BaseModel):
    name: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserRead(BaseEntity, UserBase):
    model_config = ConfigDict(from_attributes=True)
    is_verified: bool
