"""Schemas Pydantic para Solicitação e Itens Declarados (Fase 1 / M1.1)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import SolicitationStatus
from app.schemas.common import UserBrief


class SolicitationItemCreate(BaseModel):
    product_name: str = Field(min_length=1, max_length=200)
    category: str | None = Field(default=None, max_length=100)
    manufacturer: str | None = Field(default=None, max_length=160)
    model: str | None = Field(default=None, max_length=120)
    serial_number: str | None = Field(default=None, max_length=120)
    lot_number: str | None = Field(default=None, max_length=120)
    declared_quantity: Decimal = Field(default=Decimal(1), gt=0)
    unit_of_measure: str = Field(default="UN", min_length=1, max_length=32)
    notes: str | None = Field(default=None, max_length=4000)

    @field_validator("product_name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("O nome do produto é obrigatório.")
        return s


class SolicitationItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    solicitation_id: UUID
    item_number: int
    product_name: str
    category: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    serial_number: str | None = None
    lot_number: str | None = None
    declared_quantity: Decimal
    unit_of_measure: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class SolicitationCreate(BaseModel):
    requester_name: str = Field(min_length=1, max_length=160)
    requester_email: str | None = Field(default=None, max_length=255)
    requester_document: str | None = Field(default=None, max_length=64)
    requester_organization: str | None = Field(default=None, max_length=200)
    purpose: str | None = Field(default=None, max_length=4000)
    request_type: str = Field(default="FISCALIZACAO", max_length=64)
    priority: str = Field(default="NORMAL", max_length=32)
    items: list[SolicitationItemCreate] = Field(min_length=1)

    @field_validator("requester_name")
    @classmethod
    def _strip_requester(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("O nome do solicitante é obrigatório.")
        return s


class SolicitationUpdate(BaseModel):
    requester_name: str | None = Field(default=None, min_length=1, max_length=160)
    requester_email: str | None = Field(default=None, max_length=255)
    requester_document: str | None = Field(default=None, max_length=64)
    requester_organization: str | None = Field(default=None, max_length=200)
    purpose: str | None = Field(default=None, max_length=4000)
    request_type: str | None = Field(default=None, max_length=64)
    priority: str | None = Field(default=None, max_length=32)
    items: list[SolicitationItemCreate] | None = None
    version: int = Field(ge=1)


class SolicitationSubmit(BaseModel):
    version: int = Field(ge=1)
    notes: str | None = Field(default=None, max_length=1000)


class SolicitationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    solicitation_number: str
    requester_name: str
    requester_email: str | None = None
    requester_document: str | None = None
    requester_organization: str | None = None
    created_by_id: UUID
    created_by: UserBrief | None = None
    purpose: str | None = None
    request_type: str
    priority: str
    status: SolicitationStatus
    submitted_at: datetime | None = None
    items: list[SolicitationItemOut] = []
    has_receipt: bool = False
    version: int
    created_at: datetime
    updated_at: datetime
