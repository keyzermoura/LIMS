"""Schemas de amostras e cadeia de custódia."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import SampleStatus
from app.schemas.common import UserBrief


class SampleCreate(BaseModel):
    """O `id` é gerado pelo cliente para permitir vincular a assinatura
    eletrônica ao registro ANTES da gravação (evita assinatura "cega")."""

    id: UUID
    serial_number: str = Field(min_length=1, max_length=120)
    lot_number: str = Field(min_length=1, max_length=120)
    manufacturer: str = Field(min_length=1, max_length=160)
    commercial_name: str = Field(min_length=1, max_length=200)
    model: str | None = Field(default=None, max_length=120)
    registration_number: str | None = Field(default=None, max_length=64)
    description: str | None = Field(default=None, max_length=4000)
    storage_location: str = Field(min_length=1, max_length=160)
    received_at: datetime | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)

    @field_validator("serial_number", "lot_number", "manufacturer", "commercial_name")
    @classmethod
    def _strip(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Campo obrigatório.")
        return value

    @field_validator("received_at")
    @classmethod
    def _not_in_future(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        from datetime import timedelta

        now = datetime.now(UTC)
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        if value > now + timedelta(minutes=5):
            raise ValueError("A data de recebimento não pode estar no futuro.")
        return value


class SampleStatusUpdate(BaseModel):
    status: SampleStatus
    reason: str = Field(min_length=10, max_length=500)
    version: int = Field(ge=1)


class SampleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    accession_number: str
    serial_number: str
    lot_number: str
    manufacturer: str
    commercial_name: str
    model: str | None
    registration_number: str | None
    description: str | None
    status: SampleStatus
    received_at: datetime
    received_by_id: UUID
    current_custodian: UserBrief | None = None
    current_location: str | None
    attributes: dict[str, Any] = {}
    version: int
    created_at: datetime
    updated_at: datetime


class CustodyTransferRequest(BaseModel):
    device_sample_id: UUID
    to_custodian_id: UUID
    reason: str = Field(min_length=10, max_length=500)
    storage_location: str = Field(min_length=1, max_length=160)
    seal_number: str | None = Field(default=None, max_length=80)
    notes: str | None = Field(default=None, max_length=2000)
    version: int = Field(ge=1)


class CustodyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    device_sample_id: UUID
    from_custodian: UserBrief | None = None
    to_custodian: UserBrief
    transferred_at: datetime
    reason: str
    location_from: str | None
    location_to: str
    seal_number: str | None
    notes: str | None
    signature_id: UUID | None


class TimelineEvent(BaseModel):
    id: str
    type: Literal[
        "RECEIPT",
        "CUSTODY",
        "TEST_CREATED",
        "TEST_SIGNED",
        "CAPA_OPENED",
        "STATUS_CHANGE",
    ]
    occurred_at: datetime
    title: str
    description: str | None = None
    actor_name: str | None = None
    location: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SampleQrOut(BaseModel):
    token: str
    accession_number: str
    image_url: str
    verify_url: str


class SampleVerifyOut(BaseModel):
    valid: bool
    id: UUID
    accession_number: str
    serial_number: str
    lot_number: str
    manufacturer: str
    commercial_name: str
    status: SampleStatus


class TransitionInfo(BaseModel):
    from_status: SampleStatus
    to_status: SampleStatus
    allowed: list[SampleStatus]


class SampleStatusChangeOut(BaseModel):
    sample: SampleOut
    previous_status: SampleStatus
    audit_log_id: int | None = None


class TransferResponse(BaseModel):
    custody: CustodyOut
    sample: SampleOut
    audit_log_id: int
    signature_id: UUID


class SampleCreateResponse(BaseModel):
    sample: SampleOut
    audit_log_id: int
    signature_id: UUID
    qr_code_url: str


class EventSignatureOut(BaseModel):
    signature_id: UUID
    signer_full_name: str
    signer_role: str
    meaning: str
    reason: str
    signed_at: datetime
    manifest_hash: str


__all__ = [
    "CustodyOut",
    "CustodyTransferRequest",
    "EventSignatureOut",
    "SampleCreate",
    "SampleCreateResponse",
    "SampleOut",
    "SampleQrOut",
    "SampleStatusChangeOut",
    "SampleStatusUpdate",
    "SampleVerifyOut",
    "TimelineEvent",
    "TransferResponse",
]
