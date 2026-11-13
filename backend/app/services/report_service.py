"""Serviço de Emissão e Validação Pública de Laudos Oficiais (Sprint 3.2 / ISO/IEC 17025)."""

from __future__ import annotations

import hashlib
import secrets
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.context import RequestContext
from app.core.errors import NotFoundError, ValidationDomainError
from app.core.serialization import canonical_json, jsonable
from app.models.base import utcnow
from app.models.device_sample import DeviceSample
from app.models.electronic_signature import ElectronicSignature
from app.models.enums import (
    AuditAction,
    AuditEntity,
    CoordinationReviewStatus,
    SignatureAction,
    TestStatus,
)
from app.models.lab_test import LabTest
from app.models.official_report import OfficialReport
from app.models.user import User
from app.schemas.official_report import OfficialReportGenerateIn
from app.services import audit_service, signature_service
from app.services.audit_service import snapshot


async def generate_official_report(
    db: AsyncSession,
    *,
    payload: OfficialReportGenerateIn,
    issuer: User,
    signature_token: str | None = None,
    context: RequestContext | None = None,
) -> tuple[OfficialReport, int]:
    """Gera um laudo oficial consolidado para os ensaios aprovados de uma amostra."""
    sample = await db.get(DeviceSample, payload.device_sample_id)
    if sample is None:
        raise NotFoundError("Amostra não encontrada.")

    # Busca os ensaios indicados
    stmt = (
        select(LabTest)
        .options(
            selectinload(LabTest.test_method),
            selectinload(LabTest.equipment),
            selectinload(LabTest.tested_by),
        )
        .where(LabTest.id.in_(payload.test_ids))
    )
    tests = list((await db.scalars(stmt)).all())

    if len(tests) != len(payload.test_ids):
        raise ValidationDomainError("Um ou mais ensaios informados não foram encontrados.")

    for t in tests:
        if t.device_sample_id != sample.id:
            raise ValidationDomainError(
                f"O ensaio '{t.name}' não pertence à amostra indicada ({sample.accession_number})."
            )
        if t.status != TestStatus.CONCLUIDO:
            raise ValidationDomainError(
                f"O ensaio '{t.name}' ainda não está concluído (status: {t.status.value})."
            )
        if t.review_status != CoordinationReviewStatus.APROVADO:
            raise ValidationDomainError(
                f"O ensaio '{t.name}' não possui parecer técnico de aprovação (review_status: {t.review_status.value})."
            )

    now = utcnow()
    count_stmt = select(func.count()).select_from(OfficialReport)
    total_reports = (await db.scalar(count_stmt)) or 0
    report_number = f"LDO-{now.year}-{total_reports + 1:04d}"
    auth_token = secrets.token_urlsafe(24)

    # Monta payload consolidado para cálculo do hash SHA-256 criptográfico
    tests_manifest: list[dict[str, Any]] = []
    for t in sorted(tests, key=lambda x: x.name):
        tests_manifest.append(
            {
                "id": str(t.id),
                "name": t.name,
                "unit": t.unit,
                "result_value": str(t.result_value) if t.result_value is not None else None,
                "result_text": t.result_text,
                "outcome": t.outcome.value if t.outcome else None,
                "lower_limit": str(t.lower_limit) if t.lower_limit is not None else None,
                "upper_limit": str(t.upper_limit) if t.upper_limit is not None else None,
                "tested_by": t.tested_by.full_name if t.tested_by else None,
                "tested_at": t.tested_at.isoformat() if t.tested_at else None,
            }
        )

    manifest: dict[str, Any] = {
        "report_number": report_number,
        "sample": {
            "id": str(sample.id),
            "accession_number": sample.accession_number,
            "serial_number": sample.serial_number,
            "lot_number": sample.lot_number,
            "commercial_name": sample.commercial_name,
            "model": sample.model,
        },
        "conclusion": payload.conclusion.value,
        "summary": payload.summary,
        "issued_by": issuer.full_name,
        "issued_at": now.isoformat(),
        "tests": tests_manifest,
    }

    serialized_str: str = canonical_json(jsonable(manifest))
    sha256_hash = hashlib.sha256(serialized_str.encode("utf-8")).hexdigest()

    sig_record: ElectronicSignature | None = None
    if signature_token:
        request_ctx = context or RequestContext(
            ip_address="127.0.0.1", user_agent="LIMS-Internal", request_id="internal"
        )
        sig_record = await signature_service.consume(
            db,
            token=signature_token,
            user=issuer,
            entity_type="DeviceSample",
            entity_id=str(sample.id),
            action=SignatureAction.CLOSE,
            context=request_ctx,
        )

    if sig_record is None:
        raise ValidationDomainError("Assinatura eletrônica é obrigatória para emissão de laudo oficial.")

    report = OfficialReport(
        id=uuid4(),
        report_number=report_number,
        device_sample_id=sample.id,
        title=payload.title,
        conclusion=payload.conclusion,
        summary=payload.summary,
        sha256_hash=sha256_hash,
        auth_token=auth_token,
        issued_by_id=issuer.id,
        signature_id=sig_record.id,
        attributes={"manifest": manifest, "test_count": len(tests)},
        issued_at=now,
    )
    db.add(report)

    audit_entry = await audit_service.append(
        db,
        action=AuditAction.CREATE,
        entity_type=AuditEntity.OFFICIAL_REPORT.value,
        entity_id=report.id,
        actor=issuer,
        old_value=None,
        new_value=snapshot(report),
        reason=f"Laudo pericial oficial {report_number} emitido com conclusão: {payload.conclusion.value}",
        context=context,
        signature_id=sig_record.id,
    )

    await db.commit()
    await db.refresh(report, ["issued_by", "device_sample"])
    return report, audit_entry.sequence


