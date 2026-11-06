"""Schemas da trilha de auditoria."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

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


class AuditExportRequest(BaseModel):
    """Recorte exportado — os mesmos filtros da consulta da trilha."""

    format: Literal["csv", "json"] = "csv"
    entity_type: str | None = Field(default=None, max_length=64)
    entity_id: str | None = Field(default=None, max_length=64)
    actor_id: UUID | None = None
    action: AuditAction | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    search: str | None = Field(default=None, max_length=120)

    @model_validator(mode="after")
    def _validate_date_range(self) -> AuditExportRequest:
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from não pode ser posterior a date_to.")
        return self


class AuditExportVerifyResponse(BaseModel):
    ok: bool
    export_id: str | None
    generated_at: str | None
    generated_by: str | None
    record_count: int
    checked: int
    first_sequence: int | None
    last_sequence: int | None
    head_hash: str | None
    manifest_hash: str | None
    manifest_hash_ok: bool
    manifest_hmac_ok: bool
    data_hash_ok: bool
    data_hmac_ok: bool
    files_ok: bool
    chain_ok: bool
    chain_contiguous: bool
    chain_gaps: int
    matches_database: bool
    canonicalization: str | None
    issues: list[AuditIssue]
