"""Modelo de Aquisição Direta de Dados de Instrumentos Analíticos (Fase 5 / Sprint 5.3).

Garante integridade ALCOA+, zero erros de transcrição e rastreabilidade metrológica
completa com cálculo de hash SHA-256 no ato da ingestão (ISO/IEC 17025 §7.11 / 21 CFR Part 11).
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    Base,
    JsonMetadataMixin,
    PortableJSON,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from app.models.enums import InstrumentFileFormat, InstrumentImportStatus
from app.models.types import instrument_file_format_type, instrument_import_status_type

if TYPE_CHECKING:
    from app.models.equipment import LaboratoryEquipment
    from app.models.test_execution import TestExecution
    from app.models.user import User


class InstrumentDataImport(
    UUIDPrimaryKeyMixin, TimestampMixin, JsonMetadataMixin, Base
):
    """Registro imutável de dados brutos importados de instrumentos laboratoriais."""

    __tablename__ = "instrument_data_imports"
    __table_args__ = (
        UniqueConstraint(
            "equipment_id", "raw_file_hash_sha256", name="uq_instrument_import_dedup"
        ),
    )

    equipment_id: Mapped[UUID] = mapped_column(
        ForeignKey("laboratory_equipment.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    test_execution_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("test_executions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    imported_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_format: Mapped[InstrumentFileFormat] = mapped_column(
        instrument_file_format_type,
        nullable=False,
        index=True,
    )
    raw_file_hash_sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    raw_content: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_data: Mapped[dict[str, Any]] = mapped_column(
        PortableJSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    status: Mapped[InstrumentImportStatus] = mapped_column(
        instrument_import_status_type,
        nullable=False,
        default=InstrumentImportStatus.IMPORTED,
        server_default="IMPORTED",
        index=True,
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    mapped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relacionamentos
    equipment: Mapped[LaboratoryEquipment] = relationship(
        "LaboratoryEquipment", foreign_keys=[equipment_id], lazy="selectin"
    )
    test_execution: Mapped[TestExecution | None] = relationship(
        "TestExecution", foreign_keys=[test_execution_id], lazy="selectin"
    )
    imported_by: Mapped[User] = relationship(
        "User", foreign_keys=[imported_by_id], lazy="selectin"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<InstrumentDataImport {self.id} {self.file_name} [{self.file_format.value}]>"
