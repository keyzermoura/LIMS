"""Rotas Públicas e Verificação Externa de Documentos Oficiais (Sprint 5.4 / Interoperabilidade).

Conforme ESPECIFICACAO_CAMADA_INTEGRACAO_LIMS.md e ALCOA+.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import DbSession
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
    """Valida a integridade matemática e autenticidade do laudo sem necessidade de autenticação."""
    verification_data = await report_service.verify_report_public(db, token_or_hash)
    return OfficialReportPublicVerifyOut.model_validate(verification_data)
