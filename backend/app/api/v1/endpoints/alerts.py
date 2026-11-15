import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.alert import (
    AlertResponse,
    AlertUpdateStatus,
    AlertScanResult
)
from app.services import alert_service
from app.agents.alert_agent import predictive_alert_agent

router = APIRouter()


@router.get(
    "/",
    response_model=List[AlertResponse],
    summary="Listar alertas inteligentes",
    description="Retorna alertas gerados pelo motor preditivo de IA, com filtros por status, tutor, pet ou tipo."
)
async def list_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None, description="pending, sent, clicked, dismissed"),
    tutor_id: Optional[uuid.UUID] = Query(None, description="Filtrar por tutor"),
    pet_id: Optional[uuid.UUID] = Query(None, description="Filtrar por pet"),
    alert_type: Optional[str] = Query(None, description="Filtrar por tipo: vaccine_due, bath_recurrence, etc."),
    db: AsyncSession = Depends(get_db)
):
    return await alert_service.list_alerts(
        db,
        skip=skip,
        limit=limit,
        status=status,
        tutor_id=tutor_id,
        pet_id=pet_id,
        alert_type=alert_type
    )


@router.post(
    "/run-scan",
    response_model=AlertScanResult,
    summary="Executar varredura preditiva de alertas",
    description="Dispara manualmente a análise preditiva do agente de IA sobre todos os pets, detectando vacinas a vencer e recorrência de banho/tosa."
)
async def run_predictive_scan(
    db: AsyncSession = Depends(get_db)
):
    result = await predictive_alert_agent.scan_and_generate_alerts(db)
    return AlertScanResult(
        total_pets_analyzed=result["total_pets_analyzed"],
        alerts_generated=result["alerts_generated"],
        alerts=result["alerts"]
    )


@router.post(
    "/run-vaccine-scan",
    response_model=AlertScanResult,
    summary="Varredura de Alertas de Vacinação (CFMV D-30, D-7, D-0 e Atrasadas)",
    description="Executa o motor de verificação de vacinas da caderneta digital, disparando alertas de reforço para tutores."
)
async def run_vaccine_scan(
    db: AsyncSession = Depends(get_db)
):
    result = await predictive_alert_agent.scan_vaccine_reminders(db)
    return AlertScanResult(
        total_pets_analyzed=result["total_records_analyzed"],
        alerts_generated=result["alerts_generated"],
        alerts=result["alerts"]
    )


@router.patch(
    "/{alert_id}/status",
    response_model=AlertResponse,
    summary="Atualizar status do alerta",
    description="Marca o alerta como enviado ('sent'), clicado ('clicked') ou dispensado ('dismissed')."
)
async def update_alert_status(
    alert_id: uuid.UUID,
    status_in: AlertUpdateStatus,
    db: AsyncSession = Depends(get_db)
):
    alert = await alert_service.get_alert(db, alert_id, load_relations=False)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta não encontrado."
        )
    return await alert_service.update_alert_status(db, alert, status_in.status)

