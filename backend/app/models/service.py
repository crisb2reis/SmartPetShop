from decimal import Decimal
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Numeric, Integer, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import TimestampedModel

if TYPE_CHECKING:
    from app.models.appointment import Appointment


class Service(TimestampedModel):
    __tablename__ = "services"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True) # Banho, Tosa, Veterinário, Vacinação
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relacionamentos
    appointments: Mapped[List["Appointment"]] = relationship("Appointment", back_populates="service")

    def __repr__(self) -> str:
        return f"<Service id={self.id} name='{self.name}' price={self.price}>"
