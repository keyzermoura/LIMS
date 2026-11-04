"""Dependências de autenticação, autorização e assinatura eletrônica."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.context import RequestContext
from app.core.errors import ForbiddenError
from app.core.security import TokenError, decode_token
from app.db.database import get_db_session
from app.models.electronic_signature import ElectronicSignature
from app.models.enums import SignatureAction, UserRole
from app.models.user import User
from app.services import signature_service
from app.services.errors import SignatureRejectedError

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
    auto_error=False,
    description="JWT de acesso obtido em /auth/login.",
)

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


async def get_current_user(
    db: DbSession,
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> User:
    if not token:
        raise SignatureRejectedError(
            "Autenticação necessária.",
            status_code=status.HTTP_401_UNAUTHORIZED,
            audit=False,
        )
    try:
        claims = decode_token(token, expected_type="access")
    except TokenError as exc:
        raise SignatureRejectedError(
            f"Sessão inválida: {exc}",
            status_code=status.HTTP_401_UNAUTHORIZED,
            audit=False,
        ) from exc

    try:
        user_id = UUID(claims["sub"])
    except (KeyError, ValueError) as exc:
        raise SignatureRejectedError(
            "Token malformado.", status_code=401, audit=False
        ) from exc

    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise SignatureRejectedError(
            "Usuário inexistente ou inativo.", status_code=401, audit=False
        )
    if user.is_locked:
        raise ForbiddenError("Conta bloqueada temporariamente.")
    if claims.get("pwdv") != user.password_version:
        raise SignatureRejectedError(
            "Sessão expirada (senha alterada). Autentique-se novamente.",
            status_code=401,
            audit=False,
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: UserRole):
    async def dependency(user: CurrentUser) -> User:
        if user.role not in roles:
            allowed = ", ".join(role.value for role in roles)
            raise ForbiddenError(
                f"Acesso negado. Perfis autorizados: {allowed}.",
                details={"required_roles": [role.value for role in roles]},
            )
        return user

    return dependency


async def signature_token_header(
    x_signature_token: Annotated[
        str | None, Header(alias="X-Signature-Token", description="Token de assinatura eletrônica (uso único).")
    ] = None,
) -> str:
    if not x_signature_token:
        raise SignatureRejectedError(
            "Assinatura eletrônica obrigatória: reautentique-se em /auth/sign "
            "e envie o token no header X-Signature-Token.",
            status_code=status.HTTP_401_UNAUTHORIZED,
            audit=False,
        )
    return x_signature_token


SignatureToken = Annotated[str, Depends(signature_token_header)]


def require_signature(*, entity_type: str, action: SignatureAction, id_param: str):
    """Exige assinatura vinculada ao `id_param` extraído da rota.

    Usado em PATCH/transferências, onde o identificador já existe na URL.
    """

    async def dependency(
        request: Request,
        db: DbSession,
        user: CurrentUser,
        token: SignatureToken,
    ) -> ElectronicSignature:
        raw_id = request.path_params.get(id_param) or request.query_params.get(id_param)
        if raw_id is None:
            raise SignatureRejectedError(
                "Identificador do registro ausente para validar a assinatura.",
                status_code=422,
                audit=False,
            )
        return await signature_service.consume(
            db,
            token=token,
            user=user,
            entity_type=entity_type,
            entity_id=str(raw_id),
            action=action,
            context=RequestContext.from_request(request),
        )

    return dependency