async def get_report_by_id(
    db: AsyncSession,
    report_id: UUID,
) -> OfficialReport:
    """Busca um laudo oficial pelo ID."""
    stmt = (
        select(OfficialReport)
        .options(
            selectinload(OfficialReport.issued_by),
            selectinload(OfficialReport.device_sample),
        )
        .where(OfficialReport.id == report_id)
    )
    report = await db.scalar(stmt)
    if report is None:
        raise NotFoundError("Laudo oficial não encontrado.")
    return report


async def verify_report_public(
    db: AsyncSession,
    auth_token: str,
) -> dict[str, Any]:
    """Validação pública de autenticidade via QR Code / auth_token."""
    stmt = (
        select(OfficialReport)
        .options(
            selectinload(OfficialReport.issued_by),
            selectinload(OfficialReport.device_sample),
        )
        .where(OfficialReport.auth_token == auth_token)
    )
    report = await db.scalar(stmt)
    if report is None:
        raise NotFoundError("Laudo não localizado ou token de autenticidade inválido.")

    # Revalida hash SHA-256 a partir do manifesto arquivado
    manifest = report.attributes.get("manifest") if report.attributes else {}
    serialized_str = canonical_json(jsonable(manifest))
    calculated_hash = hashlib.sha256(serialized_str.encode("utf-8")).hexdigest()
    is_valid = (calculated_hash == report.sha256_hash)

    return {
        "is_valid": is_valid,
        "report_number": report.report_number,
        "sample_acc_number": report.device_sample.accession_number,
        "sample_commercial_name": report.device_sample.commercial_name,
        "sample_serial_number": report.device_sample.serial_number,
        "sample_lot_number": report.device_sample.lot_number,
        "conclusion": report.conclusion,
        "sha256_hash": report.sha256_hash,
        "issued_by_name": report.issued_by.full_name if report.issued_by else "Perito Oficial",
        "issued_at": report.issued_at,
    }


async def list_reports_for_sample(
    db: AsyncSession,
    sample_id: UUID,
) -> list[OfficialReport]:
    """Lista laudos oficiais emitidos para uma amostra."""
    stmt = (
        select(OfficialReport)
        .options(selectinload(OfficialReport.issued_by))
        .where(OfficialReport.device_sample_id == sample_id)
        .order_by(OfficialReport.issued_at.desc())
    )
    res = await db.scalars(stmt)
    return list(res.all())
