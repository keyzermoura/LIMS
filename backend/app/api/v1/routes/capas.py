"""Rotas de CAPA."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.deps import (
    CurrentUser,
    DbSession,
    SignatureToken,
    require_roles,
    require_signature,
)
from app.core.context import RequestContext
from app.models.electronic_signature import ElectronicSignature
from app.models.enums import CapaStatus, SignatureAction, UserRole
from app.models.user import User
from app.schemas.capa import CapaCreate, CapaCreateResponse, CapaOut, CapaUpdate
from app.schemas.common import Page
from app.services import capa_service, signature_service

router = APIRouter(prefix="/capas", tags=["CAPA"])

WRITE_ROLES = (UserRole.ADMIN, UserRole.FISCAL, UserRole.TECNICO)


@router.get("", response_model=Page[CapaOut], summary="Listar CAPAs")
async def list_capas(
    db: DbSession,
    user: CurrentUser,
    capa_status: CapaStatus | None = Query(None, alias="status"),
    sample_id: UUID | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
) -> Page[CapaOut]:
    items, total = await capa_service.list_capas(
        db, status=capa_status, sample_id=sample_id, page=page, size=size
    )
    return Page[CapaOut].build(
        [CapaOut.model_validate(item) for item in items], total, page, size
    )


@router.post(
    "",
    response_model=CapaCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Abrir CAPA (assinado)",
)
async def create_capa(
    payload: CapaCreate,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    token: SignatureToken,
    _role: User = Depends(require_roles(*WRITE_ROLES)),
) -> CapaCreateResponse:
    signature: ElectronicSignature = await signature_service.consume(
        db,
        token=token,
        user=user,
        entity_type="CapaAction",
        entity_id=str(payload.id),
        action=SignatureAction.CREATE,
        context=RequestContext.from_request(request),
    )
    capa, audit_id = await capa_service.create_capa(
        db,
        payload=payload,
        actor=user,
        signature=signature,
        context=RequestContext.from_request(request),
    )
    return CapaCreateResponse(
        capa=CapaOut.model_validate(capa),
        audit_log_id=audit_id,
        signature_id=signature.id,
    )


@router.get("/{capa_id}", response_model=CapaOut, summary="Detalhar CAPA")
async def get_capa(capa_id: UUID, db: DbSession, user: CurrentUser) -> CapaOut:
    capa = await capa_service.get_capa(db, capa_id)
    return CapaOut.model_validate(capa)


@router.patch(
    "/{capa_id}",
    response_model=CapaOut,
    summary="Atualizar CAPA (assinado)",
)
async def update_capa(
    capa_id: UUID,
    payload: CapaUpdate,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    signature: ElectronicSignature = Depends(
        require_signature(
            entity_type="CapaAction",
            action=SignatureAction.UPDATE,
            id_param="capa_id",
        )
    ),
    _role: User = Depends(require_roles(*WRITE_ROLES)),
) -> CapaOut:
    capa, _audit_id = await capa_service.update_capa(
        db,
        capa_id=capa_id,
        payload=payload,
        actor=user,
        signature=signature,
        context=RequestContext.from_request(request),
    )
    return CapaOut.model_validate(capa)
