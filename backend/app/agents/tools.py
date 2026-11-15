import uuid
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import service_service, appointment_service, tutor_service, pet_service, vaccine_service
from app.schemas.appointment import AppointmentCreate


async def list_services_tool(
    db: AsyncSession,
    category: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retorna o catálogo de serviços ativos do Pet Shop (Banho, Tosa, Veterinário, Vacinação) com preços e durações.
    """
    services = await service_service.list_services(db, category=category, active_only=True)
    return [
        {
            "id": str(s.id),
            "name": s.name,
            "category": s.category,
            "price": float(s.price),
            "duration_minutes": s.duration_minutes,
            "description": s.description or ""
        }
        for s in services
    ]


async def check_availability_tool(
    db: AsyncSession,
    service_name: str,
    target_date: str
) -> Dict[str, Any]:
    """
    Verifica os horários disponíveis para agendamento de determinado serviço em uma data (formato YYYY-MM-DD).
    """
    service = await service_service.get_service_by_name(db, service_name)
    if not service:
        # Tentar busca aproximada
        all_services = await service_service.list_services(db, active_only=True)
        matched = [s for s in all_services if service_name.lower() in s.name.lower()]
        if matched:
            service = matched[0]
        else:
            return {"error": f"Serviço '{service_name}' não encontrado no catálogo."}

    try:
        t_date = date.fromisoformat(target_date)
    except ValueError:
        return {"error": f"Data inválida '{target_date}'. Utilize o formato YYYY-MM-DD."}

    slots = await appointment_service.get_available_slots(db, service, t_date)
    return {
        "service_name": service.name,
        "date": target_date,
        "duration_minutes": service.duration_minutes,
        "available_slots": slots,
        "message": f"Encontrados {len(slots)} horários disponíveis." if slots else "Não há horários livres nesta data."
    }


async def get_tutor_and_pets_tool(
    db: AsyncSession,
    tutor_phone: str
) -> Dict[str, Any]:
    """
    Busca o tutor e seus pets cadastrados a partir do número de telefone/WhatsApp.
    """
    cleaned_phone = "".join(filter(str.isdigit, tutor_phone))
    tutor = await tutor_service.get_tutor_by_phone(db, tutor_phone)
    if not tutor and cleaned_phone != tutor_phone:
        tutor = await tutor_service.get_tutor_by_phone(db, cleaned_phone)

    if not tutor:
        return {"status": "not_found", "message": f"Nenhum tutor encontrado com o telefone {tutor_phone}."}

    pets = await pet_service.list_pets(db, tutor_id=tutor.id)
    return {
        "status": "found",
        "tutor_id": str(tutor.id),
        "name": tutor.name,
        "phone": tutor.phone,
        "pets": [
            {
                "id": str(p.id),
                "name": p.name,
                "species": p.species,
                "breed": p.breed or "SRD"
            }
            for p in pets
        ]
    }


async def schedule_appointment_tool(
    db: AsyncSession,
    tutor_phone: str,
    pet_name: str,
    service_name: str,
    date_time_str: str,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Efetua o agendamento de um serviço para o pet de um tutor em determinada data e hora (formato ISO YYYY-MM-DDTHH:MM:SS ou YYYY-MM-DD HH:MM).
    """
    # 1. Identificar tutor e pet
    tutor = await tutor_service.get_tutor_by_phone(db, tutor_phone)
    if not tutor:
        return {"error": f"Tutor com telefone '{tutor_phone}' não foi encontrado. Cadastre o tutor antes de agendar."}

    pets = await pet_service.list_pets(db, tutor_id=tutor.id)
    matched_pet = next((p for p in pets if p.name.lower() == pet_name.lower()), None)
    if not matched_pet:
        pet_names = [p.name for p in pets]
        return {"error": f"Pet '{pet_name}' não encontrado para este tutor. Pets cadastrados: {pet_names}"}

    # 2. Identificar serviço
    service = await service_service.get_service_by_name(db, service_name)
    if not service:
        all_services = await service_service.list_services(db, active_only=True)
        matched = [s for s in all_services if service_name.lower() in s.name.lower()]
        if matched:
            service = matched[0]
        else:
            return {"error": f"Serviço '{service_name}' não encontrado no catálogo."}

    # 3. Converter data/hora
    clean_dt = date_time_str.replace(" ", "T")
    try:
        scheduled_at = datetime.fromisoformat(clean_dt)
    except ValueError:
        return {"error": f"Formato de data e hora inválido '{date_time_str}'. Utilize 'YYYY-MM-DDTHH:MM:SS'."}

    # 4. Validar conflito
    has_conflict = await appointment_service.check_conflicts(
        db,
        service_id=service.id,
        scheduled_at=scheduled_at
    )
    if has_conflict:
        return {"error": "Horário indisponível! Já existe outro agendamento neste mesmo período."}

    # 5. Criar agendamento
    appt_in = AppointmentCreate(
        pet_id=matched_pet.id,
        service_id=service.id,
        scheduled_at=scheduled_at,
        notes=notes or f"Agendado via Chatbot IA para {matched_pet.name}"
    )
    appointment = await appointment_service.create_appointment(db, appt_in)

    return {
        "status": "success",
        "appointment_id": str(appointment.id),
        "pet_name": matched_pet.name,
        "service_name": service.name,
        "price": float(service.price),
        "scheduled_at": appointment.scheduled_at.isoformat(),
        "message": f"Agendamento de {service.name} para {matched_pet.name} confirmado com sucesso para {appointment.scheduled_at.strftime('%d/%m/%Y às %H:%M')}!"
    }


async def get_pet_vaccination_card_tool(
    db: AsyncSession,
    tutor_phone: str,
    pet_name: str
) -> Dict[str, Any]:
    """
    Consulta o extrato oficial da carteirinha de vacinação digital de um pet (CFMV),
    incluindo doses aplicadas, próximas doses e vacinas atrasadas.
    """
    tutor = await tutor_service.get_tutor_by_phone(db, tutor_phone)
    if not tutor:
        cleaned_phone = "".join(filter(str.isdigit, tutor_phone))
        tutor = await tutor_service.get_tutor_by_phone(db, cleaned_phone)

    if not tutor:
        return {"error": f"Tutor com telefone '{tutor_phone}' não encontrado no cadastro."}

    pets = await pet_service.list_pets(db, tutor_id=tutor.id)
    matched_pet = next((p for p in pets if p.name.lower() == pet_name.lower()), None)
    if not matched_pet:
        pet_names = [p.name for p in pets]
        return {"error": f"Pet '{pet_name}' não encontrado para o tutor {tutor.name}. Pets cadastrados: {pet_names}"}

    card = await vaccine_service.get_pet_vaccination_card(db, matched_pet)
    records_summary = []
    for r in card["all_records"]:
        vac_name = r.vaccine_catalog.name if r.vaccine_catalog else "Vacina"
        batch_num = r.vaccine_batch.batch_number if r.vaccine_batch else "Lote N/A"
        records_summary.append({
            "vaccine_name": vac_name,
            "species": r.vaccine_catalog.species if r.vaccine_catalog else matched_pet.species,
            "application_date": r.application_date.strftime("%d/%m/%Y"),
            "next_due_date": r.next_due_date.strftime("%d/%m/%Y") if r.next_due_date else "Sem reforço programado",
            "status": r.status,
            "vet_name": r.vet_name,
            "vet_crmv": r.vet_crmv,
            "batch": batch_num
        })

    return {
        "pet_name": matched_pet.name,
        "species": matched_pet.species,
        "breed": matched_pet.breed or "SRD",
        "tutor_name": tutor.name,
        "total_applied": card["total_applied"],
        "due_soon_count": card["due_soon_count"],
        "overdue_count": card["overdue_count"],
        "records": records_summary,
        "has_overdue_vaccines": card["overdue_count"] > 0
    }


async def get_vaccine_catalog_tool(
    db: AsyncSession,
    species: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retorna o calendário e catálogo oficial de vacinas sanitárias para cães e gatos (CFMV),
    incluindo doses de primovacinação, idade recomendada e reforço anual.
    """
    catalogs = await vaccine_service.get_vaccine_catalogs(db, species=species)
    return {
        "vaccines": [
            {
                "name": c.name,
                "species": c.species,
                "type": c.type,
                "recommended_age_weeks": f"{c.recommended_age_weeks} semanas",
                "doses_required": f"{c.doses_required} dose(s)",
                "booster_interval": "Anual (365 dias)" if c.booster_interval_days == 365 else f"A cada {c.booster_interval_days} dias",
                "description": c.description or ""
            }
            for c in catalogs
        ]
    }

