from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import DB
from app.models import CityModel
from app.schemas import CityCreate, CityReadAdmin, CityUpdate

router = APIRouter()


@router.get("", response_model=list[CityReadAdmin])
def list_all_cities_for_admin(db: DB):

    result = db.execute(select(CityModel))
    cities = result.scalars().all()
    return cities


# apply middleware to check access
@router.post("")
def create_city(payload: CityCreate, db: DB):

    city = CityModel(**payload.model_dump())

    db.add(city)
    db.commit()
    db.refresh(city)

    return city


@router.delete("/{id}")
def delete_city(id: str, db: DB):

    city = db.query(CityModel).filter(CityModel.id == id).first()

    if not city:
        return {"error": "City not found"}

    db.delete(city)
    db.commit()

    return {"message": f"Deleted city {id}"}


@router.patch("/{id}")
def update_city(payload: CityUpdate, id: str, db: DB):

    city = db.query(CityModel).filter(CityModel.id == id).first()

    if not city:
        raise HTTPException(status_code=400, detail="city not found")

    city.name = payload.name

    db.commit()
    db.refresh(city)

    return city
