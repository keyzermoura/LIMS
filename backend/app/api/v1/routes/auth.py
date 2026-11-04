"""Rotas de autenticação e assinatura eletrônica."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import CurrentUser, DbSession
from app.core import ratelimit
from app.core.config import settings
from app.core.context import RequestContext
from app.models.enums import UserRole
from app.schemas.auth import (
    ChangePasswordRequest,
    ESignatureIssueRequest,
    ESignatureIssueResponse,
    LogoutRequest,
    MeOut,
    RefreshRequest,
    TokenPair,
    UserOut,
)
from app.services import auth_service, signature_service

router = APIRouter(prefix="/auth", tags=["Autenticação e Assinatura"])


def _to_me(user) -> MeOut:
    me = MeOut.model_validate(user)
    me.permissions = auth_service.permissions_for(user.role)
    return me


@router.post(
    "/login",
    response_model=TokenPair,
    summary="Autenticar (OAuth2 password grant)",
    responses={
        401: {"description": "Credenciais inválidas"},
        403: {"description": "Conta bloqueada"},
        429: {"description": "Muitas tentativas (cabeçalho Retry-After)"},
    },
)
async def login(
    request: Request,
    db: DbSession,
    form: OAuth2PasswordRequestForm = Depends(),
) -> TokenPair:
    context = RequestContext.from_request(request)
    ratelimit.enforce(
        f"login:{context.ip_address or 'unknown'}",
        limit=settings.LOGIN_RATE_LIMIT,
        window_seconds=settings.LOGIN_RATE_WINDOW_SECONDS,
    )
    user, access, refresh = await auth_service.login(
        db,
        username=form.username,
        password=form.password,
        context=context,
    )
    return TokenPair(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=_to_me(user),
    )


@router.post("/refresh", response_model=TokenPair, summary="Rotacionar sessão")
async def refresh_session(
    payload: RefreshRequest, request: Request, db: DbSession
) -> TokenPair:
    user, access, refresh = await auth_service.refresh(
        db,
        refresh_token=payload.refresh_token,
        context=RequestContext.from_request(request),
    )
    return TokenPair(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=_to_me(user),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Encerrar sessão")
async def logout(
    payload: LogoutRequest, request: Request, db: DbSession, user: CurrentUser
) -> None:
    await auth_service.logout(
        db,
        refresh_token=payload.refresh_token,
        user=user,
        context=RequestContext.from_request(request),
    )


@router.get("/me", response_model=MeOut, summary="Perfil e permissões do usuário logado")
async def me(user: CurrentUser) -> MeOut:
    return _to_me(user)


@router.post(
    "/sign",
    response_model=ESignatureIssueResponse,
    summary="Reautenticar e obter token de assinatura eletrônica",
    description=(
        "Etapa 1 da assinatura eletrônica (21 CFR Part 11 §11.200). "
        "A senha é verificada novamente e o token emitido é de USO ÚNICO, "
        "válido por poucos minutos e vinculado ao registro/ação informados."
    ),
    responses={
        401: {"description": "Senha inválida"},
        403: {"description": "Conta bloqueada"},
        429: {"description": "Muitas tentativas (cabeçalho Retry-After)"},
    },
)
async def issue_signature(
    payload: ESignatureIssueRequest,
    request: Request,
    db: DbSession,
    user: CurrentUser,
) -> ESignatureIssueResponse:
    ratelimit.enforce(
        f"sign:{user.id}",
        limit=settings.SIGN_RATE_LIMIT,
        window_seconds=settings.SIGN_RATE_WINDOW_SECONDS,
    )
    record, token = await signature_service.issue(
        db,
        user=user,
        password=payload.password,
        meaning=payload.meaning,
        reason=payload.reason,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        action=payload.action,
        context=RequestContext.from_request(request),
    )
    return ESignatureIssueResponse(
        token=token,
        signature_id=record.id,
        expires_at=record.expires_at,
        manifest=record.manifest,
        manifest_hash=record.manifest_hash,
    )


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Trocar senha (invalida todas as sessões)",
)
async def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    db: DbSession,
    user: CurrentUser,
) -> None:
    await auth_service.change_password(
        db,
        user=user,
        current_password=payload.current_password,
        new_password=payload.new_password,
        context=RequestContext.from_request(request),
    )


@router.get("/roles", response_model=list[str], summary="Perfis disponíveis")
async def roles() -> list[str]:
    return [role.value for role in UserRole]


@router.get("/users/{user_id}", response_model=UserOut, summary="Consultar usuário")
async def user_detail(user_id: UUID, db: DbSession, user: CurrentUser) -> UserOut:
    target = await auth_service.get_user(db, user_id)
    return UserOut.model_validate(target)


__all__ = ["router"]
