"""Rotas de transferência de custódia."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request

from app.api.deps import CurrentUser, DbSession, SignatureToken, require_roles
from app.core.context import RequestContext
from app.models.electronic_signature import ElectronicSignature
from app.models.enums import SignatureAction, UserRole
from app.models.user import User
from app.schemas.sample import (
    CustodyOut,
    CustodyTransferRequest,
    SampleOut,
    TransferResponse,
)
from app.services import custody_service, signature_service

router = APIRouter(prefix="/custody", tags=["Amostras e Cadeia de Custódia"])

TRANSFER_ROLES = (
    UserRole.ADMIN,
    UserRole.FISCAL,
    UserRole.TECNICO,
    UserRole.CUSTODIANTE,
)


@router.post(
    "/transfer",
    response_model=TransferResponse,
    summary="Transferir guarda do dispositivo (assinado)",
    description=(
        "Cada transferência é um evento append-only, assinado por quem entrega "
        "a guarda. A assinatura é vinculada ao evento e ao estado resultante."
    ),
)
async def transfer_custody(
    payload: CustodyTransferRequest,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    token: SignatureToken,
    _role: User = Depends(require_roles(*TRANSFER_ROLES)),
) -> TransferResponse:
    signature: ElectronicSignature = await signature_service.consume(
        db,
        token=token,
        user=user,
        entity_type="DeviceSample",
        entity_id=str(payload.device_sample_id),
        action=SignatureAction.TRANSFER,
        context=RequestContext.from_request(request),
    )
    event, sample, audit_id = await custody_service.transfer(
        db,
        payload=payload,
        actor=user,
        signature=signature,
        context=RequestContext.from_request(request),
    )
    return TransferResponse(
        custody=CustodyOut.model_validate(event),
        sample=SampleOut.model_validate(sample),
        audit_log_id=audit_id,
        signature_id=signature.id,
    )


@router.get(
    "/{sample_id}/history",
    response_model=list[CustodyOut],
    summary="Histórico completo de custódia",
)
async def custody_history(
    sample_id: UUID, db: DbSession, user: CurrentUser
) -> list[CustodyOut]:
    events = await custody_service.history(db, sample_id)
    return [CustodyOut.model_validate(event) for event in events]
