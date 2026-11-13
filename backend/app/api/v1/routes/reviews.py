"""Rotas de Revisão Técnica por Pares (Peer Review / ISO/IEC 17025 / Sprint 3.1)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request, Response

from app.api.deps import CurrentUser, DbSession, require_roles
from app.core.context import RequestContext
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.test import LabTestOut
from app.schemas.test_review import (
    TestReviewDecisionIn,
    TestReviewOut,
    TestSubmitReviewIn,
)
from app.services import review_service

reviews_router = APIRouter(prefix="/reviews", tags=["Revisão Técnica por Pares"])

REVIEWER_ROLES = (UserRole.ADMIN, UserRole.FISCAL, UserRole.TECNICO)


@reviews_router.get(
    "/tests/pending",
    response_model=list[LabTestOut],
    summary="Listar ensaios pendentes de revisão técnica por pares",
)
async def list_pending_test_reviews(
    db: DbSession,
    _: User = Depends(require_roles(*REVIEWER_ROLES)),
) -> list[LabTestOut]:
    tests = await review_service.list_pending_reviews(db)
    return [LabTestOut.model_validate(t) for t in tests]


@reviews_router.post(
    "/tests/{test_id}/submit",
    response_model=LabTestOut,
    summary="Submeter ensaio concluído para revisão técnica por pares",
)
async def submit_test(
    test_id: UUID,
    payload: TestSubmitReviewIn,
    request: Request,
    response: Response,
    db: DbSession,
    user: CurrentUser,
) -> LabTestOut:
    context = RequestContext.from_request(request)
    test, audit_seq = await review_service.submit_test_for_review(
        db,
        test_id=test_id,
        payload=payload,
        actor=user,
        context=context,
    )
    response.headers["X-Audit-Sequence"] = str(audit_seq)
    return LabTestOut.model_validate(test)


@reviews_router.post(
    "/tests/{test_id}/decide",
    response_model=TestReviewOut,
    summary="Deliberar sobre ensaio técnico (Aprovar ou Devolver com Ressalva)",
)
async def decide_test_review(
    test_id: UUID,
    payload: TestReviewDecisionIn,
    request: Request,
    response: Response,
    db: DbSession,
    user: User = Depends(require_roles(*REVIEWER_ROLES)),
    x_signature_token: str | None = Header(None, alias="X-Signature-Token"),
) -> TestReviewOut:
    context = RequestContext.from_request(request)
    review, audit_seq = await review_service.record_test_review(
        db,
        test_id=test_id,
        payload=payload,
        reviewer=user,
        signature_token=x_signature_token,
        context=context,
    )
    response.headers["X-Audit-Sequence"] = str(audit_seq)
    return TestReviewOut.model_validate(review)


@reviews_router.get(
    "/tests/{test_id}",
    response_model=list[TestReviewOut],
    summary="Consultar pareceres e histórico de revisões do ensaio",
)
async def get_reviews_for_test(
    test_id: UUID,
    db: DbSession,
    _: CurrentUser,
) -> list[TestReviewOut]:
    reviews = await review_service.get_test_reviews(db, test_id)
    return [TestReviewOut.model_validate(r) for r in reviews]
