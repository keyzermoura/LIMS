"""Contexto de requisição propagado para a auditoria."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request
from starlette.requests import HTTPConnection


@dataclass(slots=True, frozen=True)
class RequestContext:
    ip_address: str | None
    user_agent: str | None
    request_id: str

    @classmethod
    def from_request(cls, request: Request) -> RequestContext:
        # `X-Forwarded-For` só é confiável atrás de um proxy controlado.
        # Aqui priorizamos o IP da conexão e usamos o header como fallback.
        forwarded = request.headers.get("x-forwarded-for")
        ip = request.client.host if request.client else None
        if not ip and forwarded:
            ip = forwarded.split(",")[0].strip()
        return cls(
            ip_address=ip,
            user_agent=(request.headers.get("user-agent") or "")[:512] or None,
            request_id=getattr(request.state, "request_id", "unknown"),
        )


def get_request_context(request: Request) -> RequestContext:
    return RequestContext.from_request(request)


def client_ip(conn: HTTPConnection) -> str | None:
    return conn.client.host if conn.client else None
