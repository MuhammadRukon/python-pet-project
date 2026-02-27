from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base, BaseEntity


class UserModel(Base, BaseEntity):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(nullable=False)
    is_verified: Mapped[bool] = mapped_column(nullable=False, default=False)
