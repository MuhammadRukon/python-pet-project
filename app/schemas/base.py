import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BaseEntity(BaseModel):
    # allows pydantic to read SQLAlchemy objects instead of just dictionaries.
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
