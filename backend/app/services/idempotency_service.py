"""Serviço de Idempotência para APIs de Integração.

Conforme ESPECIFICACAO_CAMADA_INTEGRACAO_LIMS.md §3 e RFC 7231 §4.2.2.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError
from app.models.base import utcnow
from app.models.idempotency import IdempotencyKey

DEFAULT_IDEMPOTENCY_TTL_SECONDS = 86400  # 24 horas
INSTRUMENT_IDEMPOTENCY_TTL_SECONDS = 7 * 86400  # 7 dias


def compute_payload_hash(payload: Any) -> str:
    """Calcula hash SHA-256 estável do payload para conferência de integridade."""
    if isinstance(payload, bytes):
        raw = payload
    elif isinstance(payload, str):
        raw = payload.encode("utf-8")
    else:
        # JSON canônico com chaves ordenadas
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


async def check_idempotency(
    db: AsyncSession,
    *,
    client_id: str,
    key: str,
    request_hash: str,
) -> tuple[bool, int | None, Any | None]:
    """Verifica se a chave já foi processada.

    Retorna:
        (True, status_code, response_body) se for replay válido.
        (False, None, None) se a chave for inédita ou expirada.

    Lança:
        ConflictError se a chave foi reusada com corpo de requisição diferente.
    """
    record = await db.get(IdempotencyKey, (client_id, key))
    if not record:
        return False, None, None

    # Verifica expiração
    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= utcnow():
        # Expirado: pode ser sobregravado ou reprocessado
        return False, None, None

    # Detecção de reuso inválido da chave com payload divergente (RFC 7231)
    if record.request_hash != request_hash:
        raise ConflictError(
            "Chave de idempotência reutilizada com payload divergente. "
            "Reenvios idempotentes devem conter o mesmo corpo de requisição."
        )

    return True, record.response_status, record.response_body


async def record_idempotency(
    db: AsyncSession,
    *,
    client_id: str,
    key: str,
    request_hash: str,
    response_status: int,
    response_body: Any,
    ttl_seconds: int = DEFAULT_IDEMPOTENCY_TTL_SECONDS,
    created_by_user_id: UUID | None = None,
) -> IdempotencyKey:
    """Persiste a resposta para replays subsequentes seguros."""
    expires_at = utcnow() + timedelta(seconds=ttl_seconds)

    # Se já existir um expirado, atualiza
    existing = await db.get(IdempotencyKey, (client_id, key))
    if existing:
        existing.request_hash = request_hash
        existing.response_status = response_status
        existing.response_body = response_body
        existing.expires_at = expires_at
        existing.created_at = utcnow()
        existing.created_by_user_id = created_by_user_id
        record = existing
    else:
        record = IdempotencyKey(
            client_id=client_id,
            key=key,
            request_hash=request_hash,
            response_status=response_status,
            response_body=response_body,
            expires_at=expires_at,
            created_by_user_id=created_by_user_id,
        )
        db.add(record)

    await db.commit()
    return record
