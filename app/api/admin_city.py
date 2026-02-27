from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import DB
from app.models import CityModel
from app.schemas import CityCreate, CityReadAdmin

router = APIRouter()


@router.get("", response_model=list[CityReadAdmin])
def list_all_cities_for_admin(db: DB):

    result = db.execute(select(CityModel))
    cities = result.scalars().all()
    return cities


@router.post("")
def create_city(payload: CityCreate, db: DB):

    city = CityModel(**payload.model_dump())

    db.add(city)
    db.commit()
    db.refresh(city)

    return city
