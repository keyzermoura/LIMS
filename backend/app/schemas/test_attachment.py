"""Schemas Pydantic para Anexos e Evidências Brutas de Ensaios (Fase 3 / ALCOA+)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.common import UserBrief


class TestAttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lab_test_id: UUID
    filename: str
    content_type: str
    file_size: int
    sha256_hash: str
    description: str | None = None
    uploaded_by_id: UUID
    uploaded_by: UserBrief | None = None
    created_at: datetime
