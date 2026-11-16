"""Rotas de Cálculo de Incerteza de Medição GUM e Regras de Decisão ILAC-G8 (Sprint 4.2)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, Query, Request, status

from app.api.deps import CurrentUser, DbSession
from app.core.context import RequestContext
from app.models.enums import ConformityStatus
from app.schemas.uncertainty import (
    UncertaintyBudgetCreateIn,
    UncertaintyBudgetOut,
    UncertaintyCalculationOut,
    UncertaintySimulateIn,
)
from app.services import uncertainty_service

router = APIRouter(
    prefix="/uncertainty",
    tags=["Incerteza de Medição & ILAC-G8 (Fase 4)"],
)


@router.post("/simulate", response_model=UncertaintyCalculationOut)
async def simulate_uncertainty(
    payload: UncertaintySimulateIn,
    _: CurrentUser,
) -> UncertaintyCalculationOut:
    """Simula o cálculo GUM (Tipo A/B, uc, v_eff, k, U) e decisão ILAC-G8 sem persistir."""
    return uncertainty_service.calculate_uncertainty_budget(payload)


@router.post(
    "/budgets",
    response_model=UncertaintyBudgetOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_uncertainty_budget(
    payload: UncertaintyBudgetCreateIn,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    x_signature_token: Annotated[str | None, Header(alias="X-Signature-Token")] = None,
) -> UncertaintyBudgetOut:
    """Calcula, persiste e audita o orçamento de incerteza metrológica vinculado ao ensaio."""
    ctx = RequestContext(
        ip_address=request.client.host if request.client else "127.0.0.1",
        user_agent=request.headers.get("user-agent", "LIMS-Client"),
        request_id=request.headers.get("x-request-id", "api"),
    )
    budget, _ = await uncertainty_service.create_uncertainty_budget(
        db,
        payload=payload,
        actor=current_user,
        signature_token=x_signature_token,
        context=ctx,
    )
    return uncertainty_service.to_budget_out(budget)


@router.get("/budgets", response_model=list[UncertaintyBudgetOut])
async def list_uncertainty_budgets(
    db: DbSession,
    _: CurrentUser,
    lab_test_id: UUID | None = None,
    method_id: UUID | None = None,
    execution_id: UUID | None = None,
    conformity_status: ConformityStatus | None = Query(default=None),
) -> list[UncertaintyBudgetOut]:
    """Lista os orçamentos de incerteza GUM registrados com filtros opcionais."""
    budgets = await uncertainty_service.list_uncertainty_budgets(
        db,
        lab_test_id=lab_test_id,
        method_id=method_id,
        execution_id=execution_id,
        conformity_status=conformity_status,
    )
    return [uncertainty_service.to_budget_out(b) for b in budgets]


@router.get("/budgets/{budget_id}", response_model=UncertaintyBudgetOut)
async def get_uncertainty_budget(
    budget_id: UUID,
    db: DbSession,
    _: CurrentUser,
) -> UncertaintyBudgetOut:
    """Retorna os detalhes completos de um orçamento de incerteza específico."""
    budget = await uncertainty_service.get_uncertainty_budget(db, budget_id)
    return uncertainty_service.to_budget_out(budget)
