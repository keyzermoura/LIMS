"""Serviço de extração e exportação de dados analíticos para BI e Data Lakes.

Fornece paginação segura por cursor determinístico e suporte a ingestão incremental via updated_since.
Em conformidade com a especificação da Camada de Integração (docs/ESPECIFICACAO_CAMADA_INTEGRACAO_LIMS.md §6).
"""

from __future__ import annotations

import base64
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.base import utcnow
from app.models.device_sample import DeviceSample
from app.models.lab_test import LabTest
from app.models.official_report import OfficialReport
from app.models.oos_investigation import OOSInvestigation, OOSInvestigationStatus
from app.schemas.integration import (
    CursorPage,
    ExportQcMetricItem,
    ExportReportItem,
    ExportSampleItem,
    ExportTestItem,
)


def encode_cursor(dt: datetime, item_id: UUID) -> str:
    """Codifica timestamp e UUID em cursor opaco base64 URL-safe."""
    raw = f"{dt.isoformat()}|{str(item_id)}"
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8")


def decode_cursor(cursor_str: str) -> tuple[datetime, UUID] | None:
    """Decodifica cursor base64 opaco para tupla (timestamp, id)."""
    try:
        raw = base64.urlsafe_b64decode(cursor_str.encode("utf-8")).decode("utf-8")
        parts = raw.split("|", 1)
        if len(parts) != 2:
            return None
        dt = datetime.fromisoformat(parts[0])
        uid = UUID(parts[1])
        return dt, uid
    except Exception:
        return None


async def export_tests_cursor(
    db: AsyncSession,
    *,
    updated_since: datetime | None = None,
    cursor: str | None = None,
    limit: int = 50,
) -> CursorPage[ExportTestItem]:
    """Exporta ensaios com paginação determinística por cursor."""
    query = (
        select(LabTest)
        .options(
            selectinload(LabTest.sample),
            selectinload(LabTest.test_method),
            selectinload(LabTest.equipment),
        )
        .order_by(LabTest.created_at.asc(), LabTest.id.asc())
    )

    if updated_since:
        query = query.where(LabTest.updated_at >= updated_since)

    if cursor:
        parsed = decode_cursor(cursor)
        if parsed:
            cursor_dt, cursor_id = parsed
            query = query.where(
                (LabTest.created_at > cursor_dt)
                | ((LabTest.created_at == cursor_dt) & (LabTest.id > cursor_id))
            )

    fetch_limit = min(max(1, limit), 500)
    query = query.limit(fetch_limit + 1)
    result = await db.scalars(query)
    records = list(result.all())

    has_more = len(records) > fetch_limit
    items = records[:fetch_limit]

    count_stmt = select(func.count(LabTest.id))
    if updated_since:
        count_stmt = count_stmt.where(LabTest.updated_at >= updated_since)
    total_estimated = await db.scalar(count_stmt) or 0

    exported_items: list[ExportTestItem] = []
    for test in items:
        exported_items.append(
            ExportTestItem(
                id=test.id,
                sample_id=test.device_sample_id,
                sample_accession_number=test.sample.accession_number if test.sample else "N/A",
                test_name=test.name,
                method_name=test.test_method.name if test.test_method else test.method,
                equipment_code=test.equipment.code if test.equipment else None,
                status=test.status.value,
                outcome=test.outcome.value if test.outcome else None,
                result_value=test.result_value,
                result_text=test.result_text,
                unit=test.unit,
                lower_limit=test.lower_limit,
                upper_limit=test.upper_limit,
                tested_at=test.tested_at,
                signed_at=test.signed_at,
                created_at=test.created_at,
                updated_at=test.updated_at,
            )
        )

    next_cursor = None
    if has_more and items:
        last = items[-1]
        next_cursor = encode_cursor(last.created_at, last.id)

    return CursorPage(
        items=exported_items,
        next_cursor=next_cursor,
        has_more=has_more,
        count=len(exported_items),
        total_estimated=total_estimated,
    )


