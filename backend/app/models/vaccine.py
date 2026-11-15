import uuid
from datetime import date
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Date, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import TimestampedModel

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.pet import Pet


class VaccineCatalog(TimestampedModel):
    """
    Catálogo Oficial de Vacinas para cães e gatos.
    Pode ser global (tenant_id=None) ou customizado por organização.
    Atende às normas do CFMV e controle de zoonoses.
    """
    __tablename__ = "vaccine_catalogs"

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    species: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True
    )  # CANINO, FELINO, AMBOS
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True
    )  # ex: V8, V10, Raiva, Giárdia, V3, V4, V5, Leishmaniose
    type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="OBRIGATORIA",
        index=True
    )  # OBRIGATORIA, OPCIONAL
    recommended_age_weeks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=8
    )  # Idade inicial recomendada em semanas
    doses_required: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1
    )  # Quantidade de doses no protocolo de primovacinação
    booster_interval_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=365
    )  # Intervalo de reforço periódico em dias (ex: 365 = anual)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relacionamentos
    batches: Mapped[List["VaccineBatch"]] = relationship(
        "VaccineBatch",
        back_populates="vaccine_catalog",
        cascade="all, delete-orphan"
    )
    vaccination_records: Mapped[List["PetVaccinationRecord"]] = relationship(
        "PetVaccinationRecord",
        back_populates="vaccine_catalog"
    )

    def __repr__(self) -> str:
        return f"<VaccineCatalog id={self.id} name='{self.name}' species='{self.species}'>"


class VaccineBatch(TimestampedModel):
    """
    Controle de Estoque e Rastreabilidade de Lotes de Vacinas.
    Exigência sanitária e regulamentar do CFMV para comprovação de procedência.
    """
    __tablename__ = "vaccine_batches"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    vaccine_catalog_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vaccine_catalogs.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    batch_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )  # Número do Lote impresso na ampola
    manufacturer: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )  # Fabricante (ex: Zoetis, Boehringer Ingelheim, MSD, Dechra)
    expiration_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True
    )  # Validade do lote
    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    # Relacionamentos
    vaccine_catalog: Mapped["VaccineCatalog"] = relationship(
        "VaccineCatalog",
        back_populates="batches"
    )
    vaccination_records: Mapped[List["PetVaccinationRecord"]] = relationship(
        "PetVaccinationRecord",
        back_populates="vaccine_batch"
    )

    def __repr__(self) -> str:
        return f"<VaccineBatch id={self.id} batch='{self.batch_number}' manufacturer='{self.manufacturer}'>"


class PetVaccinationRecord(TimestampedModel):
    """
    Caderneta de Vacinação Digital do Pet.
    Armazena histórico de aplicações, conformidade legal CFMV com CRMV do responsável,
    validade e data de reforço calculada.
    """
    __tablename__ = "pet_vaccination_records"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    pet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    vaccine_catalog_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vaccine_catalogs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    vaccine_batch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vaccine_batches.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    application_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True
    )  # Data da aplicação
    next_due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        index=True
    )  # Próxima dose / vencimento do reforço
    vet_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )  # Nome completo do médico veterinário
    vet_crmv: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )  # Registro CRMV com UF (ex: CRMV-SP 12345)
    clinic_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )  # Clínica / Pet Shop emissor
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="APLICADA",
        index=True
    )  # APLICADA, PENDENTE, ATRASADA
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )  # Reações adversas, peso no momento da vacina, etc.

    # Relacionamentos
    pet: Mapped["Pet"] = relationship(
        "Pet",
        back_populates="vaccination_records"
    )
    vaccine_catalog: Mapped["VaccineCatalog"] = relationship(
        "VaccineCatalog",
        back_populates="vaccination_records"
    )
    vaccine_batch: Mapped["VaccineBatch | None"] = relationship(
        "VaccineBatch",
        back_populates="vaccination_records"
    )

    def __repr__(self) -> str:
        return f"<PetVaccinationRecord id={self.id} pet_id={self.pet_id} status='{self.status}'>"

