"""Rotas Públicas e Verificação Externa de Documentos Oficiais (ISO/IEC 17025 §7.8).

Conforme ESPECIFICACAO_CAMADA_INTEGRACAO_LIMS.md, 21 CFR Part 11 e ALCOA+.
"""

from __future__ import annotations

from fastapi import APIRouter, Response
from sqlalchemy import or_, select

from app.api.deps import DbSession
from app.core.errors import NotFoundError
from app.models.official_report import OfficialReport
from app.schemas.official_report import OfficialReportPublicVerifyOut
from app.services import report_service

public_reports_router = APIRouter(prefix="/public/reports", tags=["Verificação Pública de Documentos"])


@public_reports_router.get(
    "/verify/{token_or_hash}",
    response_model=OfficialReportPublicVerifyOut,
    summary="Validação pública de autenticidade de laudo via QR Code / Token ou Hash SHA-256",
)
async def verify_public_report(
    token_or_hash: str,
    db: DbSession,
) -> OfficialReportPublicVerifyOut:
    """Valida a integridade matemática, versão e autenticidade do laudo sem necessidade de autenticação."""
    verification_data = await report_service.verify_report_public(db, token_or_hash)
    return OfficialReportPublicVerifyOut.model_validate(verification_data)


@public_reports_router.get(
    "/{token_or_hash}/pdf",
    summary="Download público do PDF autêntico do laudo pericial oficial",
)
async def download_public_report_pdf(
    token_or_hash: str,
    db: DbSession,
) -> Response:
    """Permite download do arquivo PDF original caso o token ou hash corresponda ao laudo pericial."""
    stmt = (
        select(OfficialReport)
        .where(
            or_(
                OfficialReport.auth_token == token_or_hash,
                OfficialReport.sha256_hash == token_or_hash,
            )
        )
    )
    report = await db.scalar(stmt)
    if report is None or not report.pdf_data:
        raise NotFoundError("Laudo oficial não localizado ou PDF indisponível.")

    filename = f"{report.report_number}.pdf"
    return Response(
        content=report.pdf_data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )
