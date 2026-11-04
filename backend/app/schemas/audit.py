"""Schemas da trilha de auditoria."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import AuditAction


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sequence: int
    occurred_at: datetime
    actor_id: UUID | None
    actor_username: str
    actor_role: str | None
    action: AuditAction
    entity_type: str
    entity_id: str
    old_value: dict[str, Any] | None
    new_value: dict[str, Any] | None
    reason: str | None
    ip_address: str | None
    user_agent: str | None
    request_id: str | None
    signature_id: UUID | None
    prev_hash: str
    hash: str
    hmac: str


class AuditLogDetailOut(AuditLogOut):
    payload: dict[str, Any]


class AuditIssue(BaseModel):
    sequence: int
    type: str
    detail: str


class AuditVerifyResponse(BaseModel):
    ok: bool
    checked: int
    total_records: int
    from_sequence: int
    last_sequence: int | None
    head_hash: str | None
    canonicalization: str
    issues: list[AuditIssue]


class AuditFilterOptions(BaseModel):
    actions: list[str]
    entity_types: list[str]
    actors: list[dict[str, str]]
