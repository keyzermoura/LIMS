"""Rotas de usuários (seleção de custodiantes e administração)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.deps import CurrentUser, DbSession, SignatureToken, require_roles
from app.core.context import RequestContext
from app.models.enums import SignatureAction, UserRole
from app.models.user import User
from app.schemas.auth import UserCreatedResponse, UserCreateRequest
from app.schemas.common import UserBrief
from app.services import auth_service, signature_service

router = APIRouter(prefix="/users", tags=["Usuários"])


@router.get(
    "",
    response_model=list[UserBrief],
    summary="Listar usuários ativos (para seleção de custodiante/testador)",
)
async def list_users(
    db: DbSession,
    user: CurrentUser,
    role: UserRole | None = Query(None),
) -> list[UserBrief]:
    users = await auth_service.list_users(db, role=role)
    return [UserBrief.model_validate(item) for item in users]


@router.post(
    "",
    response_model=UserCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar usuário (somente ADMIN, assinado)",
)
async def create_user(
    payload: UserCreateRequest,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    token: SignatureToken,
    _role: User = Depends(require_roles(UserRole.ADMIN)),
) -> UserCreatedResponse:
    context = RequestContext.from_request(request)
    signature = await signature_service.consume(
        db,
        token=token,
        user=user,
        entity_type="User",
        entity_id=str(payload.id),
        action=SignatureAction.CREATE,
        context=context,
    )
    created = await auth_service.create_user(
        db,
        actor=user,
        user_id=payload.id,
        username=payload.username,
        email=payload.email,
        full_name=payload.full_name,
        role=payload.role,
        password=payload.password,
        registration_number=payload.registration_number,
        signature=signature,
        context=context,
    )
    return UserCreatedResponse.model_validate(created)
