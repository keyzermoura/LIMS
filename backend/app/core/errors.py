"""Erros de domínio e handlers padronizados.

Respostas de erro não vazam detalhes internos e sempre carregam um
`request_id` para correlação com a trilha de auditoria.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)


class DomainError(Exception):
    """Erro de regra de negócio com status HTTP associado."""

    status_code = status.HTTP_400_BAD_REQUEST
    code = "DOMAIN_ERROR"

    def __init__(self, message: str, *, details: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class ValidationDomainError(DomainError):
    status_code = 422
    code = "VALIDATION_ERROR"


class NotFoundError(DomainError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "NOT_FOUND"


class ConflictError(DomainError):
    status_code = status.HTTP_409_CONFLICT
    code = "CONFLICT"


class ForbiddenError(DomainError):
    status_code = status.HTTP_403_FORBIDDEN
    code = "FORBIDDEN"


class SignatureError(DomainError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "ESIGNATURE_REQUIRED"


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _domain_error(request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.message,
                "code": exc.code,
                "request_id": _request_id(request),
                "context": exc.details,
            },
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Dados inválidos.",
                "code": "REQUEST_VALIDATION_ERROR",
                "request_id": _request_id(request),
                "errors": exc.errors(),
            },
        )

    @app.exception_handler(IntegrityError)
    async def _integrity_error(request: Request, exc: IntegrityError) -> JSONResponse:
        logger.warning("IntegrityError request_id=%s: %s", _request_id(request), exc)
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": "Operação conflita com um registro existente.",
                "code": "INTEGRITY_ERROR",
                "request_id": _request_id(request),
            },
        )

    @app.exception_handler(HTTPException)
    async def _http_error(request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "code": "HTTP_ERROR",
                "request_id": _request_id(request),
            },
            headers=exc.headers,
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Erro não tratado request_id=%s", _request_id(request))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Erro interno. Informe o request_id ao administrador.",
                "code": "INTERNAL_ERROR",
                "request_id": _request_id(request),
            },
        )
