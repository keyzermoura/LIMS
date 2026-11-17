"""Rotas REST para Controle Estatístico de Processo e Westgard (H2.5 / ISO 17025 §7.7)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.deps import CurrentUser, DbSession, require_roles
from app.core.context import RequestContext
from app.models.enums import QCStatus, UserRole
from app.schemas.qc_spc import LeveyJenningsChartData, QCRunCreate, QCRunOut, QCRunResolve
from app.services import qc_spc_service

router = APIRouter(prefix="/spc", tags=["Controle Estatístico de Processo (CEP / Westgard)"])


@router.post(
    "/runs",
    response_model=QCRunOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar corrida de Controle de Qualidade Interno (CQI) com avaliação de Westgard",
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.TECNICO, UserRole.FISCAL))],
)
async def create_qc_run(
    payload: QCRunCreate,
    request: Request,
    db: DbSession,
    user: CurrentUser,
) -> QCRunOut:
    run = await qc_spc_service.record_qc_run(
        db,
        payload=payload,
        actor=user,
        context=RequestContext.from_request(request),
    )
    return QCRunOut.model_validate(run)


@router.get(
    "/runs",
    response_model=list[QCRunOut],
    summary="Listar corridas de CQI com filtros analíticos",
)
async def list_qc_runs(
    db: DbSession,
    user: CurrentUser,
    method_id: UUID | None = Query(None, description="Filtrar por método analítico"),
    status_filter: QCStatus | None = Query(None, alias="status", description="Filtrar por status"),
    is_active_violation: bool | None = Query(None, description="Filtrar apenas violações ativas"),
) -> list[QCRunOut]:
    runs = await qc_spc_service.list_qc_runs(
        db,
        method_id=method_id,
        status_filter=status_filter,
        is_active_violation=is_active_violation,
    )
    return [QCRunOut.model_validate(r) for r in runs]


@router.get(
    "/methods/{method_id}/chart",
    response_model=LeveyJenningsChartData,
    summary="Obter série temporal e limites da Carta de Controle Levey-Jennings",
)
async def get_levey_jennings_chart(
    method_id: UUID,
    db: DbSession,
    user: CurrentUser,
) -> LeveyJenningsChartData:
    return await qc_spc_service.get_qc_chart_data(db, method_id=method_id)


@router.post(
    "/runs/{run_id}/resolve",
    response_model=QCRunOut,
    summary="Registrar parecer técnico corretivo e desbloquear violação de Westgard",
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.TECNICO, UserRole.FISCAL))],
)
async def resolve_qc_violation_endpoint(
    run_id: UUID,
    payload: QCRunResolve,
    request: Request,
    db: DbSession,
    user: CurrentUser,
) -> QCRunOut:
    run = await qc_spc_service.resolve_qc_violation(
        db,
        run_id=run_id,
        payload=payload,
        actor=user,
        context=RequestContext.from_request(request),
    )
    return QCRunOut.model_validate(run)
