"""Trilha de auditoria — leitura restrita e verificação de integridade."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, Request, Response, UploadFile
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession, require_roles
from app.core.config import settings
from app.core.context import RequestContext
from app.core.errors import ValidationDomainError
from app.models.audit_log import AuditLog
from app.models.enums import AuditAction, AuditEntity, UserRole
from app.models.user import User
from app.schemas.audit import (
    AuditExportRequest,
    AuditExportVerifyResponse,
    AuditLogDetailOut,
    AuditLogOut,
    AuditVerifyResponse,
)
from app.schemas.common import Page
from app.services import audit_export_service, audit_service

router = APIRouter(prefix="/audit", tags=["Trilha de Auditoria"])

AUDIT_ROLES = (UserRole.ADMIN, UserRole.AUDITOR)


@router.get(
    "",
    response_model=Page[AuditLogOut],
    summary="Consultar trilha de auditoria",
    description=(
        "Somente leitura, restrita a AUDITOR e ADMIN. A ordenação padrão é "
        "decrescente por sequência (evento mais recente primeiro)."
    ),
)
async def list_audit_logs(
    db: DbSession,
    user: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    entity_type: str | None = Query(None, max_length=64),
    entity_id: str | None = Query(None, max_length=64),
    actor_id: UUID | None = Query(None),
    action: AuditAction | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    search: str | None = Query(None, max_length=120),
    _role: User = Depends(require_roles(*AUDIT_ROLES)),
) -> Page[AuditLogOut]:
    stmt = audit_service.filtered_query(
        entity_type=entity_type,
        entity_id=entity_id,
        actor_id=actor_id,
        action=action,
        date_from=date_from,
        date_to=date_to,
        search=search,
    )

    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    stmt = (
        stmt.order_by(AuditLog.sequence.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return Page[AuditLogOut].build(
        [AuditLogOut.model_validate(row) for row in rows], int(total), page, size
    )


@router.get(
    "/{log_id}",
    response_model=AuditLogDetailOut,
    summary="Detalhar evento de auditoria (inclui payload canônico)",
)
async def get_audit_log(
    log_id: int,
    db: DbSession,
    user: CurrentUser,
    _role: User = Depends(require_roles(*AUDIT_ROLES)),
) -> AuditLogDetailOut:
    from app.core.errors import NotFoundError

    row = await db.get(AuditLog, log_id)
    if row is None:
        raise NotFoundError("Evento de auditoria não encontrado.")
    return AuditLogDetailOut.model_validate(row)


@router.post(
    "/verify",
    response_model=AuditVerifyResponse,
    summary="Verificar integridade da cadeia de auditoria",
    description=(
        "Recalcula SHA-256 e HMAC de cada registro, valida a sequência e o "
        "encadeamento. A própria verificação é registrada na trilha."
    ),
)
async def verify_audit_chain(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    from_sequence: int = Query(1, ge=1),
    _role: User = Depends(require_roles(*AUDIT_ROLES)),
) -> AuditVerifyResponse:
    report = await audit_service.verify_chain(db, from_sequence=from_sequence)

    await audit_service.append(
        db,
        action=AuditAction.INTEGRITY_CHECK,
        entity_type=AuditEntity.AUDIT_LOG.value,
        entity_id="chain",
        actor=user,
        new_value={
            "ok": report["ok"],
            "checked": report["checked"],
            "last_sequence": report["last_sequence"],
            "issues": len(report["issues"]),
        },
        reason="Verificação de integridade da trilha de auditoria.",
        context=RequestContext.from_request(request),
    )
    await db.commit()
    return AuditVerifyResponse.model_validate(report)


@router.post(
    "/export",
    summary="Exportar trilha assinada (CSV/JSON + manifesto)",
    description=(
        "Gera um pacote ZIP com o recorte da trilha em CSV ou JSON, o arquivo "
        "canônico `events.jsonl` e um manifesto SHA-256/HMAC. A exportação é "
        "registrada na própria trilha. Restrito a AUDITOR e ADMIN."
    ),
    response_class=Response,
    responses={
        200: {
            "content": {"application/zip": {}},
            "description": "Pacote ZIP com eventos e manifesto assinado.",
        }
    },
)
async def export_audit_trail(
    request: Request,
    body: AuditExportRequest,
    db: DbSession,
    user: CurrentUser,
    _role: User = Depends(require_roles(*AUDIT_ROLES)),
) -> Response:
    filters = body.model_dump(exclude={"format"})
    bundle = await audit_export_service.export_bundle(
        db,
        actor=user,
        filters=filters,
        fmt=body.format,
        context=RequestContext.from_request(request),
    )

    event = await audit_service.append(
        db,
        action=AuditAction.EXPORT,
        entity_type=AuditEntity.AUDIT_LOG.value,
        entity_id=str(bundle.manifest["export_id"]),
        actor=user,
        new_value={
            "export_id": bundle.manifest["export_id"],
            "format": body.format,
            "scope": bundle.manifest["scope"],
            "record_count": bundle.manifest["record_count"],
            "first_sequence": bundle.manifest["first_sequence"],
            "last_sequence": bundle.manifest["last_sequence"],
            "head_hash": bundle.manifest["head_hash"],
            "manifest_hash": bundle.manifest_hash,
            "manifest_hmac": bundle.hmac,
            "artifact_sha256": bundle.artifact_sha256,
        },
        reason="Exportação assinada da trilha de auditoria.",
        context=RequestContext.from_request(request),
    )
    await db.commit()

    headers = {
        "Content-Disposition": f'attachment; filename="{bundle.filename}"',
        "X-Audit-Export-Id": str(bundle.manifest["export_id"]),
        "X-Audit-Export-Sequence": str(event.sequence),
        "X-Audit-Export-Manifest-Hash": bundle.manifest_hash,
    }
    return Response(
        content=bundle.content,
        media_type="application/zip",
        headers=headers,
    )


@router.post(
    "/export/verify",
    response_model=AuditExportVerifyResponse,
    summary="Verificar arquivo exportado da trilha",
    description=(
        "Recalcula o hash/HMAC do manifesto e dos arquivos, valida a cadeia "
        "interna dos registros e ancora a cabeça exportada no banco atual. "
        "A verificação também é registrada na trilha."
    ),
)
async def verify_audit_export(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    file: UploadFile = File(..., description="Pacote ZIP gerado por /audit/export."),
    _role: User = Depends(require_roles(*AUDIT_ROLES)),
) -> AuditExportVerifyResponse:
    content = await file.read(settings.AUDIT_EXPORT_MAX_BYTES + 1)
    if len(content) > settings.AUDIT_EXPORT_MAX_BYTES:
        raise ValidationDomainError(
            "O arquivo excede o tamanho máximo aceito para verificação.",
            details={"max_bytes": settings.AUDIT_EXPORT_MAX_BYTES},
        )

    report = await audit_export_service.verify_bundle(db, content)

    await audit_service.append(
        db,
        action=AuditAction.EXPORT_VERIFIED,
        entity_type=AuditEntity.AUDIT_LOG.value,
        entity_id=str(report.get("export_id") or "unknown")[:64],
        actor=user,
        new_value={
            "export_id": report.get("export_id"),
            "filename": file.filename,
            "ok": report["ok"],
            "checked": report["checked"],
            "first_sequence": report.get("first_sequence"),
            "last_sequence": report.get("last_sequence"),
            "head_hash": report.get("head_hash"),
            "manifest_hash_ok": report["manifest_hash_ok"],
            "data_hash_ok": report["data_hash_ok"],
            "chain_ok": report["chain_ok"],
            "matches_database": report["matches_database"],
            "issues": len(report["issues"]),
        },
        reason="Verificação de arquivo exportado da trilha de auditoria.",
        context=RequestContext.from_request(request),
    )
    await db.commit()

    return AuditExportVerifyResponse.model_validate(report)
