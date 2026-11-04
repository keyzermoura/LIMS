"""Schemas de autenticação e assinatura eletrônica."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    SignatureAction,
    SignatureMeaning,
    UserRole,
)
from app.schemas.common import UserBrief


class UserOut(UserBrief):
    email: str
    is_active: bool
    last_login_at: datetime | None = None
    mfa_enabled: bool = False
    created_at: datetime


class MeOut(UserOut):
    permissions: list[str] = []


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: MeOut


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=20)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=12, max_length=128)


class ESignatureIssueRequest(BaseModel):
    """Reautenticação + declaração de intenção (Part 11 §11.200(a))."""

    password: str = Field(min_length=1, max_length=256)
    meaning: SignatureMeaning
    reason: str = Field(min_length=10, max_length=1000)
    entity_type: str = Field(min_length=2, max_length=64)
    entity_id: str = Field(min_length=1, max_length=64)
    action: SignatureAction


class ESignatureIssueResponse(BaseModel):
    token: str
    signature_id: UUID
    expires_at: datetime
    manifest: dict[str, Any]
    manifest_hash: str


class UserCreateRequest(BaseModel):
    # Gerado pelo cliente para vincular a assinatura ao registro antes do INSERT.
    id: UUID

    username: str = Field(min_length=3, max_length=64, pattern=r"^[a-z0-9._-]+$")
    email: str = Field(min_length=5, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    full_name: str = Field(min_length=3, max_length=160)
    role: UserRole
    password: str = Field(min_length=12, max_length=128)
    registration_number: str | None = Field(default=None, max_length=64)


class UserCreatedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
