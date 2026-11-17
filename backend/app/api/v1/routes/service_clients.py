"""Rotas administrativas de Gestão de Contas de Serviço (M2M).

Conforme ESPECIFICACAO_CAMADA_INTEGRACAO_LIMS.md e ALCOA+.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status

from app.api.deps import DbSession, require_roles
from app.core.context import RequestContext
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.service_client import (
    ServiceClientCreate,
    ServiceClientCreated,
    ServiceClientOut,
    ServiceSecretRotateResponse,
)
from app.services import service_client_service

router = APIRouter(prefix="/service-clients", tags=["Contas de Serviço (M2M)"])


@router.post(
    "",
    response_model=ServiceClientCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar nova conta de serviço M2M (Admin)",
)
async def create_client(
    payload: ServiceClientCreate,
    request: Request,
    db: DbSession,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> ServiceClientCreated:
    """Gera identificador e credenciais iniciais. O segredo é retornado uma única vez."""
    context = RequestContext.from_request(request)
    client, raw_secret = await service_client_service.create_service_client(
        db,
        payload=payload,
        created_by=current_user,
        context=context,
    )
    return ServiceClientCreated(
        id=client.id,
        client_id=client.client_id,
        client_secret=raw_secret,
        name=client.name,
        scopes=client.scopes,
        expires_at=client.expires_at,
        service_user_id=client.service_user_id,
    )


@router.get(
    "",
    response_model=list[ServiceClientOut],
    summary="Listar contas de serviço cadastradas (Admin)",
)
async def list_clients(
    db: DbSession,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> list[ServiceClientOut]:
    clients = await service_client_service.list_service_clients(db, actor=current_user)
    return [ServiceClientOut.model_validate(c) for c in clients]


@router.post(
    "/{client_id}/rotate",
    response_model=ServiceSecretRotateResponse,
    summary="Rotacionar segredo da conta de serviço (Admin)",
)
async def rotate_secret(
    client_id: str,
    request: Request,
    db: DbSession,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> ServiceSecretRotateResponse:
    """Gera novo segredo com janela de sobreposição para não interromper a operação."""
    context = RequestContext.from_request(request)
    client, new_secret = await service_client_service.rotate_service_client_secret(
        db,
        client_id=client_id,
        actor=current_user,
        context=context,
    )
    return ServiceSecretRotateResponse(
        client_id=client.client_id,
        new_client_secret=new_secret,
        expires_at=client.expires_at,
    )


@router.delete(
    "/{client_id}",
    response_model=ServiceClientOut,
    summary="Revogar conta de serviço (Admin)",
)
async def revoke_client(
    client_id: str,
    request: Request,
    db: DbSession,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> ServiceClientOut:
    """Revoga imediatamente o acesso da conta de serviço."""
    context = RequestContext.from_request(request)
    client = await service_client_service.deactivate_service_client(
        db,
        client_id=client_id,
        actor=current_user,
        context=context,
    )
    return ServiceClientOut.model_validate(client)


__all__ = ["router"]