async def export_reports_cursor(
    db: AsyncSession,
    *,
    updated_since: datetime | None = None,
    cursor: str | None = None,
    limit: int = 50,
) -> CursorPage[ExportReportItem]:
    """Exporta laudos periciais com paginação por cursor."""
    query = (
        select(OfficialReport)
        .options(selectinload(OfficialReport.device_sample))
        .order_by(OfficialReport.created_at.asc(), OfficialReport.id.asc())
    )

    if updated_since:
        query = query.where(OfficialReport.updated_at >= updated_since)

    if cursor:
        parsed = decode_cursor(cursor)
        if parsed:
            cursor_dt, cursor_id = parsed
            query = query.where(
                (OfficialReport.created_at > cursor_dt)
                | ((OfficialReport.created_at == cursor_dt) & (OfficialReport.id > cursor_id))
            )

    fetch_limit = min(max(1, limit), 500)
    query = query.limit(fetch_limit + 1)
    result = await db.scalars(query)
    records = list(result.all())

    has_more = len(records) > fetch_limit
    items = records[:fetch_limit]

    count_stmt = select(func.count(OfficialReport.id))
    if updated_since:
        count_stmt = count_stmt.where(OfficialReport.updated_at >= updated_since)
    total_estimated = await db.scalar(count_stmt) or 0

    exported_items: list[ExportReportItem] = []
    for rep in items:
        exported_items.append(
            ExportReportItem(
                id=rep.id,
                report_number=rep.report_number,
                sample_id=rep.device_sample_id,
                sample_accession_number=rep.device_sample.accession_number
                if rep.device_sample
                else "N/A",
                title=rep.title,
                conclusion=rep.conclusion.value,
                sha256_hash=rep.sha256_hash,
                version=rep.version,
                is_latest=rep.is_latest,
                created_at=rep.created_at,
                updated_at=rep.updated_at,
            )
        )

    next_cursor = None
    if has_more and items:
        last = items[-1]
        next_cursor = encode_cursor(last.created_at, last.id)

    return CursorPage(
        items=exported_items,
        next_cursor=next_cursor,
        has_more=has_more,
        count=len(exported_items),
        total_estimated=total_estimated,
    )


async def export_samples_cursor(
    db: AsyncSession,
    *,
    updated_since: datetime | None = None,
    cursor: str | None = None,
    limit: int = 50,
) -> CursorPage[ExportSampleItem]:
    """Exporta amostras operacionais com paginação por cursor."""
    query = select(DeviceSample).order_by(DeviceSample.created_at.asc(), DeviceSample.id.asc())

    if updated_since:
        query = query.where(DeviceSample.updated_at >= updated_since)

    if cursor:
        parsed = decode_cursor(cursor)
        if parsed:
            cursor_dt, cursor_id = parsed
            query = query.where(
                (DeviceSample.created_at > cursor_dt)
                | ((DeviceSample.created_at == cursor_dt) & (DeviceSample.id > cursor_id))
            )

    fetch_limit = min(max(1, limit), 500)
    query = query.limit(fetch_limit + 1)
    result = await db.scalars(query)
    records = list(result.all())

    has_more = len(records) > fetch_limit
    items = records[:fetch_limit]

    count_stmt = select(func.count(DeviceSample.id))
    if updated_since:
        count_stmt = count_stmt.where(DeviceSample.updated_at >= updated_since)
    total_estimated = await db.scalar(count_stmt) or 0

    exported_items: list[ExportSampleItem] = []
    for s in items:
        exported_items.append(
            ExportSampleItem(
                id=s.id,
                accession_number=s.accession_number,
                commercial_name=s.commercial_name,
                manufacturer=s.manufacturer,
                status=s.status.value if hasattr(s.status, "value") else str(s.status),
                solicitation_id=s.solicitation_id,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
        )

    next_cursor = None
    if has_more and items:
        last = items[-1]
        next_cursor = encode_cursor(last.created_at, last.id)

    return CursorPage(
        items=exported_items,
        next_cursor=next_cursor,
        has_more=has_more,
        count=len(exported_items),
        total_estimated=total_estimated,
    )


async def get_qc_metrics_export(db: AsyncSession) -> ExportQcMetricItem:
    """Calcula agregados metrológicos e de conformidade em tempo hábil."""
    total_tests = await db.scalar(select(func.count(LabTest.id))) or 0

    status_counts = await db.execute(
        select(LabTest.status, func.count(LabTest.id)).group_by(LabTest.status)
    )
    tests_by_status = {
        (k.value if hasattr(k, "value") else str(k)): v for k, v in status_counts.all()
    }

    outcome_counts = await db.execute(
        select(LabTest.outcome, func.count(LabTest.id))
        .where(LabTest.outcome.isnot(None))
        .group_by(LabTest.outcome)
    )
    tests_by_outcome = {
        (k.value if k is not None else "UNKNOWN"): v for k, v in outcome_counts.all()
    }

    total_official_reports = await db.scalar(select(func.count(OfficialReport.id))) or 0
    total_oos = await db.scalar(select(func.count(OOSInvestigation.id))) or 0
    open_oos = (
        await db.scalar(
            select(func.count(OOSInvestigation.id)).where(
                OOSInvestigation.status != OOSInvestigationStatus.CLOSED
            )
        )
        or 0
    )

    return ExportQcMetricItem(
        total_tests=total_tests,
        tests_by_status=tests_by_status,
        tests_by_outcome=tests_by_outcome,
        total_official_reports=total_official_reports,
        total_oos_investigations=total_oos,
        open_oos_count=open_oos,
        generated_at=utcnow(),
    )
