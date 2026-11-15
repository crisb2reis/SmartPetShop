from fastapi import APIRouter
from app.api.v1.endpoints import tutors, pets, services, appointments

api_router = APIRouter()

api_router.include_router(tutors.router, prefix="/tutors", tags=["Tutores"])
api_router.include_router(pets.router, prefix="/pets", tags=["Pets"])
api_router.include_router(services.router, prefix="/services", tags=["Serviços"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["Agendamentos"])
