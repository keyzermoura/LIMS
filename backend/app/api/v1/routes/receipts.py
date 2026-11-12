"""Rotas de Recebimento, Conferência Física e Objetos de Custódia (Fase 1 / M1.1)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, status

from app.api.deps import CurrentUser, DbSession, require_roles
from app.core.context import RequestContext
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.receipt import (
    CustodyAcceptanceCreate,
    CustodyEventOut,
    CustodyObjectOut,
    CustodyTransferCreate,
    ReceiptItemConference,
    ReceiptItemOut,
    ReceiptOut,
)
from app.schemas.sample import SampleOut
from app.services import receipt_service

receipts_router = APIRouter(prefix="/receipts", tags=["Recebimento"])
custody_objects_router = APIRouter(prefix="/custody/objects", tags=["Objetos de Custódia"])

WRITE_ROLES = (UserRole.ADMIN, UserRole.FISCAL, UserRole.TECNICO, UserRole.CUSTODIANTE)


@receipts_router.get(
    "/{receipt_id}",
    response_model=ReceiptOut,
    summary="Consultar recebimento por identificador",
)
async def get_receipt(
    receipt_id: UUID,
    db: DbSession,
    _: CurrentUser,
) -> ReceiptOut:
    receipt = await receipt_service.get_receipt(db, receipt_id)
    return ReceiptOut.model_validate(receipt)


@receipts_router.post(
    "/{receipt_id}/items/{item_id}/conference",
    response_model=ReceiptItemOut,
    summary="Registrar conferência física de item do recebimento",
)
async def conference_item(
    receipt_id: UUID,
    item_id: UUID,
    payload: ReceiptItemConference,
    request: Request,
    response: Response,
    db: DbSession,
    user: User = Depends(require_roles(*WRITE_ROLES)),
) -> ReceiptItemOut:
    context = RequestContext.from_request(request)
    item, audit_seq = await receipt_service.conference_item(
        db,
        receipt_id=receipt_id,
        item_id=item_id,
        payload=payload,
        actor=user,
        context=context,
    )
    response.headers["X-Audit-Sequence"] = str(audit_seq)
    return ReceiptItemOut.model_validate(item)


@custody_objects_router.get(
    "/{custody_object_id}",
    response_model=CustodyObjectOut,
    summary="Consultar objeto de custódia",
)
async def get_custody_object(
    custody_object_id: UUID,
    db: DbSession,
    _: CurrentUser,
) -> CustodyObjectOut:
    obj = await receipt_service.get_custody_object(db, custody_object_id)
    return CustodyObjectOut.model_validate(obj)


@custody_objects_router.get(
    "/{custody_object_id}/history",
    response_model=list[CustodyEventOut],
    summary="Consultar histórico append-only de eventos de custódia do objeto",
)
async def get_custody_history(
    custody_object_id: UUID,
    db: DbSession,
    _: CurrentUser,
) -> list[CustodyEventOut]:
    events = await receipt_service.get_custody_history(db, custody_object_id)
    return [CustodyEventOut.model_validate(e) for e in events]


@custody_objects_router.post(
    "/{custody_object_id}/transfers",
    response_model=CustodyObjectOut,
    summary="Registrar transferência de custódia física do objeto",
)
async def transfer_custody(
    custody_object_id: UUID,
    payload: CustodyTransferCreate,
    request: Request,
    response: Response,
    db: DbSession,
    user: User = Depends(require_roles(*WRITE_ROLES)),
) -> CustodyObjectOut:
    context = RequestContext.from_request(request)
    obj, audit_seq = await receipt_service.transfer_custody(
        db,
        custody_object_id=custody_object_id,
        payload=payload,
        actor=user,
        context=context,
    )
    response.headers["X-Audit-Sequence"] = str(audit_seq)
    return CustodyObjectOut.model_validate(obj)


@custody_objects_router.post(
    "/{custody_object_id}/acceptance",
    response_model=SampleOut | None,
    status_code=status.HTTP_200_OK,
    summary="Formalizar aceite técnico do objeto e gerar amostra operacional",
)
async def accept_custody_object(
    custody_object_id: UUID,
    payload: CustodyAcceptanceCreate,
    request: Request,
    response: Response,
    db: DbSession,
    user: User = Depends(require_roles(*WRITE_ROLES)),
) -> SampleOut | None:
    context = RequestContext.from_request(request)
    sample, audit_seq = await receipt_service.accept_custody_object(
        db,
        custody_object_id=custody_object_id,
        payload=payload,
        actor=user,
        context=context,
    )
    response.headers["X-Audit-Sequence"] = str(audit_seq)
    if sample is not None:
        return SampleOut.model_validate(sample)
    return None
