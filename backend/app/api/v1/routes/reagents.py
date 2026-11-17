"""Rotas de Gestão de Reagentes, Padrões Analíticos (CRMs) e Insumos (Sprint 7.1)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.deps import CurrentUser, DbSession, require_roles
from app.core.context import RequestContext
from app.models.enums import ReagentType, UserRole
from app.schemas.reagent import (
    ExecutionReagentUsageCreate,
    ExecutionReagentUsageOut,
    ReagentBatchCreate,
    ReagentBatchOut,
    ReagentCreate,
    ReagentOut,
)
from app.services import reagent_service

router = APIRouter(prefix="/reagents", tags=["Reagentes e Padrões Analíticos"])


@router.get("", response_model=list[ReagentOut], summary="Listar catálogo de reagentes e padrões")
async def list_reagents(
    db: DbSession,
    user: CurrentUser,
    reagent_type: ReagentType | None = Query(None, description="Filtrar por tipologia"),
    is_active: bool | None = Query(None, description="Filtrar ativos/inativos"),
    search: str | None = Query(None, description="Buscar por código, nome ou CAS"),
) -> list[ReagentOut]:
    reagents = await reagent_service.list_reagents(
        db,
        reagent_type=reagent_type,
        is_active=is_active,
        search=search,
    )
    return [ReagentOut.model_validate(r) for r in reagents]


@router.post(
    "",
    response_model=ReagentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar reagente ou padrão analítico no catálogo",
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.TECNICO, UserRole.FISCAL))],
)
async def create_reagent(
    payload: ReagentCreate,
    request: Request,
    db: DbSession,
    user: CurrentUser,
) -> ReagentOut:
    reagent = await reagent_service.create_reagent(
        db,
        payload=payload,
        actor=user,
        context=RequestContext.from_request(request),
    )
    return ReagentOut.model_validate(reagent)


@router.get("/batches", response_model=list[ReagentBatchOut], summary="Listar lotes de reagentes")
async def list_batches(
    db: DbSession,
    user: CurrentUser,
    reagent_id: UUID | None = Query(None, description="Filtrar por reagente"),
    available_only: bool = Query(False, description="Apenas lotes válidos e com saldo"),
    expiring_days: int | None = Query(None, description="Expirando nos próximos N dias"),
) -> list[ReagentBatchOut]:
    batches = await reagent_service.list_batches(
        db,
        reagent_id=reagent_id,
        available_only=available_only,
        expiring_days=expiring_days,
    )
    return [ReagentBatchOut.model_validate(b) for b in batches]


@router.get("/{reagent_id}", response_model=ReagentOut, summary="Consultar reagente por ID")
async def get_reagent(reagent_id: UUID, db: DbSession, user: CurrentUser) -> ReagentOut:
    reagent = await reagent_service.get_reagent(db, reagent_id)
    return ReagentOut.model_validate(reagent)


@router.post(
    "/{reagent_id}/batches",
    response_model=ReagentBatchOut,
    status_code=status.HTTP_201_CREATED,
    summary="Dar entrada de lote físico de reagente/padrão (ISO 17025 §6.4)",
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.TECNICO, UserRole.FISCAL))],
)
async def create_batch(
    reagent_id: UUID,
    payload: ReagentBatchCreate,
    request: Request,
    db: DbSession,
    user: CurrentUser,
) -> ReagentBatchOut:
    batch = await reagent_service.create_batch(
        db,
        reagent_id=reagent_id,
        payload=payload,
        actor=user,
        context=RequestContext.from_request(request),
    )
    return ReagentBatchOut.model_validate(batch)


@router.get(
    "/executions/{execution_id}/reagents",
    response_model=list[ExecutionReagentUsageOut],
    summary="Listar insumos e padrões consumidos em uma execução de ensaio",
)
async def list_execution_reagents(
    execution_id: UUID,
    db: DbSession,
    user: CurrentUser,
) -> list[ExecutionReagentUsageOut]:
    usages = await reagent_service.list_execution_usages(db, execution_id=execution_id)
    return [ExecutionReagentUsageOut.model_validate(u) for u in usages]


@router.post(
    "/executions/{execution_id}/consume",
    response_model=ExecutionReagentUsageOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar consumo de insumo analítico em ensaio de bancada",
    description="Aplica intertravamento ISO 17025: rejeita consumo de lote vencido, em quarentena ou sem saldo.",
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.TECNICO))],
)
async def consume_reagent(
    execution_id: UUID,
    payload: ExecutionReagentUsageCreate,
    request: Request,
    db: DbSession,
    user: CurrentUser,
) -> ExecutionReagentUsageOut:
    usage = await reagent_service.consume_reagent_in_execution(
        db,
        execution_id=execution_id,
        batch_id=payload.batch_id,
        quantity_used=payload.quantity_used,
        unit=payload.unit,
        actor=user,
        context=RequestContext.from_request(request),
    )
    return ExecutionReagentUsageOut.model_validate(usage)


__all__ = ["router"]
