"""Rotas de BI, Indicadores Operacionais e Controle Estatístico Metrológico (Fase 5 / Sprint 5.1).

Conforme ISO/IEC 17025:2017 (§8.8, §7.7) e 21 CFR Part 11.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.schemas.analytics import OperationalAnalyticsOut, QualityControlAnalyticsOut
from app.services import analytics_service

router = APIRouter(
    prefix="/analytics",
    tags=["Painéis e Indicadores BI (Fase 5)"],
)


@router.get("/operational", response_model=OperationalAnalyticsOut)
async def get_operational_metrics(
    db: DbSession,
    _: CurrentUser,
) -> OperationalAnalyticsOut:
    """Retorna os indicadores consolidados de tempo de ciclo (TAT), backlog e conformidade."""
    return await analytics_service.get_operational_analytics(db)


@router.get("/quality-control", response_model=QualityControlAnalyticsOut)
async def get_quality_control_chart(
    db: DbSession,
    _: CurrentUser,
    method_id: Annotated[UUID | None, Query(description="Filtrar por método analítico específico")] = None,
) -> QualityControlAnalyticsOut:
    """Retorna dados de controle estatístico (Cartas de Shewhart e Regras de Westgard)."""
    return await analytics_service.get_quality_control_analytics(db, method_id=method_id)
