"""Erros específicos da camada de serviços."""

from __future__ import annotations

from fastapi import status

from app.core.errors import DomainError


class SignatureRejectedError(DomainError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "ESIGNATURE_REJECTED"

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        audit: bool = True,
    ) -> None:
        super().__init__(message)
        if status_code is not None:
            self.status_code = status_code
        self.audit = audit
        self.headers = {"WWW-Authenticate": "Signature"}


class ImmutableRecordError(DomainError):
    status_code = status.HTTP_409_CONFLICT
    code = "IMMUTABLE_RECORD"
