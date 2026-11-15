from typing import List, TYPE_CHECKING
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import TimestampedModel

if TYPE_CHECKING:
    from app.models.user import User


class Organization(TimestampedModel):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    cnpj: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True, index=True)
    plan: Mapped[str] = mapped_column(String(50), default="pro", nullable=False) # starter, pro, enterprise
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relacionamento com funcionários da empresa
    users: Mapped[List["User"]] = relationship("User", back_populates="organization", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Organization id={self.id} name='{self.name}'>"
