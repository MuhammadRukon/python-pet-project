import uuid

from pydantic import BaseModel, ConfigDict

from app.schemas import BaseEntity


class CityBase(BaseModel):
    name: str


class CityCreate(CityBase):
    pass


class CityReadPublic(CityBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


class CityReadAdmin(BaseEntity, CityBase):
    is_active: bool
