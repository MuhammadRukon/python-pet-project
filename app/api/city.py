from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import DB
from app.models import CityModel
from app.schemas import CityReadPublic

router = APIRouter()


@router.get("", response_model=list[CityReadPublic])
def get_cities(db: DB):
    query = select(CityModel).where(CityModel.is_active)

    result = db.execute(query)
    cities = result.scalars().all()
    return cities
