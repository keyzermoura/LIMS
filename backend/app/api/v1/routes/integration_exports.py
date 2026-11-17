"""Rotas de exportação analítica corporativa com paginação determinística por cursor.

Fornece endpoints REST otimizados para ingestão em pipelines de Business Intelligence (BI),
Data Lakes corporativos e auditoria externa de metrologia (ISO/IEC 17025 §7.8 e ALCOA+).
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, Response

from app.api import deps
from app.core.errors import ForbiddenError
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.integration import (
    CursorPage,
    ExportQcMetricItem,
    ExportReportItem,
    ExportSampleItem,
    ExportTestItem,
)
from app.services import integration_export_service

router = APIRouter(prefix="/integration/exports", tags=["Integrações & BI"])


def verify_export_access(current_user: User) -> None:
    """Verifica autorização de usuário humano ou serviço M2M."""
    if current_user.role == UserRole.SERVICE:
        scopes = getattr(current_user, "_service_scopes", [])
        allowed_scopes = {"integration:read", "reports:read", "tests:read", "samples:read", "*"}
        if not scopes or not any(s in allowed_scopes for s in scopes):
            raise ForbiddenError("Credencial de serviço sem escopo de leitura analítica.")
        return

    # Usuário interativo
    allowed_roles = {UserRole.ADMIN, UserRole.AUDITOR, UserRole.FISCAL, UserRole.TECNICO}
    if current_user.role not in allowed_roles:
        raise ForbiddenError("Acesso restrito à equipe técnica e fiscalização.")


@router.get(
    "/tests",
    response_model=CursorPage[ExportTestItem],
    summary="Exportar ensaios laboratoriais com paginação por cursor",
)
async def export_tests(
    db: deps.DbSession,
    current_user: Annotated[User, Depends(deps.get_current_user)],
    response: Response,
    updated_since: datetime | None = Query(None, description="Filtro incremental ISO-8601"),
    cursor: str | None = Query(None, description="Cursor opaco da página anterior"),
    limit: int = Query(50, ge=1, le=500, description="Quantidade por lote"),
    accept: str | None = Header(None),
) -> CursorPage[ExportTestItem]:
    verify_export_access(current_user)
    if accept and "application/vnd.lims.v1+json" in accept:
        response.headers["Content-Type"] = "application/vnd.lims.v1+json"

    return await integration_export_service.export_tests_cursor(
        db, updated_since=updated_since, cursor=cursor, limit=limit
    )


@router.get(
    "/reports",
    response_model=CursorPage[ExportReportItem],
    summary="Exportar laudos oficiais homologados com paginação por cursor",
)
async def export_reports(
    db: deps.DbSession,
    current_user: Annotated[User, Depends(deps.get_current_user)],
    response: Response,
    updated_since: datetime | None = Query(None, description="Filtro incremental ISO-8601"),
    cursor: str | None = Query(None, description="Cursor opaco da página anterior"),
    limit: int = Query(50, ge=1, le=500, description="Quantidade por lote"),
    accept: str | None = Header(None),
) -> CursorPage[ExportReportItem]:
    verify_export_access(current_user)
    if accept and "application/vnd.lims.v1+json" in accept:
        response.headers["Content-Type"] = "application/vnd.lims.v1+json"

    return await integration_export_service.export_reports_cursor(
        db, updated_since=updated_since, cursor=cursor, limit=limit
    )


@router.get(
    "/samples",
    response_model=CursorPage[ExportSampleItem],
    summary="Exportar amostras operacionais com paginação por cursor",
)
async def export_samples(
    db: deps.DbSession,
    current_user: Annotated[User, Depends(deps.get_current_user)],
    response: Response,
    updated_since: datetime | None = Query(None, description="Filtro incremental ISO-8601"),
    cursor: str | None = Query(None, description="Cursor opaco da página anterior"),
    limit: int = Query(50, ge=1, le=500, description="Quantidade por lote"),
    accept: str | None = Header(None),
) -> CursorPage[ExportSampleItem]:
    verify_export_access(current_user)
    if accept and "application/vnd.lims.v1+json" in accept:
        response.headers["Content-Type"] = "application/vnd.lims.v1+json"

    return await integration_export_service.export_samples_cursor(
        db, updated_since=updated_since, cursor=cursor, limit=limit
    )


@router.get(
    "/qc-metrics",
    response_model=ExportQcMetricItem,
    summary="Resumo analítico metrológico consolidado para dashboards",
)
async def get_qc_metrics(
    db: deps.DbSession,
    current_user: Annotated[User, Depends(deps.get_current_user)],
    response: Response,
    accept: str | None = Header(None),
) -> ExportQcMetricItem:
    verify_export_access(current_user)
    if accept and "application/vnd.lims.v1+json" in accept:
        response.headers["Content-Type"] = "application/vnd.lims.v1+json"

    return await integration_export_service.get_qc_metrics_export(db)
