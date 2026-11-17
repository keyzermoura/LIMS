"""Serviço de Emissão e Validação Pública de Laudos Oficiais e Emendas (ISO/IEC 17025 §7.8 e §7.8.8).

Responsável pela emissão de laudos periciais com PDF real assinado, controle estrito de
emendas retificadoras com rastreabilidade histórica e validação pública de integridade criptográfica.
"""

from __future__ import annotations

import hashlib
import secrets
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.context import RequestContext
from app.core.errors import NotFoundError, ValidationDomainError
from app.core.serialization import canonical_json, jsonable
from app.db.dialect import next_sequence
from app.models.base import utcnow
from app.models.device_sample import DeviceSample
from app.models.electronic_signature import ElectronicSignature
from app.models.enums import (
    AuditAction,
    AuditEntity,
    CoordinationReviewStatus,
    OOSInvestigationStatus,
    SignatureAction,
    TestStatus,
)
from app.models.lab_test import LabTest
from app.models.official_report import OfficialReport
from app.models.oos_investigation import OOSInvestigation
from app.models.uncertainty import UncertaintyBudget
from app.models.user import User
from app.schemas.official_report import OfficialReportGenerateIn
from app.services import audit_service, outbox_service, qc_spc_service, signature_service
from app.services.audit_service import snapshot
from app.services.pdf_report_service import generate_official_report_pdf


