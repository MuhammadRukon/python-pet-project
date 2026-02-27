from fastapi import APIRouter

from app.api import admin_city, auth, city

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

api_router.include_router(city.router, prefix="/cities", tags=["cities"])
api_router.include_router(admin_city.router, prefix="/admin/cities", tags=["cities"])
