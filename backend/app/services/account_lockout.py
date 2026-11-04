"""Política de bloqueio por tentativas de senha.

Compartilhada pelo login e pela reautenticação da assinatura eletrônica: uma
senha errada no `/auth/sign` também incrementa o contador da conta. Sem isso,
um portador de access token válido poderia testar senhas indefinidamente sem
sofrer o bloqueio aplicado ao login.
"""

from __future__ import annotations

from datetime import timedelta

from app.core.config import settings
from app.core.errors import ForbiddenError
from app.models.base import utcnow
from app.models.user import User

INVALID_PASSWORD_REASON = "Senha inválida."
LOCKOUT_REASON = "Limite de tentativas atingido — conta bloqueada."


def locked_message() -> str:
    return (
        "Conta bloqueada temporariamente após tentativas inválidas. "
        f"Tente novamente em até {settings.LOGIN_LOCKOUT_MINUTES} minutos."
    )


def locked_error() -> ForbiddenError:
    return ForbiddenError(locked_message())


def register_failure(user: User) -> tuple[str, bool]:
    """Incrementa o contador e aplica o bloqueio quando o limite é atingido.

    Retorna o motivo para a auditoria e se a conta acabou de ser bloqueada.
    A persistência fica a cargo do chamador, na mesma transação do evento de
    auditoria (ver `auth_service._audit_failed_login`).
    """
    user.failed_login_attempts += 1
    if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
        user.locked_until = utcnow() + timedelta(minutes=settings.LOGIN_LOCKOUT_MINUTES)
        user.failed_login_attempts = 0
        return LOCKOUT_REASON, True
    return INVALID_PASSWORD_REASON, False


def reset_failures(user: User) -> None:
    """Limpa contador e bloqueio após uma autenticação bem-sucedida."""
    user.failed_login_attempts = 0
    user.locked_until = None
