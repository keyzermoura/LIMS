"""Schemas Pydantic para Notificações e Alertas em Tempo Real (Fase 5 / Sprint 5.2).

Conforme ISO/IEC 17025:2017 (§7.11, §8.7) e 21 CFR Part 11.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import NotificationCategory, NotificationSeverity, UserRole


class NotificationCreateIn(BaseModel):
    """Payload para emissão de notificação manual ou programada."""

    user_id: UUID | None = Field(
        None, description="Destinatário individual. Se nulo, direciona por perfil."
    )
    target_role: UserRole | None = Field(
        None, description="Perfil destinatário (ex.: TECNICO, FISCAL, ADMIN)."
    )
    title: str = Field(..., max_length=160, description="Título conciso do alerta.")
    message: str = Field(..., description="Corpo detalhado da notificação.")
    severity: NotificationSeverity = Field(
        NotificationSeverity.INFO, description="Severidade do alerta."
    )
    category: NotificationCategory = Field(
        NotificationCategory.SYSTEM, description="Categoria do evento."
    )
    link_url: str | None = Field(
        None, max_length=255, description="Link de navegação direta para o recurso afetado."
    )


class NotificationOut(BaseModel):
    """Payload de retorno de uma notificação."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID | None
    target_role: UserRole | None
    title: str
    message: str
    severity: NotificationSeverity
    category: NotificationCategory
    link_url: str | None
    is_read: bool
    read_at: datetime | None
    created_at: datetime


class NotificationSummary(BaseModel):
    """Resumo de contagem de notificações não lidas e distribuição de severidade."""

    unread_count: int = Field(0, description="Total de notificações não lidas.")
    critical_count: int = Field(0, description="Alertas críticos não lidos.")
    warning_count: int = Field(0, description="Alertas de atenção não lidos.")
    info_count: int = Field(0, description="Informativos não lidos.")


class AlertCheckResult(BaseModel):
    """Resultado da rotina de varredura proativa de desvios do laboratório."""

    alerts_generated: int = Field(
        0, description="Quantidade de novos alertas emitidos nesta varredura."
    )
    details: list[str] = Field(
        default_factory=list, description="Resumo dos desvios identificados."
    )
