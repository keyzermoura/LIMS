"""Rotas de Decisões Técnicas de Recebimento e Revisão da Coordenação (Fase 1 / M1.2)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response

from app.api.deps import CurrentUser, DbSession, require_roles
from app.core.context import RequestContext
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.decision import (
    CoordinationReviewAction,
    CoordinationReviewOut,
    ReceiptDecisionCreate,
    ReceiptDecisionOut,
)
from app.services import decision_service

decisions_router = APIRouter(prefix="/receipts", tags=["Decisões de Recebimento"])
coordination_router = APIRouter(prefix="/coordination", tags=["Revisão da Coordenação"])

TECHNICAL_ROLES = (UserRole.ADMIN, UserRole.FISCAL, UserRole.TECNICO)
COORDINATION_ROLES = (UserRole.ADMIN, UserRole.FISCAL)


@decisions_router.post(
    "/{receipt_id}/items/{item_id}/decisions",
    response_model=ReceiptDecisionOut,
    summary="Registrar decisão técnica formalizada sobre item de recebimento",
)
async def record_item_decision(
    receipt_id: UUID,
    item_id: UUID,
    payload: ReceiptDecisionCreate,
    request: Request,
    response: Response,
    db: DbSession,
    user: User = Depends(require_roles(*TECHNICAL_ROLES)),
) -> ReceiptDecisionOut:
    context = RequestContext.from_request(request)
    decision, audit_seq = await decision_service.record_receipt_decision(
        db,
        receipt_item_id=item_id,
        payload=payload,
        actor=user,
        context=context,
    )
    response.headers["X-Audit-Sequence"] = str(audit_seq)
    return ReceiptDecisionOut.model_validate(decision)


@decisions_router.get(
    "/{receipt_id}/items/{item_id}/decisions",
    response_model=list[ReceiptDecisionOut],
    summary="Consultar histórico de decisões técnicas do item",
)
async def get_item_decisions(
    receipt_id: UUID,
    item_id: UUID,
    db: DbSession,
    _: CurrentUser,
) -> list[ReceiptDecisionOut]:
    decisions = await decision_service.get_decisions_for_item(db, item_id)
    return [ReceiptDecisionOut.model_validate(d) for d in decisions]


@coordination_router.get(
    "/reviews/pending",
    response_model=list[CoordinationReviewOut],
    summary="Listar revisões pendentes de deliberação pela coordenação",
)
async def list_pending_reviews(
    db: DbSession,
    _: User = Depends(require_roles(*COORDINATION_ROLES)),
) -> list[CoordinationReviewOut]:
    reviews = await decision_service.list_pending_reviews(db)
    return [CoordinationReviewOut.model_validate(r) for r in reviews]


@coordination_router.post(
    "/reviews/{review_id}/action",
    response_model=CoordinationReviewOut,
    summary="Deliberar sobre revisão técnica (Aprovar, Devolver ou Rejeitar)",
)
async def review_decision_action(
    review_id: UUID,
    payload: CoordinationReviewAction,
    request: Request,
    response: Response,
    db: DbSession,
    user: User = Depends(require_roles(*COORDINATION_ROLES)),
) -> CoordinationReviewOut:
    context = RequestContext.from_request(request)
    review, audit_seq = await decision_service.review_coordination_decision(
        db,
        review_id=review_id,
        payload=payload,
        reviewer=user,
        context=context,
    )
    response.headers["X-Audit-Sequence"] = str(audit_seq)
    return CoordinationReviewOut.model_validate(review)
