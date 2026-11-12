"""Modelos de Checklist e Critérios de Conferência (M0.3 / D11-D12).

Checklists versionados com critérios Eliminatórios (E), Saneáveis (S) e Informativos (I).
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ChecklistResult, CriterionClass
from app.models.types import checklist_result_type, criterion_class_type

if TYPE_CHECKING:
    from app.models.receipt import ReceiptItem
    from app.models.user import User


class ChecklistTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Modelo/template de checklist aplicável por categoria de dispositivo."""

    __tablename__ = "checklist_templates"

    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relacionamentos
    criteria: Mapped[list[ChecklistCriterion]] = relationship(
        "ChecklistCriterion", back_populates="template", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ChecklistTemplate {self.code} v{self.version}>"


class ChecklistCriterion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Critério versionado com classificação regulatória (E/S/I)."""

    __tablename__ = "checklist_criteria"

    template_id: Mapped[UUID] = mapped_column(
        ForeignKey("checklist_templates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(16), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    criterion_class: Mapped[CriterionClass] = mapped_column(
        criterion_class_type, nullable=False, default=CriterionClass.ELIMINATORIO
    )
    is_mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relacionamentos
    template: Mapped[ChecklistTemplate] = relationship("ChecklistTemplate", back_populates="criteria")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ChecklistCriterion {self.code} [{self.criterion_class.value}]>"


class ChecklistAnswer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Resposta formalizada a um critério no ato da conferência."""

    __tablename__ = "checklist_answers"

    receipt_item_id: Mapped[UUID] = mapped_column(
        ForeignKey("receipt_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    criterion_id: Mapped[UUID] = mapped_column(
        ForeignKey("checklist_criteria.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    result: Mapped[ChecklistResult] = mapped_column(
        checklist_result_type, nullable=False, default=ChecklistResult.CONFORME
    )
    justification: Mapped[str | None] = mapped_column(Text)
    evaluated_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    # Relacionamentos
    receipt_item: Mapped[ReceiptItem] = relationship("ReceiptItem", back_populates="checklist_answers")
    criterion: Mapped[ChecklistCriterion] = relationship("ChecklistCriterion", lazy="selectin")
    evaluated_by: Mapped[User] = relationship("User", lazy="selectin")
