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
        claims = decode_token(token, expected_type=("access", "service"))
    except TokenError as exc:
        raise SignatureRejectedError(
            f"Sessão inválida: {exc}",
            status_code=status.HTTP_401_UNAUTHORIZED,
            audit=False,
        ) from exc

    if claims.get("typ") == "service":
        from datetime import UTC

        from sqlalchemy import select

        from app.models.base import utcnow
        from app.models.service_client import ServiceClient

        client_id = claims.get("client_id")
        user_id_str = claims.get("uid")
        if not client_id or not user_id_str:
            raise SignatureRejectedError(
                "Token de serviço malformado.", status_code=401, audit=False
            )

        try:
            user_id = UUID(user_id_str)
        except ValueError as exc:
            raise SignatureRejectedError(
                "Token de serviço malformado.", status_code=401, audit=False
            ) from exc

        client = await db.scalar(select(ServiceClient).where(ServiceClient.client_id == client_id))
        if client is None or not client.is_active:
            raise SignatureRejectedError(
                "Cliente de serviço inexistente ou inativo.", status_code=401, audit=False
            )

        client_expires_at = client.expires_at
        if client_expires_at.tzinfo is None:
            client_expires_at = client_expires_at.replace(tzinfo=UTC)
        if client_expires_at <= utcnow():
            raise SignatureRejectedError(
                "Credencial de serviço expirada.", status_code=401, audit=False
            )

        user = await db.get(User, user_id)
        if user is None or not user.is_active or user.role != UserRole.SERVICE:
            raise SignatureRejectedError(
                "Conta de serviço associada inexistente ou inativa.", status_code=401, audit=False
            )

        # Associa metadados do cliente para controle de escopo e idempotência
        user._service_client = client  # type: ignore[attr-defined]
        user._service_scopes = claims.get("scp", [])  # type: ignore[attr-defined]
        return user

    try:
        user_id = UUID(claims["sub"])
    except (KeyError, ValueError) as exc:
        raise SignatureRejectedError("Token malformado.", status_code=401, audit=False) from exc

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


def require_scope(*scopes: str):
    """Valida se uma conta de serviço M2M (UserRole.SERVICE) possui os escopos necessários."""
    async def dependency(user: CurrentUser) -> User:
        if user.role == UserRole.SERVICE:
            client_scopes: list[str] = getattr(user, "_service_scopes", [])
            allowed = set(scopes) | {"*"}
            if not client_scopes or not any(s in allowed for s in client_scopes):
                raise ForbiddenError(
                    f"Acesso negado para conta de serviço. Escopos autorizados: {sorted(scopes)}.",
                    details={
                        "required_scopes": list(scopes),
                        "provided_scopes": client_scopes,
                    },
                )
        return user

    return dependency


async def signature_token_header(
    x_signature_token: Annotated[
        str | None,
        Header(
            alias="X-Signature-Token", description="Token de assinatura eletrônica (uso único)."
        ),
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
