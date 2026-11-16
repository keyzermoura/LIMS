"""Schemas Pydantic para Webhooks e Mensageria Segura de Integração (Sprint 5.4)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class WebhookSubscriptionCreateIn(BaseModel):
    """Payload para registro de um novo endpoint de webhook de saída."""

    url: str = Field(..., max_length=500, description="URL HTTPS do receptor do webhook")
    secret: str | None = Field(
        None,
        min_length=16,
        max_length=255,
        description="Segredo compartilhado para assinatura HMAC SHA-256 (se omitido, será gerado automaticamente)",
    )
    description: str | None = Field(None, max_length=255, description="Identificação do sistema cliente integrador")
    events: list[str] = Field(
        default_factory=lambda: ["*"],
        description="Lista de eventos inscritos (ex: ['report.issued', 'test.completed'] ou ['*'])",
    )


class WebhookSubscriptionOut(BaseModel):
    """Dados cadastrais de uma subscrição de webhook."""

    id: UUID
    url: str
    description: str | None
    events: list[str]
    is_active: bool
    created_by_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WebhookDeliveryOut(BaseModel):
    """Registro de entrega / tentativa de disparo de webhook."""

    id: UUID
    subscription_id: UUID
    event: str
    payload: dict[str, Any]
    status: str
    status_code: int | None
    response_body: str | None
    attempt_count: int
    delivered_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class WebhookPingResponse(BaseModel):
    """Resposta do disparo de teste / ping para um webhook."""

    subscription_id: UUID
    delivery_id: UUID
    event: str
    status: str
    status_code: int | None
    signature_header: str
