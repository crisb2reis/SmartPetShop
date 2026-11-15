from fastapi import APIRouter
from app.api.v1.endpoints import tutors, pets

api_router = APIRouter()

api_router.include_router(tutors.router, prefix="/tutors", tags=["Tutores"])
api_router.include_router(pets.router, prefix="/pets", tags=["Pets"])
