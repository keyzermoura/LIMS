"""Schemas para Contas de Serviço (M2M) e Idempotência."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ServiceClientCreate(BaseModel):
    name: str = Field(min_length=3, max_length=160, description="Nome identificador da integração")
    scopes: list[str] = Field(default_factory=list, description="Escopos concedidos à conta")
    expires_in_days: int = Field(
        default=90, ge=1, le=365, description="Validade da credencial em dias"
    )
    ip_allowlist: list[str] | None = Field(
        default=None, description="Lista opcional de IPs/CIDRs permitidos"
    )
    service_username: str | None = Field(
        default=None,
        min_length=3,
        max_length=64,
        description="Nome de usuário opcional para a conta de serviço associada",
    )


class ServiceClientCreated(BaseModel):
    id: UUID
    client_id: str
    client_secret: str = Field(description="Segredo de autenticação exibido uma única vez")
    name: str
    scopes: list[str]
    expires_at: datetime
    service_user_id: UUID


class ServiceClientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_id: str
    name: str
    scopes: list[str]
    service_user_id: UUID
    is_active: bool
    expires_at: datetime
    last_used_at: datetime | None = None
    created_at: datetime
    ip_allowlist: list[str] | None = None


class ServiceTokenRequest(BaseModel):
    grant_type: str = Field(default="client_credentials", description="Tipo de concessão OAuth2")
    client_id: str = Field(min_length=3, max_length=64)
    client_secret: str = Field(min_length=16, max_length=256)
    scope: str | None = Field(default=None, description="Escopos solicitados separados por espaço")


class ServiceTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 900
    scope: str


class ServiceSecretRotateResponse(BaseModel):
    client_id: str
    new_client_secret: str = Field(description="Novo segredo gerado exibido uma única vez")
    expires_at: datetime
    message: str = (
        "Novo segredo gerado com sucesso. O segredo anterior permanecerá "
        "válido durante a janela de sobreposição."
    )
