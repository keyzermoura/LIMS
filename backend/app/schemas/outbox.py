"""Schemas para Outbox Transacional e Webhooks."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class OutboxEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_type: str
    aggregate_type: str
    aggregate_id: str
    payload: dict[str, Any]
    created_at: datetime
    published_at: datetime | None = None
    attempts: int
    next_attempt_at: datetime
    last_error: str | None = None
    dead_lettered_at: datetime | None = None


class OutboxDispatchResponse(BaseModel):
    dispatched_count: int
    message: str = "Processamento do outbox concluído com sucesso."
