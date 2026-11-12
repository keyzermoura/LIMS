"""Rotas de Templates de Checklist e Avaliação de Conferência (Fase 1 / M1.2)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response

from app.api.deps import CurrentUser, DbSession, require_roles
from app.core.context import RequestContext
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.checklist import (
    ChecklistAnswerOut,
    ChecklistEvaluationSubmit,
    ChecklistTemplateOut,
)
from app.schemas.receipt import ReceiptItemOut
from app.services import checklist_service, receipt_service

templates_router = APIRouter(prefix="/checklists", tags=["Checklists e Critérios"])
checklist_eval_router = APIRouter(prefix="/receipts", tags=["Conferência e Checklist"])

WRITE_ROLES = (UserRole.ADMIN, UserRole.FISCAL, UserRole.TECNICO)


@templates_router.get(
    "/templates",
    response_model=list[ChecklistTemplateOut],
    summary="Listar templates de checklist ativos",
)
async def list_templates(
    db: DbSession,
    _: CurrentUser,
    category: str | None = Query(default=None, max_length=100),
) -> list[ChecklistTemplateOut]:
    templates = await checklist_service.list_templates(db, category=category)
    return [ChecklistTemplateOut.model_validate(t) for t in templates]


@templates_router.get(
    "/templates/{template_id}",
    response_model=ChecklistTemplateOut,
    summary="Consultar template de checklist e critérios",
)
async def get_template(
    template_id: UUID,
    db: DbSession,
    _: CurrentUser,
) -> ChecklistTemplateOut:
    template = await checklist_service.get_template(db, template_id)
    return ChecklistTemplateOut.model_validate(template)


@checklist_eval_router.post(
    "/{receipt_id}/items/{item_id}/checklist",
    response_model=ReceiptItemOut,
    summary="Responder checklist e avaliar conformidade do item",
)
async def submit_item_checklist(
    receipt_id: UUID,
    item_id: UUID,
    payload: ChecklistEvaluationSubmit,
    request: Request,
    response: Response,
    db: DbSession,
    user: User = Depends(require_roles(*WRITE_ROLES)),
) -> ReceiptItemOut:
    context = RequestContext.from_request(request)
    _, _, audit_seq = await checklist_service.submit_checklist_answers(
        db,
        receipt_item_id=item_id,
        answers_payload=payload.answers,
        actor=user,
        context=context,
    )
    response.headers["X-Audit-Sequence"] = str(audit_seq)

    receipt = await receipt_service.get_receipt(db, receipt_id)
    refreshed_item = next(i for i in receipt.items if i.id == item_id)
    return ReceiptItemOut.model_validate(refreshed_item)


@checklist_eval_router.get(
    "/{receipt_id}/items/{item_id}/checklist",
    response_model=list[ChecklistAnswerOut],
    summary="Consultar respostas formalizadas de checklist do item",
)
async def get_item_checklist_answers(
    receipt_id: UUID,
    item_id: UUID,
    db: DbSession,
    _: CurrentUser,
) -> list[ChecklistAnswerOut]:
    answers = await checklist_service.get_answers_for_item(db, item_id)
    return [ChecklistAnswerOut.model_validate(a) for a in answers]
