"""Schemas Pydantic para Aquisição de Dados de Instrumentos (Fase 5 / Sprint 5.3)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import InstrumentFileFormat, InstrumentImportStatus


class InstrumentDataImportOut(BaseModel):
    """Representação serializada de um registro de importação de instrumento."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    equipment_id: UUID
    test_execution_id: UUID | None = None
    imported_by_id: UUID
    file_name: str
    file_format: InstrumentFileFormat
    raw_file_hash_sha256: str
    raw_content: str | None = None
    parsed_data: dict[str, Any]
    status: InstrumentImportStatus
    rejection_reason: str | None = None
    mapped_at: datetime | None = None
    created_at: datetime


class InstrumentDataMapIn(BaseModel):
    """Requisição para vincular leituras importadas a uma execução de ensaio."""

    execution_id: UUID = Field(..., description="ID da execução de ensaio alvo.")


class InstrumentDataSummary(BaseModel):
    """Resumo de aquisições de instrumentos por status."""

    total_imports: int
    mapped_imports: int
    unmapped_imports: int