async def generate_official_report(
    db: AsyncSession,
    *,
    payload: OfficialReportGenerateIn,
    issuer: User,
    signature_token: str | None = None,
    context: RequestContext | None = None,
) -> tuple[OfficialReport, int]:
    """Gera um laudo oficial consolidado para os ensaios aprovados de uma amostra com PDF real e hash SHA-256."""
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

        # Intertravamento regulamentar ISO/IEC 17025 §7.10: bloqueia laudo se houver OOS pendente
        open_oos = await db.scalar(
            select(OOSInvestigation).where(
                OOSInvestigation.lab_test_id == t.id,
                OOSInvestigation.status != OOSInvestigationStatus.CLOSED,
            )
        )
        if open_oos:
            raise ValidationDomainError(
                f"O ensaio '{t.name}' possui investigação de desvio analítico OOS pendente "
                f"({open_oos.investigation_number} - status: {open_oos.status.value}). "
                "Emissão de laudo bloqueada (ISO/IEC 17025 §7.10)."
            )

        # Intertravamento regulamentar ISO/IEC 17025 §7.7.1: bloqueia laudo se houver violação ativa de Westgard
        if t.method_id:
            has_spc_block, spc_msg = await qc_spc_service.check_method_has_active_violation(
                db, t.method_id
            )
            if has_spc_block:
                raise ValidationDomainError(
                    f"O ensaio '{t.name}' está vinculado a método com violação de controle estatístico (CEP/Westgard). "
                    f"{spc_msg} Emissão de laudo bloqueada (ISO/IEC 17025 §7.7.1)."
                )

    now = utcnow()
    seq = await next_sequence(db, "official_report_seq")
    report_number = f"LDO-{now.year}-{seq:04d}"
    auth_token = secrets.token_urlsafe(24)

    # Monta payload consolidado para cálculo do hash SHA-256 criptográfico
    tests_manifest: list[dict[str, Any]] = []
    tests_data_pdf: list[dict[str, Any]] = []

    for t in sorted(tests, key=lambda x: x.name):
        entry: dict[str, Any] = {
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
        budget = await db.scalar(
            select(UncertaintyBudget)
            .where(UncertaintyBudget.lab_test_id == t.id)
            .order_by(UncertaintyBudget.created_at.desc())
        )
        u_str = "—"
        if budget is not None:
            entry["uncertainty"] = {
                "budget_id": str(budget.id),
                "combined_uncertainty": str(budget.combined_uncertainty),
                "expanded_uncertainty": str(budget.expanded_uncertainty),
                "coverage_factor": str(budget.coverage_factor),
                "confidence_level": str(budget.confidence_level),
                "guard_band_width": str(budget.guard_band_width),
                "decision_rule": budget.decision_rule.value,
                "conformity_status": budget.conformity_status.value,
                "conformity_statement": budget.conformity_statement,
            }
            u_str = f"± {budget.expanded_uncertainty} {t.unit or ''} (k={budget.coverage_factor})".strip()

        tests_manifest.append(entry)
        tests_data_pdf.append(
            {
                "parameter_name": t.name,
                "specification": f"{t.lower_limit or '—'} a {t.upper_limit or '—'} {t.unit or ''}".strip(),
                "result_value": str(t.result_value)
                if t.result_value is not None
                else (t.result_text or "—"),
                "unit": t.unit or "",
                "uncertainty_u": u_str,
                "outcome": t.outcome.value if t.outcome else "APROVADO",
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

    sample_data = {
        "accession_number": sample.accession_number,
        "lot_number": sample.lot_number or "—",
        "serial_number": sample.serial_number or "—",
        "manufacturer": sample.manufacturer or "—",
        "device_type": sample.commercial_name,
        "collected_at": sample.created_at.strftime("%d/%m/%Y") if sample.created_at else "—",
    }

    # Gera o PDF binário real do laudo pericial (ISO/IEC 17025 §7.8)
    pdf_bytes = generate_official_report_pdf(
        report_number=report_number,
        title=payload.title,
        conclusion=payload.conclusion.value,
        summary=payload.summary,
        version=1,
        is_latest=True,
        amendment_reason=None,
        supersedes_number=None,
        sample_data=sample_data,
        tests_data=tests_data_pdf,
        issuer_name=issuer.full_name,
        issuer_role=issuer.role.value if hasattr(issuer.role, "value") else str(issuer.role),
        issued_at_iso=now.strftime("%d/%m/%Y %H:%M:%S"),
        auth_token=auth_token,
    )
    sha256_hash = hashlib.sha256(pdf_bytes).hexdigest()

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
        raise ValidationDomainError(
            "Assinatura eletrônica é obrigatória para emissão de laudo oficial."
        )

    report = OfficialReport(
        id=uuid4(),
        report_number=report_number,
        device_sample_id=sample.id,
        title=payload.title,
        conclusion=payload.conclusion,
        summary=payload.summary,
        version=1,
        root_report_id=None,
        supersedes_id=None,
        is_latest=True,
        amendment_reason=None,
        sha256_hash=sha256_hash,
        pdf_data=pdf_bytes,
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

    await outbox_service.enqueue_event(
        db,
        event_type="report.issued",
        aggregate_type="OfficialReport",
        aggregate_id=str(report.id),
        payload={
            "report_id": str(report.id),
            "report_number": report.report_number,
            "device_sample_id": str(report.device_sample_id),
            "conclusion": (
                report.conclusion.value
                if hasattr(report.conclusion, "value")
                else str(report.conclusion)
            ),
            "sha256_hash": report.sha256_hash,
            "issued_at": report.issued_at.isoformat(),
        },
    )

    await db.commit()
    await db.refresh(report, ["issued_by", "device_sample"])
    return report, audit_entry.sequence


async def amend_official_report(
    db: AsyncSession,
    *,
    report_id: UUID,
    amendment_reason: str,
    title: str | None = None,
    conclusion: Any | None = None,
    summary: str | None = None,
    issuer: User,
    signature_token: str | None = None,
    context: RequestContext | None = None,
) -> tuple[OfficialReport, int]:
    """Emite uma emenda formal retificadora para um laudo oficial (ISO/IEC 17025:2017 §7.8.8).

    - O laudo original ou anterior é mantido estritamente imutável (status auditado histórico).
    - Seu sinalizador `is_latest` é desativado para False.
    - É gerada uma nova linha OfficialReport com version = anterior.version + 1.
    - É gerado um novo PDF binário registrando a justificativa da emenda e o hash SHA-256.
    """
    stmt = (
        select(OfficialReport)
        .options(
            selectinload(OfficialReport.device_sample),
            selectinload(OfficialReport.issued_by),
        )
        .where(OfficialReport.id == report_id)
    )
    prev_report = await db.scalar(stmt)
    if prev_report is None:
        raise NotFoundError("Laudo oficial não encontrado para emissão de emenda.")

    if not prev_report.is_latest:
        raise ValidationDomainError(
            f"O laudo {prev_report.report_number} já foi superado por outra versão e não pode ser emendado diretamente."
        )

    clean_reason = amendment_reason.strip() if amendment_reason else ""
    if len(clean_reason) < 10:
        raise ValidationDomainError(
            "A justificativa técnica formal da emenda deve conter ao menos 10 caracteres (ISO/IEC 17025 §7.8.8)."
        )

    now = utcnow()
    new_version = prev_report.version + 1
    root_id = prev_report.root_report_id or prev_report.id
    base_number = prev_report.report_number.split("-V")[0]
    new_report_number = f"{base_number}-V{new_version}"
    new_auth_token = secrets.token_urlsafe(24)

    new_title = title or prev_report.title
    new_conclusion = conclusion or prev_report.conclusion
    new_summary = summary if summary is not None else prev_report.summary

    # Valida assinatura eletrônica para a emenda
    sig_record: ElectronicSignature | None = None
    if signature_token:
        request_ctx = context or RequestContext(
            ip_address="127.0.0.1", user_agent="LIMS-Internal", request_id="internal"
        )
        sig_record = await signature_service.consume(
            db,
            token=signature_token,
            user=issuer,
            entity_type="OfficialReport",
            entity_id=str(prev_report.id),
            action=SignatureAction.CLOSE,
            context=request_ctx,
        )

    if sig_record is None:
        raise ValidationDomainError(
            "Assinatura eletrônica é obrigatória para emissão de emenda ao laudo."
        )

    sample = prev_report.device_sample
    sample_data = {
        "accession_number": sample.accession_number,
        "lot_number": sample.lot_number or "—",
        "serial_number": sample.serial_number or "—",
        "manufacturer": sample.manufacturer or "—",
        "device_type": sample.commercial_name,
        "collected_at": sample.created_at.strftime("%d/%m/%Y") if sample.created_at else "—",
    }

    # Recupera os ensaios do manifesto anterior
    old_manifest = prev_report.attributes.get("manifest", {}) if prev_report.attributes else {}
    old_tests_manifest = old_manifest.get("tests", [])

    tests_data_pdf: list[dict[str, Any]] = []
    for tm in old_tests_manifest:
        u_str = "—"
        if "uncertainty" in tm:
            u_str = f"± {tm['uncertainty'].get('expanded_uncertainty', '')} {tm.get('unit', '')}".strip()
        tests_data_pdf.append(
            {
                "parameter_name": tm.get("name", "Ensaio"),
                "specification": f"{tm.get('lower_limit') or '—'} a {tm.get('upper_limit') or '—'} {tm.get('unit') or ''}".strip(),
                "result_value": str(tm.get("result_value"))
                if tm.get("result_value") is not None
                else (tm.get("result_text") or "—"),
                "unit": tm.get("unit") or "",
                "uncertainty_u": u_str,
                "outcome": tm.get("outcome") or "APROVADO",
            }
        )

    # Gera novo PDF oficial com carimbo de emenda
    pdf_bytes = generate_official_report_pdf(
        report_number=new_report_number,
        title=new_title,
        conclusion=new_conclusion.value
        if hasattr(new_conclusion, "value")
        else str(new_conclusion),
        summary=new_summary,
        version=new_version,
        is_latest=True,
        amendment_reason=clean_reason,
        supersedes_number=prev_report.report_number,
        sample_data=sample_data,
        tests_data=tests_data_pdf,
        issuer_name=issuer.full_name,
        issuer_role=issuer.role.value if hasattr(issuer.role, "value") else str(issuer.role),
        issued_at_iso=now.strftime("%d/%m/%Y %H:%M:%S"),
        auth_token=new_auth_token,
    )
    new_sha256_hash = hashlib.sha256(pdf_bytes).hexdigest()

    # Desativa vigência do laudo anterior
    prev_report.is_latest = False

    new_manifest = dict(old_manifest)
    new_manifest.update(
        {
            "report_number": new_report_number,
            "version": new_version,
            "amendment_reason": clean_reason,
            "supersedes_report_number": prev_report.report_number,
            "conclusion": new_conclusion.value
            if hasattr(new_conclusion, "value")
            else str(new_conclusion),
            "summary": new_summary,
            "issued_by": issuer.full_name,
            "issued_at": now.isoformat(),
        }
    )

    amended_report = OfficialReport(
        id=uuid4(),
        report_number=new_report_number,
        solicitation_id=prev_report.solicitation_id,
        device_sample_id=prev_report.device_sample_id,
        title=new_title,
        conclusion=new_conclusion,
        summary=new_summary,
        version=new_version,
        root_report_id=root_id,
        supersedes_id=prev_report.id,
        is_latest=True,
        amendment_reason=clean_reason,
        sha256_hash=new_sha256_hash,
        pdf_data=pdf_bytes,
        auth_token=new_auth_token,
        issued_by_id=issuer.id,
        signature_id=sig_record.id,
        attributes={
            "manifest": new_manifest,
            "superseded_report_number": prev_report.report_number,
            "supersedes_id": str(prev_report.id),
        },
        issued_at=now,
    )
    db.add(amended_report)

    audit_entry = await audit_service.append(
        db,
        action=AuditAction.UPDATE,
        entity_type=AuditEntity.OFFICIAL_REPORT.value,
        entity_id=amended_report.id,
        actor=issuer,
        old_value={"superseded_report": prev_report.report_number, "version": prev_report.version},
        new_value=snapshot(amended_report),
        reason=f"Emenda formal (v{new_version}) ao laudo {prev_report.report_number}: {clean_reason}",
        context=context,
        signature_id=sig_record.id,
    )

    await db.commit()
    await db.refresh(amended_report, ["issued_by", "device_sample"])
    return amended_report, audit_entry.sequence


async def get_report_by_id(
    db: AsyncSession,
    report_id: UUID,
) -> OfficialReport:
    """Busca laudo oficial com dados carregados."""
    stmt = (
        select(OfficialReport)
        .options(
            selectinload(OfficialReport.issued_by),
            selectinload(OfficialReport.device_sample),
            selectinload(OfficialReport.solicitation),
            selectinload(OfficialReport.root_report),
            selectinload(OfficialReport.superseded_report),
        )
        .where(OfficialReport.id == report_id)
    )
    report = await db.scalar(stmt)
    if report is None:
        raise NotFoundError("Laudo oficial não encontrado.")
    return report


async def get_report_pdf(
    db: AsyncSession,
    report_id: UUID,
) -> tuple[bytes, str]:
    """Retorna os bytes do PDF e o nome do arquivo para download."""
    report = await db.get(OfficialReport, report_id)
    if report is None:
        raise NotFoundError("Laudo oficial não encontrado.")
    if not report.pdf_data:
        raise NotFoundError("PDF do laudo não está disponível para este registro.")
    filename = f"{report.report_number}.pdf"
    return report.pdf_data, filename


async def verify_report_public(
    db: AsyncSession,
    token_or_hash: str,
) -> dict[str, Any]:
    """Validação pública de autenticidade via QR Code / auth_token ou Hash SHA-256."""
    stmt = (
        select(OfficialReport)
        .options(
            selectinload(OfficialReport.issued_by),
            selectinload(OfficialReport.device_sample),
        )
        .where(
            or_(
                OfficialReport.auth_token == token_or_hash,
                OfficialReport.sha256_hash == token_or_hash,
            )
        )
    )
    report = await db.scalar(stmt)
    if report is None:
        raise NotFoundError("Laudo não localizado ou token/hash de autenticidade inválido.")

    # Revalida hash SHA-256 a partir do PDF real ou manifesto arquivado
    if report.pdf_data:
        calculated_hash = hashlib.sha256(report.pdf_data).hexdigest()
        is_valid = calculated_hash == report.sha256_hash
    else:
        manifest = report.attributes.get("manifest") if report.attributes else {}
        serialized_str = canonical_json(jsonable(manifest))
        calculated_hash = hashlib.sha256(serialized_str.encode("utf-8")).hexdigest()
        is_valid = calculated_hash == report.sha256_hash

    # Identifica o laudo raiz e histórico de todas as versões emitidas
    root_id = report.root_report_id or report.id
    history_stmt = (
        select(OfficialReport)
        .where(or_(OfficialReport.id == root_id, OfficialReport.root_report_id == root_id))
        .order_by(OfficialReport.version.asc())
    )
    family_versions = list((await db.scalars(history_stmt)).all())
    latest_report = max(family_versions, key=lambda r: r.version) if family_versions else report

    history_list = [
        {
            "version": v.version,
            "report_number": v.report_number,
            "is_latest": v.is_latest,
            "amendment_reason": v.amendment_reason,
            "issued_at": v.issued_at.isoformat(),
            "sha256_hash": v.sha256_hash,
        }
        for v in family_versions
    ]

    supersedes_num = None
    if report.attributes and "superseded_report_number" in report.attributes:
        supersedes_num = report.attributes["superseded_report_number"]

    return {
        "is_valid": is_valid,
        "report_number": report.report_number,
        "version": report.version,
        "is_latest": report.is_latest,
        "amendment_reason": report.amendment_reason,
        "supersedes_number": supersedes_num,
        "latest_report_number": latest_report.report_number
        if not report.is_latest
        else report.report_number,
        "sample_acc_number": report.device_sample.accession_number,
        "sample_commercial_name": report.device_sample.commercial_name,
        "sample_serial_number": report.device_sample.serial_number,
        "sample_lot_number": report.device_sample.lot_number,
        "conclusion": report.conclusion,
        "sha256_hash": report.sha256_hash,
        "issued_by_name": report.issued_by.full_name if report.issued_by else "Perito Oficial",
        "issued_at": report.issued_at,
        "history": history_list,
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
