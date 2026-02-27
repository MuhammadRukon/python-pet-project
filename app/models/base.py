import uuid
from datetime import datetime

from sqlalchemy import UUID, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# registry instance, keep it clean so tables dont inherit redundant member / row
class Base(DeclarativeBase):
    pass


# Template that is inherited for almost all tables
class BaseEntity:
    __abstract__ = True
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )
