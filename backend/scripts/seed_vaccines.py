#!/usr/bin/env python3
"""
Seed Data Script for Official Vaccine Calendars (Canines and Felines)
Compliant with CFMV (Conselho Federal de Medicina Veterinária) standards.
Idempotent: will not duplicate vaccines if already present.
"""

import asyncio
import os
import sys
import uuid
from datetime import date, timedelta

# Garante que o diretório raiz da app esteja no PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.organization import Organization
from app.models.pet import Pet
from app.models.vaccine import VaccineCatalog, VaccineBatch, PetVaccinationRecord


OFFICIAL_VACCINES = [
    # -----------------------------
    # CANINOS
    # -----------------------------
    {
        "species": "CANINO",
        "name": "Múltipla Canina (V10)",
        "type": "OBRIGATORIA",
        "recommended_age_weeks": 6,
        "doses_required": 3,
        "booster_interval_days": 365,
        "description": "Protege contra Cinomose, Parvovirose, Coronavirose, Hepatite Infecciosa, Adenovirose tipo 2, Parainfluenza e 4 sorovares de Leptospirose (Canicola, Icterohaemorrhagiae, Grippotyphosa, Pomona). Protocolo primário: 3 doses a cada 21-30 dias + Reforço Anual."
    },
    {
        "species": "CANINO",
        "name": "Múltipla Canina (V8)",
        "type": "OBRIGATORIA",
        "recommended_age_weeks": 6,
        "doses_required": 3,
        "booster_interval_days": 365,
        "description": "Protege contra Cinomose, Parvovirose, Hepatite Infecciosa Canina, Adenovirose tipo 2, Parainfluenza e Leptospirose (Canicola e Icterohaemorrhagiae). Protocolo primário: 3 doses a cada 21-30 dias + Reforço Anual."
    },
    {
        "species": "CANINO",
        "name": "Antirrábica Canina",
        "type": "OBRIGATORIA",
        "recommended_age_weeks": 12,
        "doses_required": 1,
        "booster_interval_days": 365,
        "description": "Imunização contra o vírus da Raiva (zoonose fatal com vacinação anual obrigatória por lei federal de zoonoses). Dose única a partir de 12 semanas + Reforço Anual."
    },
    {
        "species": "CANINO",
        "name": "Tosse dos Canis (Traqueobronquite)",
        "type": "OPCIONAL",
        "recommended_age_weeks": 8,
        "doses_required": 1,
        "booster_interval_days": 365,
        "description": "Protege contra Bordetella bronchiseptica e Parainfluenza canina (tosse dos canis). Altamente recomendada para cães que frequentam creche, banho & tosa, parques ou hotéis."
    },
    {
        "species": "CANINO",
        "name": "Giárdia Canina",
        "type": "OPCIONAL",
        "recommended_age_weeks": 8,
        "doses_required": 2,
        "booster_interval_days": 365,
        "description": "Prevenção da Giardíase. Reduz a gravidade dos sinais clínicos e a eliminação de cistos no ambiente. Protocolo inicial de 2 doses com intervalo de 21 dias + Reforço Anual."
    },
    {
        "species": "CANINO",
        "name": "Leishmaniose Visceral Canina",
        "type": "OPCIONAL",
        "recommended_age_weeks": 16,
        "doses_required": 3,
        "booster_interval_days": 365,
        "description": "Prevenção da Leishmaniose Visceral Canina em áreas endêmicas. Exige teste sorológico prévio negativo. Protocolo inicial de 3 doses com intervalo de 21 dias + Reforço Anual."
    },

    # -----------------------------
    # FELINOS
    # -----------------------------
    {
        "species": "FELINO",
        "name": "Tríplice Felina (V3)",
        "type": "OBRIGATORIA",
        "recommended_age_weeks": 8,
        "doses_required": 2,
        "booster_interval_days": 365,
        "description": "Protege contra Panleucopenia Felina, Rinotraqueíte (Herpesvírus) e Calicivirose Felina. Protocolo de filhote: 2 a 3 doses com intervalo de 21-30 dias + Reforço Anual."
    },
    {
        "species": "FELINO",
        "name": "Quádrupla Felina (V4)",
        "type": "OBRIGATORIA",
        "recommended_age_weeks": 8,
        "doses_required": 2,
        "booster_interval_days": 365,
        "description": "Protege contra Panleucopenia, Rinotraqueíte, Calicivirose e Clamidiose Felina. Protocolo primário de 2 doses + Reforço Anual."
    },
    {
        "species": "FELINO",
        "name": "Quíntupla Felina (V5 / FeLV)",
        "type": "OBRIGATORIA",
        "recommended_age_weeks": 8,
        "doses_required": 2,
        "booster_interval_days": 365,
        "description": "Protege contra Panleucopenia, Rinotraqueíte, Calicivirose, Clamidiose e o vírus da Leucemia Felina (FeLV). Exige teste sorológico prévio negativo. Protocolo de 2 doses + Reforço Anual."
    },
    {
        "species": "FELINO",
        "name": "Antirrábica Felina",
        "type": "OBRIGATORIA",
        "recommended_age_weeks": 12,
        "doses_required": 1,
        "booster_interval_days": 365,
        "description": "Imunização obrigatória contra o vírus da Raiva em gatos a partir de 12 semanas de vida + Reforço Anual."
    },
    {
        "species": "FELINO",
        "name": "Leucemia Felina (FeLV Recombinante)",
        "type": "OPCIONAL",
        "recommended_age_weeks": 8,
        "doses_required": 2,
        "booster_interval_days": 365,
        "description": "Imunização complementar contra o vírus da Leucemia Felina (FeLV) para animais de convívio livre ou ambiente com múltiplos gatos. 2 doses iniciais + Reforço Anual."
    }
]


async def seed_vaccines():
    print("🐾 Iniciando povoamento do Calendário Oficial de Vacinas (CFMV)...")
    async with AsyncSessionLocal() as db:
        # 1. Obter organização matriz
        org_res = await db.execute(select(Organization).limit(1))
        org = org_res.scalar_one_or_none()
        if not org:
            org = Organization(
                name="Pet Shop Patas & Pelos (Matriz)",
                cnpj="12.345.678/0001-90",
                plan="enterprise",
                active=True
            )
            db.add(org)
            await db.flush()

        # 2. Inserir Catálogo Oficial de Vacinas de forma idempotente
        inserted_count = 0
        catalog_map = {}

        for vac_data in OFFICIAL_VACCINES:
            existing_res = await db.execute(
                select(VaccineCatalog).where(
                    VaccineCatalog.name == vac_data["name"],
                    VaccineCatalog.species == vac_data["species"]
                )
            )
            existing = existing_res.scalar_one_or_none()

            if not existing:
                catalog_item = VaccineCatalog(
                    tenant_id=None,  # Global / Padrão Oficial do Sistema
                    species=vac_data["species"],
                    name=vac_data["name"],
                    type=vac_data["type"],
                    recommended_age_weeks=vac_data["recommended_age_weeks"],
                    doses_required=vac_data["doses_required"],
                    booster_interval_days=vac_data["booster_interval_days"],
                    description=vac_data["description"]
                )
                db.add(catalog_item)
                await db.flush()
                catalog_map[vac_data["name"]] = catalog_item
                inserted_count += 1
            else:
                catalog_map[vac_data["name"]] = existing

        print(f"✅ Catálogo de vacinas pronto: {len(catalog_map)} disponíveis ({inserted_count} novas inseridas).")

        # 3. Inserir Lotes de Vacinas (Estoque Ativo da Unidade)
        sample_batches = [
            {
                "vac_name": "Múltipla Canina (V10)",
                "batch_number": "V10-2026-08A",
                "manufacturer": "Zoetis Saúde Animal",
                "expiration_date": date.today() + timedelta(days=400)
            },
            {
                "vac_name": "Antirrábica Canina",
                "batch_number": "DEF-2026-11K",
                "manufacturer": "Boehringer Ingelheim",
                "expiration_date": date.today() + timedelta(days=365)
            },
            {
                "vac_name": "Quádrupla Felina (V4)",
                "batch_number": "FEL-2026-04M",
                "manufacturer": "MSD Saúde Animal",
                "expiration_date": date.today() + timedelta(days=300)
            },
            {
                "vac_name": "Tosse dos Canis (Traqueobronquite)",
                "batch_number": "BRON-2026-02Z",
                "manufacturer": "Zoetis Saúde Animal",
                "expiration_date": date.today() + timedelta(days=280)
            }
        ]

        batch_map = {}
        batch_inserted = 0
        for b_data in sample_batches:
            catalog_item = catalog_map.get(b_data["vac_name"])
            if not catalog_item:
                continue

            existing_b = await db.execute(
                select(VaccineBatch).where(
                    VaccineBatch.tenant_id == org.id,
                    VaccineBatch.batch_number == b_data["batch_number"]
                )
            )
            batch_obj = existing_b.scalar_one_or_none()

            if not batch_obj:
                batch_obj = VaccineBatch(
                    tenant_id=org.id,
                    vaccine_catalog_id=catalog_item.id,
                    batch_number=b_data["batch_number"],
                    manufacturer=b_data["manufacturer"],
                    expiration_date=b_data["expiration_date"],
                    active=True
                )
                db.add(batch_obj)
                await db.flush()
                batch_inserted += 1

            batch_map[b_data["vac_name"]] = batch_obj

        print(f"✅ Lotes de estoque registrados: {len(batch_map)} lotes ativos ({batch_inserted} novos).")

        # 4. Criar registros de vacinação de teste nos pets cadastrados
        # Bob (Canino) -> V10 aplicada recentemente (em dia)
        # Thor (Canino) -> Antirrábica a vencer em 15 dias (alerta próximo do vencimento)
        # Luna (Felino) -> V4 vencida há 20 dias (alerta de atrasada)
        pets_res = await db.execute(select(Pet).where(Pet.tenant_id == org.id))
        pets_list = {p.name: p for p in pets_res.scalars().all()}

        today = date.today()
        sample_records = []

        if "Bob" in pets_list and "Múltipla Canina (V10)" in catalog_map:
            v10_cat = catalog_map["Múltipla Canina (V10)"]
            v10_batch = batch_map.get("Múltipla Canina (V10)")
            sample_records.append({
                "pet": pets_list["Bob"],
                "catalog": v10_cat,
                "batch": v10_batch,
                "app_date": today - timedelta(days=60),
                "due_date": today + timedelta(days=305),
                "vet_name": "Dr. Roberto Alencar",
                "vet_crmv": "CRMV-SP 38412",
                "status": "APLICADA",
                "notes": "Animal hígido, aplicação subcutânea em região escapular direita. Sem reações adversas imediatas."
            })

        if "Thor" in pets_list and "Antirrábica Canina" in catalog_map:
            rab_cat = catalog_map["Antirrábica Canina"]
            rab_batch = batch_map.get("Antirrábica Canina")
            sample_records.append({
                "pet": pets_list["Thor"],
                "catalog": rab_cat,
                "batch": rab_batch,
                "app_date": today - timedelta(days=350),
                "due_date": today + timedelta(days=15), # Próxima do vencimento!
                "vet_name": "Dra. Camila Rocha",
                "vet_crmv": "CRMV-SP 42910",
                "status": "APLICADA",
                "notes": "Reforço anual obrigatório agendado para os próximos 15 dias."
            })

        if "Luna" in pets_list and "Quádrupla Felina (V4)" in catalog_map:
            v4_cat = catalog_map["Quádrupla Felina (V4)"]
            v4_batch = batch_map.get("Quádrupla Felina (V4)")
            sample_records.append({
                "pet": pets_list["Luna"],
                "catalog": v4_cat,
                "batch": v4_batch,
                "app_date": today - timedelta(days=385),
                "due_date": today - timedelta(days=20), # Vencida / atrasada!
                "vet_name": "Dr. Roberto Alencar",
                "vet_crmv": "CRMV-SP 38412",
                "status": "ATRASADA",
                "notes": "Dose de reforço atrasada em 20 dias. Tutor notificado para comparecer à clínica."
            })

        rec_inserted = 0
        for rec in sample_records:
            existing_rec = await db.execute(
                select(PetVaccinationRecord).where(
                    PetVaccinationRecord.pet_id == rec["pet"].id,
                    PetVaccinationRecord.vaccine_catalog_id == rec["catalog"].id
                )
            )
            if not existing_rec.scalar_one_or_none():
                new_rec = PetVaccinationRecord(
                    tenant_id=org.id,
                    pet_id=rec["pet"].id,
                    vaccine_catalog_id=rec["catalog"].id,
                    vaccine_batch_id=rec["batch"].id if rec["batch"] else None,
                    application_date=rec["app_date"],
                    next_due_date=rec["due_date"],
                    vet_name=rec["vet_name"],
                    vet_crmv=rec["vet_crmv"],
                    clinic_id=org.id,
                    status=rec["status"],
                    notes=rec["notes"]
                )
                db.add(new_rec)
                rec_inserted += 1

        await db.commit()
        print(f"🎉 Seed de Vacinas concluído com sucesso! {rec_inserted} registros vinculados aos pets.")


if __name__ == "__main__":
    asyncio.run(seed_vaccines())

