"""Rotas de Emissão, Emenda e Validação de Laudos Oficiais (ISO/IEC 17025 §7.8 e §7.8.8)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request, Response

from app.api.deps import CurrentUser, DbSession, require_roles
from app.core.context import RequestContext
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.official_report import (
    OfficialReportAmendIn,
    OfficialReportBatchIn,
    OfficialReportBatchOut,
    OfficialReportGenerateIn,
    OfficialReportOut,
    OfficialReportPublicVerifyOut,
)
from app.services import report_service

reports_router = APIRouter(prefix="/reports", tags=["Laudos Periciais Oficiais"])

ISSUER_ROLES = (UserRole.ADMIN, UserRole.FISCAL)


@reports_router.post(
    "/official",
    response_model=OfficialReportOut,
    summary="Emitir Laudo Pericial Oficial consolidado com assinatura e PDF assinado",
)
async def create_official_report(
    payload: OfficialReportGenerateIn,
    request: Request,
    response: Response,
    db: DbSession,
    user: User = Depends(require_roles(*ISSUER_ROLES)),
    x_signature_token: str | None = Header(None, alias="X-Signature-Token"),
) -> OfficialReportOut:
    context = RequestContext.from_request(request)
    report, audit_seq = await report_service.generate_official_report(
        db,
        payload=payload,
        issuer=user,
        signature_token=x_signature_token,
        context=context,
    )
    response.headers["X-Audit-Sequence"] = str(audit_seq)
    return OfficialReportOut.model_validate(report)


@reports_router.post(
    "/official/batch",
    response_model=OfficialReportBatchOut,
    summary="Emitir Laudos Periciais Oficiais em lote com manifesto agregado (v1.1.0)",
)
async def create_batch_official_reports(
    payload: OfficialReportBatchIn,
    request: Request,
    response: Response,
    db: DbSession,
    user: User = Depends(require_roles(*ISSUER_ROLES)),
    x_signature_token: str | None = Header(None, alias="X-Signature-Token"),
) -> OfficialReportBatchOut:
    context = RequestContext.from_request(request)
    batch_out, audit_seq = await report_service.generate_batch_official_reports(
        db,
        payload=payload,
        issuer=user,
        signature_token=x_signature_token,
        context=context,
    )
    response.headers["X-Audit-Sequence"] = str(audit_seq)
    return batch_out


@reports_router.post(
    "/official/{report_id}/amend",
    response_model=OfficialReportOut,
    summary="Emitir Emenda Formal Retificadora ao Laudo Oficial (ISO/IEC 17025 §7.8.8)",
)
async def amend_official_report(
    report_id: UUID,
    payload: OfficialReportAmendIn,
    request: Request,
    response: Response,
    db: DbSession,
    user: User = Depends(require_roles(*ISSUER_ROLES)),
    x_signature_token: str | None = Header(None, alias="X-Signature-Token"),
) -> OfficialReportOut:
    """Emite uma nova versão do laudo (vN+1) registrando a justificativa técnica da emenda."""
    context = RequestContext.from_request(request)
    amended_report, audit_seq = await report_service.amend_official_report(
        db,
        report_id=report_id,
        amendment_reason=payload.amendment_reason,
        title=payload.title,
        conclusion=payload.conclusion,
        summary=payload.summary,
        issuer=user,
        signature_token=x_signature_token,
        context=context,
    )
    response.headers["X-Audit-Sequence"] = str(audit_seq)
    return OfficialReportOut.model_validate(amended_report)


@reports_router.get(
    "/official/{report_id}",
    response_model=OfficialReportOut,
    summary="Consultar Laudo Oficial pelo ID",
)
async def get_official_report(
    report_id: UUID,
    db: DbSession,
    _: CurrentUser,
) -> OfficialReportOut:
    report = await report_service.get_report_by_id(db, report_id)
    return OfficialReportOut.model_validate(report)


@reports_router.get(
    "/official/{report_id}/pdf",
    summary="Download do PDF binário do Laudo Pericial Oficial",
)
async def download_report_pdf(
    report_id: UUID,
    db: DbSession,
    _: CurrentUser,
) -> Response:
    pdf_bytes, filename = await report_service.get_report_pdf(db, report_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@reports_router.get(
    "/official/sample/{sample_id}",
    response_model=list[OfficialReportOut],
    summary="Listar laudos oficiais de uma amostra",
)
async def list_sample_reports(
    sample_id: UUID,
    db: DbSession,
    _: CurrentUser,
) -> list[OfficialReportOut]:
    reports = await report_service.list_reports_for_sample(db, sample_id)
    return [OfficialReportOut.model_validate(r) for r in reports]


@reports_router.get(
    "/verify/{auth_token}",
    response_model=OfficialReportPublicVerifyOut,
    summary="Validação pública de autenticidade de laudo via QR Code / token (sem autenticação)",
)
async def verify_report_authenticity(
    auth_token: str,
    db: DbSession,
) -> OfficialReportPublicVerifyOut:
    verification_data = await report_service.verify_report_public(db, auth_token)
    return OfficialReportPublicVerifyOut.model_validate(verification_data)
