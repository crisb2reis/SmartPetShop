import os
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "smartpetshop_workers",
    broker=settings.redis_connection_url,
    backend=settings.redis_connection_url,
    include=["app.worker.whatsapp_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
)
