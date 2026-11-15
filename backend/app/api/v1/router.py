from fastapi import APIRouter
from app.api.v1.endpoints import tutors, pets, services, appointments, chat, alerts, health_records

api_router = APIRouter()

api_router.include_router(tutors.router, prefix="/tutors", tags=["Tutores"])
api_router.include_router(pets.router, prefix="/pets", tags=["Pets"])
api_router.include_router(services.router, prefix="/services", tags=["Serviços"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["Agendamentos"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chatbot IA"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alertas Preditivos"])
api_router.include_router(health_records.router, prefix="/health-records", tags=["Prontuário & Vacinas"])
