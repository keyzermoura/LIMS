"""Schemas para a camada de integração M2M e exportação corporativa para BI."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class CursorPage(BaseModel, Generic[T]):
    """Envelope de resposta para endpoints de exportação paginados por cursor."""

    items: list[T]
    next_cursor: str | None = None
    has_more: bool = False
    count: int = 0
    total_estimated: int = 0


class ExportTestItem(BaseModel):
    """Ensaio de bancada normalizado para ingestão em pipelines de BI e Data Lake."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sample_id: UUID
    sample_accession_number: str
    test_name: str
    method_name: str | None = None
    equipment_code: str | None = None
    status: str
    outcome: str | None = None
    result_value: Decimal | None = None
    result_text: str | None = None
    unit: str
    lower_limit: Decimal | None = None
    upper_limit: Decimal | None = None
    tested_at: datetime | None = None
    signed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ExportReportItem(BaseModel):
    """Laudo pericial emitido para integração com ERPs e relatórios corporativos."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    report_number: str
    sample_id: UUID
    sample_accession_number: str
    title: str
    conclusion: str
    sha256_hash: str
    version: int
    is_latest: bool
    created_at: datetime
    updated_at: datetime


class ExportSampleItem(BaseModel):
    """Amostra operacional para rastreamento de cadeia de custódia e SLA."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    accession_number: str
    commercial_name: str
    manufacturer: str
    status: str
    solicitation_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class ExportQcMetricItem(BaseModel):
    """Métricas consolidadas de qualidade metrológica e taxa de conformidade."""

    total_tests: int
    tests_by_status: dict[str, int]
    tests_by_outcome: dict[str, int]
    total_official_reports: int
    total_oos_investigations: int
    open_oos_count: int
    generated_at: datetime
