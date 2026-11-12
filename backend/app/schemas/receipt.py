"""Schemas Pydantic para Recebimento, Conferência e Custódia (Fase 1 / M1.1)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    ConferenceStatus,
    CustodyEventType,
    CustodyObjectStatus,
    PresentationStatus,
    ReceiptDecisionEnum,
    ReceiptStatus,
)
from app.schemas.common import UserBrief
from app.schemas.solicitation import SolicitationItemOut


class ReceiptCreate(BaseModel):
    arrived_at: datetime | None = None
    arrival_location: str | None = Field(default=None, max_length=255)
    external_protocol: str | None = Field(default=None, max_length=120)
    delivery_method: str | None = Field(default=None, max_length=100)
    packaging_condition: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=4000)


class ReceiptItemConference(BaseModel):
    presentation_status: PresentationStatus = PresentationStatus.PRESENTED
    presented_quantity: Decimal = Field(default=Decimal(1), ge=0)
    conference_status: ConferenceStatus = ConferenceStatus.PENDENTE
    decision: ReceiptDecisionEnum | None = None
    notes: str | None = Field(default=None, max_length=4000)
    version: int = Field(ge=1)


class CustodyEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    custody_object_id: UUID
    event_type: CustodyEventType
    effective_at: datetime
    from_custodian_id: UUID | None = None
    from_custodian: UserBrief | None = None
    to_custodian_id: UUID | None = None
    to_custodian: UserBrief | None = None
    from_location: str | None = None
    to_location: str | None = None
    reason: str
    registered_by_id: UUID
    registered_by: UserBrief | None = None
    created_at: datetime


class CustodyObjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    receipt_item_id: UUID
    object_code: str
    grouping_description: str | None = None
    represented_quantity: Decimal
    current_location: str | None = None
    seal_number: str | None = None
    status: CustodyObjectStatus
    current_custodian_id: UUID | None = None
    current_custodian: UserBrief | None = None
    linked_device_sample_id: UUID | None = None
    version: int
    created_at: datetime
    updated_at: datetime


class CustodyTransferCreate(BaseModel):
    to_custodian_id: UUID
    to_location: str | None = Field(default=None, max_length=255)
    reason: str = Field(min_length=5, max_length=500)
    version: int = Field(ge=1)


class CustodyAcceptanceCreate(BaseModel):
    decision: ReceiptDecisionEnum = ReceiptDecisionEnum.ACCEPTED
    storage_location: str = Field(min_length=1, max_length=160)
    notes: str | None = Field(default=None, max_length=4000)
    version: int = Field(ge=1)


class ReceiptItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    receipt_id: UUID
    solicitation_item_id: UUID
    solicitation_item: SolicitationItemOut | None = None
    presentation_status: PresentationStatus
    presented_quantity: Decimal
    conference_status: ConferenceStatus
    decision: ReceiptDecisionEnum | None = None
    notes: str | None = None
    custody_objects: list[CustodyObjectOut] = []
    version: int
    created_at: datetime
    updated_at: datetime


class ReceiptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    solicitation_id: UUID
    receipt_number: str
    arrived_at: datetime
    received_by_id: UUID
    received_by: UserBrief | None = None
    arrival_location: str | None = None
    external_protocol: str | None = None
    delivery_method: str | None = None
    packaging_condition: str | None = None
    notes: str | None = None
    status: ReceiptStatus
    items: list[ReceiptItemOut] = []
    version: int
    created_at: datetime
    updated_at: datetime
