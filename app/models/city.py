from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base, BaseEntity


class CityModel(Base, BaseEntity):
    __tablename__ = "cities"
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
