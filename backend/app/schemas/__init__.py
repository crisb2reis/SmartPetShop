from app.schemas.tutor import TutorCreate, TutorUpdate, TutorResponse, TutorWithPetsResponse
from app.schemas.pet import PetCreate, PetUpdate, PetResponse
from app.schemas.service import ServiceCreate, ServiceUpdate, ServiceResponse
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
    AvailableSlotsResponse
)

__all__ = [
    "TutorCreate",
    "TutorUpdate",
    "TutorResponse",
    "TutorWithPetsResponse",
    "PetCreate",
    "PetUpdate",
    "PetResponse",
    "ServiceCreate",
    "ServiceUpdate",
    "ServiceResponse",
    "AppointmentCreate",
    "AppointmentUpdate",
    "AppointmentResponse",
    "AvailableSlotsResponse",
]
