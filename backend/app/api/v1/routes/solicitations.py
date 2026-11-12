"""Rotas de Solicitações e Itens Declarados (Fase 1 / M1.1)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response, status

from app.api.deps import CurrentUser, DbSession, require_roles
from app.core.context import RequestContext
from app.models.enums import SolicitationStatus, UserRole
from app.models.user import User
from app.schemas.common import Page
from app.schemas.receipt import ReceiptCreate, ReceiptOut
from app.schemas.solicitation import (
    SolicitationCreate,
    SolicitationOut,
    SolicitationSubmit,
    SolicitationUpdate,
)
from app.services import receipt_service, solicitation_service

router = APIRouter(prefix="/solicitations", tags=["Solicitações"])

WRITE_ROLES = (UserRole.ADMIN, UserRole.FISCAL, UserRole.TECNICO)


@router.post(
    "",
    response_model=SolicitationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar nova solicitação de ensaio ou fiscalização",
)
async def create_solicitation(
    payload: SolicitationCreate,
    request: Request,
    response: Response,
    db: DbSession,
    user: User = Depends(require_roles(*WRITE_ROLES)),
) -> SolicitationOut:
    context = RequestContext.from_request(request)
    solicitation, audit_seq = await solicitation_service.create_solicitation(
        db, payload=payload, actor=user, context=context
    )
    response.headers["X-Audit-Sequence"] = str(audit_seq)
    out = SolicitationOut.model_validate(solicitation)
    out.has_receipt = solicitation.receipt is not None
    return out


@router.get(
    "",
    response_model=Page[SolicitationOut],
    summary="Listar solicitações",
)
async def list_solicitations(
    db: DbSession,
    _: CurrentUser,
    status_filter: SolicitationStatus | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None, max_length=120),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> Page[SolicitationOut]:
    items, total = await solicitation_service.list_solicitations(
        db, status=status_filter, search=search, page=page, size=size
    )
    out_items: list[SolicitationOut] = []
    for item in items:
        out = SolicitationOut.model_validate(item)
        out.has_receipt = item.receipt is not None
        out_items.append(out)
    return Page.build(items=out_items, total=total, page=page, size=size)


@router.get(
    "/{solicitation_id}",
    response_model=SolicitationOut,
    summary="Consultar detalhes de uma solicitação",
)
async def get_solicitation(
    solicitation_id: UUID,
    db: DbSession,
    _: CurrentUser,
) -> SolicitationOut:
    solicitation = await solicitation_service.get_solicitation(db, solicitation_id)
    out = SolicitationOut.model_validate(solicitation)
    out.has_receipt = solicitation.receipt is not None
    return out


@router.put(
    "/{solicitation_id}",
    response_model=SolicitationOut,
    summary="Atualizar solicitação em rascunho",
)
async def update_solicitation(
    solicitation_id: UUID,
    payload: SolicitationUpdate,
    request: Request,
    response: Response,
    db: DbSession,
    user: User = Depends(require_roles(*WRITE_ROLES)),
) -> SolicitationOut:
    context = RequestContext.from_request(request)
    solicitation, audit_seq = await solicitation_service.update_solicitation(
        db, solicitation_id=solicitation_id, payload=payload, actor=user, context=context
    )
    response.headers["X-Audit-Sequence"] = str(audit_seq)
    out = SolicitationOut.model_validate(solicitation)
    out.has_receipt = solicitation.receipt is not None
    return out


@router.post(
    "/{solicitation_id}/submit",
    response_model=SolicitationOut,
    summary="Submeter solicitação para recebimento",
)
async def submit_solicitation(
    solicitation_id: UUID,
    payload: SolicitationSubmit,
    request: Request,
    response: Response,
    db: DbSession,
    user: User = Depends(require_roles(*WRITE_ROLES)),
) -> SolicitationOut:
    context = RequestContext.from_request(request)
    solicitation, audit_seq = await solicitation_service.submit_solicitation(
        db, solicitation_id=solicitation_id, payload=payload, actor=user, context=context
    )
    response.headers["X-Audit-Sequence"] = str(audit_seq)
    out = SolicitationOut.model_validate(solicitation)
    out.has_receipt = solicitation.receipt is not None
    return out


@router.post(
    "/{solicitation_id}/cancel",
    response_model=SolicitationOut,
    summary="Cancelar solicitação",
)
async def cancel_solicitation(
    solicitation_id: UUID,
    request: Request,
    response: Response,
    db: DbSession,
    reason: str = Query(min_length=5, max_length=500),
    version: int = Query(ge=1),
    user: User = Depends(require_roles(*WRITE_ROLES)),
) -> SolicitationOut:
    context = RequestContext.from_request(request)
    solicitation, audit_seq = await solicitation_service.cancel_solicitation(
        db, solicitation_id=solicitation_id, reason=reason, actor=user, version=version, context=context
    )
    response.headers["X-Audit-Sequence"] = str(audit_seq)
    out = SolicitationOut.model_validate(solicitation)
    out.has_receipt = solicitation.receipt is not None
    return out


@router.post(
    "/{solicitation_id}/receipt",
    response_model=ReceiptOut,
    status_code=status.HTTP_201_CREATED,
    summary="Formalizar chegada física e criar recebimento",
)
async def create_receipt_for_solicitation(
    solicitation_id: UUID,
    payload: ReceiptCreate,
    request: Request,
    response: Response,
    db: DbSession,
    user: User = Depends(require_roles(*WRITE_ROLES)),
) -> ReceiptOut:
    context = RequestContext.from_request(request)
    receipt, audit_seq = await receipt_service.create_receipt(
        db, solicitation_id=solicitation_id, payload=payload, actor=user, context=context
    )
    response.headers["X-Audit-Sequence"] = str(audit_seq)
    return ReceiptOut.model_validate(receipt)


@router.get(
    "/{solicitation_id}/receipt",
    response_model=ReceiptOut,
    summary="Consultar recebimento vinculado à solicitação",
)
async def get_receipt_by_solicitation(
    solicitation_id: UUID,
    db: DbSession,
    _: CurrentUser,
) -> ReceiptOut:
    receipt = await receipt_service.get_receipt_by_solicitation(db, solicitation_id)
    return ReceiptOut.model_validate(receipt)
