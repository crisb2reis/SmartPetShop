#!/usr/bin/env python3
"""
Seed Data Script for SmartPetShop
Populates sample Organization, Admin, Services, Tutors and Pets for testing.
"""

import asyncio
import os
import sys
import uuid
from decimal import Decimal
from datetime import date, datetime, timedelta

# Garante que o diretório raiz da app esteja no PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import AsyncSessionLocal
from app.core.auth import hash_password
from app.models.organization import Organization
from app.models.user import User
from app.models.service import Service
from app.models.tutor import Tutor
from app.models.pet import Pet
from app.models.health_record import HealthRecord
from app.models.appointment import Appointment


async def seed():
    print("Iniciando povoamento de dados de teste (Seed)...")
    async with AsyncSessionLocal() as db:
        # 1. Criar Organização (Pet Shop Matriz)
        org = Organization(
            name="Pet Shop Patas & Pelos (Matriz)",
            cnpj="12.345.678/0001-90",
            plan="enterprise",
            active=True
        )
        db.add(org)
        await db.flush()
        print(f"✅ Organização criada: {org.name} (ID: {org.id})")

        # 2. Criar Usuário Admin
        admin = User(
            tenant_id=org.id,
            name="Cristiano Reis",
            email="admin@smartpetshop.com",
            hashed_password=hash_password("admin123"),
            role="admin",
            active=True
        )
        db.add(admin)
        print(f"✅ Usuário Admin: {admin.email} (Senha: admin123)")

        # 3. Criar Catálogo de Serviços
        services = [
            Service(tenant_id=org.id, name="Banho & Hidratação", category="Banho", price=Decimal("60.00"), duration_minutes=45, active=True),
            Service(tenant_id=org.id, name="Tosa Completa na Tesoura", category="Tosa", price=Decimal("95.00"), duration_minutes=75, active=True),
            Service(tenant_id=org.id, name="Banho e Tosa Higiênica", category="Banho e Tosa", price=Decimal("110.00"), duration_minutes=90, active=True),
            Service(tenant_id=org.id, name="Consulta Veterinária Geral", category="Veterinário", price=Decimal("150.00"), duration_minutes=30, active=True),
            Service(tenant_id=org.id, name="Vacina V10 Polivalente", category="Vacinação", price=Decimal("85.00"), duration_minutes=20, active=True),
        ]
        db.add_all(services)
        await db.flush()
        print(f"✅ {len(services)} serviços adicionados ao catálogo.")

        # 4. Criar Tutores e Pets
        tutor1 = Tutor(
            tenant_id=org.id,
            name="Mariana Silva",
            phone="11998877665",
            email="mariana@gmail.com",
            address="Rua das Flores, 123 - Jardins"
        )
        tutor2 = Tutor(
            tenant_id=org.id,
            name="Carlos Eduardo",
            phone="11987654321",
            email="carlos@hotmail.com",
            address="Av. Paulista, 1000 - Apto 42"
        )
        db.add_all([tutor1, tutor2])
        await db.flush()

        pet1 = Pet(
            tenant_id=org.id,
            tutor_id=tutor1.id,
            name="Bob",
            species="Canino",
            breed="Golden Retriever",
            weight=32.5,
            birth_date=date(2021, 5, 10),
            medical_notes="Alergia a shampoo com perfume forte."
        )
        pet2 = Pet(
            tenant_id=org.id,
            tutor_id=tutor1.id,
            name="Luna",
            species="Felino",
            breed="Siamês",
            weight=4.2,
            birth_date=date(2022, 8, 15)
        )
        pet3 = Pet(
            tenant_id=org.id,
            tutor_id=tutor2.id,
            name="Thor",
            species="Canino",
            breed="Shih Tzu",
            weight=6.8,
            birth_date=date(2020, 2, 20)
        )
        db.add_all([pet1, pet2, pet3])
        await db.flush()
        print(f"✅ Tutores e Pets cadastrados (Bob, Luna, Thor).")

        # 5. Criar Prontuário com Vacina a Vencer (para testar o Agente de Alertas)
        vaccine_due = HealthRecord(
            tenant_id=org.id,
            pet_id=pet1.id,
            record_type="vaccine",
            title="Vacina Antirrábica Anual",
            application_date=date.today() - timedelta(days=360),
            next_due_date=date.today() + timedelta(days=5), # Vence em 5 dias!
            veterinarian_name="Dra. Camila",
            batch_number="VR-2025-99B"
        )
        db.add(vaccine_due)

        # 6. Criar Agendamento de Exemplo para Hoje
        now = datetime.utcnow()
        appt1 = Appointment(
            tenant_id=org.id,
            pet_id=pet1.id,
            service_id=services[0].id,
            scheduled_at=now.replace(hour=14, minute=0, second=0, microsecond=0),
            status="scheduled",
            notes="Trazer toalha própria"
        )
        appt2 = Appointment(
            tenant_id=org.id,
            pet_id=pet3.id,
            service_id=services[1].id,
            scheduled_at=now.replace(hour=16, minute=0, second=0, microsecond=0),
            status="in_progress",
            notes="Tosa baixa higiênica"
        )
        db.add_all([appt1, appt2])

        await db.commit()
        print("🎉 Banco de dados povoado com sucesso!")


if __name__ == "__main__":
    asyncio.run(seed())

