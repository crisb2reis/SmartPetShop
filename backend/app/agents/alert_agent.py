import uuid
import logging
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pet import Pet
from app.models.tutor import Tutor
from app.models.health_record import HealthRecord
from app.models.appointment import Appointment
from app.models.service import Service
from app.models.vaccine import PetVaccinationRecord, VaccineCatalog
from app.schemas.alert import AlertCreate, AlertResponse
from app.services import alert_service
from app.core.config import settings

logger = logging.getLogger("smartpetshop.alert_agent")


class PredictiveAlertAgent:
    """
    Agente de IA Preditivo para retenção de clientes e saúde dos pets:
    1. Detecta vacinas e vermífugos com vencimento em até 7 dias (ou recém-vencidos).
    2. Identifica ciclo médio de banho/tosa e sugere retorno para pets sem atendimento recente (> 15 dias).
    3. Gera mensagens personalizadas humanizadas para envio via WhatsApp ou push notification.
    """

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY

    async def scan_and_generate_alerts(self, db: AsyncSession) -> Dict[str, Any]:
        """Varre toda a base de pets e gera os alertas preventivos cabíveis."""
        # Carregar pets com tutores
        pets_query = select(Pet).options(selectinload(Pet.tutor))
        result = await db.execute(pets_query)
        pets = result.scalars().all()

        generated_alerts: List[Any] = []
        today = date.today()
        upcoming_threshold = today + timedelta(days=7)
        overdue_threshold = today - timedelta(days=15)

        for pet in pets:
            tutor = pet.tutor
            if not tutor:
                continue

            # ----------------------------------------------------
            # 1. Checagem de Vacinas e Prontuários (Health Records)
            # ----------------------------------------------------
            hr_query = select(HealthRecord).where(
                and_(
                    HealthRecord.pet_id == pet.id,
                    HealthRecord.next_due_date.isnot(None),
                    HealthRecord.next_due_date >= overdue_threshold,
                    HealthRecord.next_due_date <= upcoming_threshold
                )
            )
            hr_result = await db.execute(hr_query)
            due_records = hr_result.scalars().all()

            for hr in due_records:
                alert_type = f"{hr.record_type}_due"
                already_notified = await alert_service.has_recent_alert(
                    db,
                    pet_id=pet.id,
                    alert_type=alert_type,
                    days=7
                )
                if not already_notified:
                    due_str = hr.next_due_date.strftime("%d/%m")
                    is_overdue = hr.next_due_date < today
                    
                    if is_overdue:
                        msg = (
                            f"Atenção {tutor.name}! ⚠️ A dose de reforço da {hr.title} do {pet.name} "
                            f"venceu em {due_str}. A imunização contínua é fundamental para a saúde dele. "
                            f"Vamos agendar a vacinação com nosso veterinário?"
                        )
                    else:
                        msg = (
                            f"Olá {tutor.name}! 🐾 Passando para avisar que a {hr.title} do {pet.name} "
                            f"vence em {due_str}. Proteger quem você ama é nosso compromisso. "
                            f"Podemos agendar a aplicação para esta semana?"
                        )

                    new_alert = await alert_service.create_alert(
                        db,
                        AlertCreate(
                            tutor_id=tutor.id,
                            pet_id=pet.id,
                            alert_type=alert_type,
                            message=msg,
                            status="pending",
                            scheduled_for=datetime.utcnow()
                        )
                    )
                    generated_alerts.append(new_alert)

            # ----------------------------------------------------
            # 2. Checagem de Recorrência de Banho e Tosa
            # ----------------------------------------------------
            last_appt_query = (
                select(Appointment)
                .join(Service)
                .where(
                    and_(
                        Appointment.pet_id == pet.id,
                        Service.category.in_(["Banho", "Tosa"]),
                        Appointment.status.in_(["completed", "scheduled"])
                    )
                )
                .order_by(Appointment.scheduled_at.desc())
                .limit(1)
            )
            last_appt_res = await db.execute(last_appt_query)
            last_appt = last_appt_res.scalar_one_or_none()

            needs_bath_alert = False
            days_since = 0

            if last_appt:
                days_since = (datetime.utcnow() - last_appt.scheduled_at.replace(tzinfo=None)).days
                if days_since >= 15:
                    needs_bath_alert = True
            else:
                # Pet cadastrado há mais de 10 dias sem nenhum agendamento
                days_created = (datetime.utcnow() - pet.created_at.replace(tzinfo=None)).days
                if days_created >= 10:
                    needs_bath_alert = True
                    days_since = days_created

            if needs_bath_alert:
                already_alerted = await alert_service.has_recent_alert(
                    db,
                    pet_id=pet.id,
                    alert_type="bath_recurrence",
                    days=10
                )
                if not already_alerted:
                    msg = (
                        f"Oi {tutor.name}! 🛁 Já faz {days_since} dias desde a última visita do {pet.name}. "
                        f"Que tal reservar um horário de Banho e Tosa para deixá-lo limpinho, hidratado e cheiroso? "
                        f"Temos horários especiais disponíveis!"
                    )

                    new_alert = await alert_service.create_alert(
                        db,
                        AlertCreate(
                            tutor_id=tutor.id,
                            pet_id=pet.id,
                            alert_type="bath_recurrence",
                            message=msg,
                            status="pending",
                            scheduled_for=datetime.utcnow()
                        )
                    )
                    generated_alerts.append(new_alert)

        await db.commit()

        # Executa também a varredura oficial de vacinas CFMV
        vaccine_scan = await self.scan_vaccine_reminders(db)
        generated_alerts.extend(vaccine_scan.get("alerts", []))

        return {
            "total_pets_analyzed": len(pets),
            "alerts_generated": len(generated_alerts),
            "alerts": generated_alerts
        }

    async def scan_vaccine_reminders(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Varredura de vacinas oficial CFMV:
        Verifica registros em pet_vaccination_records para:
        - D-30: Aviso prévio de reforço (30 a 8 dias antes)
        - D-7:  Lembrete de agendamento (7 a 1 dias antes)
        - D-0:  Vencimento hoje
        - Atrasadas: Vacinas vencidas (dias < 0) -> marca como ATRASADA
        """
        query = (
            select(PetVaccinationRecord)
            .options(
                selectinload(PetVaccinationRecord.pet).selectinload(Pet.tutor),
                selectinload(PetVaccinationRecord.vaccine_catalog),
                selectinload(PetVaccinationRecord.vaccine_batch)
            )
            .where(PetVaccinationRecord.next_due_date.isnot(None))
        )
        result = await db.execute(query)
        records = result.scalars().all()

        today = date.today()
        generated: List[Any] = []

        for record in records:
            pet = record.pet
            if not pet or not pet.tutor:
                continue
            tutor = pet.tutor
            due_date = record.next_due_date
            if not due_date:
                continue

            days_remaining = (due_date - today).days
            due_str = due_date.strftime("%d/%m/%Y")
            vac_name = record.vaccine_catalog.name if record.vaccine_catalog else "Vacina"

            alert_type: Optional[str] = None
            msg: Optional[str] = None

            if days_remaining < 0:
                # Vacina atrasada / vencida
                alert_type = "vaccine_overdue"
                if record.status != "ATRASADA":
                    record.status = "ATRASADA"

                days_overdue = abs(days_remaining)
                msg = (
                    f"Atenção {tutor.name}! ⚠️ A vacina {vac_name} do {pet.name} está atrasada há {days_overdue} dia(s) (venceu em {due_str}). "
                    f"A imunização contínua é fundamental para protegê-lo contra zoonoses e viroses graves. "
                    f"Agende hoje mesmo o reforço no nosso consultório veterinário!"
                )
            elif days_remaining == 0:
                # D-0: Vence hoje!
                alert_type = "vaccine_d0"
                msg = (
                    f"Olá {tutor.name}! 🚨 Hoje ({due_str}) é o dia da dose de reforço da vacina {vac_name} do {pet.name}. "
                    f"Traga-o ao nosso pet shop para aplicação com o médico veterinário responsável!"
                )
            elif 1 <= days_remaining <= 7:
                # D-7: Lembrete de 7 dias
                alert_type = "vaccine_d7"
                msg = (
                    f"Olá {tutor.name}! 🐾 Lembrete: a vacina {vac_name} do {pet.name} vence em {days_remaining} dia(s) ({due_str}). "
                    f"Que tal já deixar o horário reservado para garantir a proteção dele?"
                )
            elif 8 <= days_remaining <= 30:
                # D-30: Aviso prévio de 30 dias
                alert_type = "vaccine_d30"
                msg = (
                    f"Oi {tutor.name}! 📋 Aviso prévio de vacinação: a dose de reforço da vacina {vac_name} do {pet.name} vence no próximo mês ({due_str}). "
                    f"Fique atento ao calendário para manter a caderneta digital sempre em dia!"
                )

            if alert_type and msg:
                already_sent = await alert_service.has_recent_alert(
                    db,
                    pet_id=pet.id,
                    alert_type=alert_type,
                    days=7
                )
                if not already_sent:
                    new_alert = await alert_service.create_alert(
                        db,
                        AlertCreate(
                            tutor_id=tutor.id,
                            pet_id=pet.id,
                            alert_type=alert_type,
                            message=msg,
                            status="pending",
                            scheduled_for=datetime.utcnow()
                        )
                    )
                    generated.append(new_alert)

        await db.commit()

        return {
            "total_records_analyzed": len(records),
            "alerts_generated": len(generated),
            "alerts": generated
        }


predictive_alert_agent = PredictiveAlertAgent()

