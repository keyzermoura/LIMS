"""Rotas de Investigação de Desvios Analíticos OOS e OOT (Sprint 7.2 / ISO 17025 §7.10)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.deps import CurrentUser, DbSession, require_roles
from app.core.context import RequestContext
from app.models.enums import DeviationType, OOSInvestigationStatus, UserRole
from app.schemas.oos_investigation import (
    OOSCloseRequest,
    OOSInvestigationCreate,
    OOSInvestigationOut,
    OOSPhase1Update,
    OOSPhase2Update,
)
from app.services import oos_service

router = APIRouter(prefix="/oos", tags=["Investigação de Desvios OOS/OOT"])


@router.post(
    "",
    response_model=OOSInvestigationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Abrir formalmente uma investigação de desvio analítico OOS/OOT",
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.TECNICO, UserRole.FISCAL))],
)
async def create_investigation(
    payload: OOSInvestigationCreate,
    request: Request,
    db: DbSession,
    user: CurrentUser,
) -> OOSInvestigationOut:
    investigation = await oos_service.create_investigation(
        db,
        payload=payload,
        actor=user,
        context=RequestContext.from_request(request),
    )
    return OOSInvestigationOut.model_validate(investigation)


@router.get(
    "",
    response_model=list[OOSInvestigationOut],
    summary="Listar investigações OOS/OOT com filtros analíticos",
)
async def list_investigations(
    db: DbSession,
    user: CurrentUser,
    lab_test_id: UUID | None = Query(None, description="Filtrar por ensaio"),
    status_filter: OOSInvestigationStatus | None = Query(None, alias="status", description="Filtrar por status"),
    deviation_type: DeviationType | None = Query(None, description="OOS ou OOT"),
    is_open: bool | None = Query(None, description="Filtrar apenas abertas/fechadas"),
    search: str | None = Query(None, description="Buscar por número de investigação"),
) -> list[OOSInvestigationOut]:
    investigations = await oos_service.list_investigations(
        db,
        lab_test_id=lab_test_id,
        status_filter=status_filter,
        deviation_type=deviation_type,
        is_open=is_open,
        search=search,
    )
    return [OOSInvestigationOut.model_validate(inv) for inv in investigations]


@router.get(
    "/{investigation_id}",
    response_model=OOSInvestigationOut,
    summary="Consultar investigação OOS por ID",
)
async def get_investigation(
    investigation_id: UUID,
    db: DbSession,
    user: CurrentUser,
) -> OOSInvestigationOut:
    investigation = await oos_service.get_investigation(db, investigation_id)
    return OOSInvestigationOut.model_validate(investigation)


@router.put(
    "/{investigation_id}/phase1",
    response_model=OOSInvestigationOut,
    summary="Registrar e concluir a Fase I da investigação (Laboratorial Imediata)",
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.TECNICO, UserRole.FISCAL))],
)
async def record_phase_1(
    investigation_id: UUID,
    payload: OOSPhase1Update,
    request: Request,
    db: DbSession,
    user: CurrentUser,
) -> OOSInvestigationOut:
    investigation = await oos_service.record_phase_1(
        db,
        investigation_id=investigation_id,
        payload=payload,
        actor=user,
        context=RequestContext.from_request(request),
    )
    return OOSInvestigationOut.model_validate(investigation)


@router.put(
    "/{investigation_id}/phase2",
    response_model=OOSInvestigationOut,
    summary="Registrar Fase II, resultados de re-ensaio, causa raiz e vínculo com CAPA",
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.TECNICO, UserRole.FISCAL))],
)
async def record_phase_2(
    investigation_id: UUID,
    payload: OOSPhase2Update,
    request: Request,
    db: DbSession,
    user: CurrentUser,
) -> OOSInvestigationOut:
    investigation = await oos_service.record_phase_2(
        db,
        investigation_id=investigation_id,
        payload=payload,
        actor=user,
        context=RequestContext.from_request(request),
    )
    return OOSInvestigationOut.model_validate(investigation)


@router.post(
    "/{investigation_id}/close",
    response_model=OOSInvestigationOut,
    summary="Encerrar formalmente a investigação OOS/OOT (Coordenação/Fiscal)",
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.FISCAL))],
)
async def close_investigation(
    investigation_id: UUID,
    payload: OOSCloseRequest,
    request: Request,
    db: DbSession,
    user: CurrentUser,
) -> OOSInvestigationOut:
    investigation = await oos_service.close_investigation(
        db,
        investigation_id=investigation_id,
        payload=payload,
        actor=user,
        context=RequestContext.from_request(request),
    )
    return OOSInvestigationOut.model_validate(investigation)


__all__ = ["router"]
