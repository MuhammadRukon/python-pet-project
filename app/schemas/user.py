from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    name: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_verified: bool
