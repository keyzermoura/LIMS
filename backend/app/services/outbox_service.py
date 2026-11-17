"""Serviço de Outbox Transacional e Webhooks Assinados HMAC-SHA256 (H3.2).

Conforme ESPECIFICACAO_CAMADA_INTEGRACAO_LIMS.md §4 e ALCOA+.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models.base import utcnow
from app.models.outbox import IntegrationOutbox
from app.models.webhook import WebhookDelivery, WebhookSubscription

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 12
DEFAULT_WEBHOOK_TIMEOUT_SECONDS = 5.0
ANTI_REPLAY_MAX_DRIFT_SECONDS = 300  # 5 minutos


def canonical_json(payload: Any) -> str:
    """Serializa JSON estável com chaves ordenadas para assinatura criptográfica determinística."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def sign_webhook_payload(secret: str, timestamp: int, payload_json: str) -> str:
    """Gera assinatura HMAC-SHA256 com prefixo de versão (v1=<hash>)."""
    message = f"{timestamp}.{payload_json}".encode()
    digest = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
    return f"v1={digest}"


def verify_webhook_signature(
    secret: str,
    timestamp: int,
    payload_json: str,
    signature: str,
    *,
    max_drift_seconds: int = ANTI_REPLAY_MAX_DRIFT_SECONDS,
) -> bool:
    """Verifica autenticidade, integridade e proteção anti-replay contra desvio temporal."""
    now_ts = int(datetime.now(UTC).timestamp())
    if abs(now_ts - timestamp) > max_drift_seconds:
        logger.warning("Rejeição anti-replay de webhook: desvio temporal excessivo (%ss).", abs(now_ts - timestamp))
        return False

    expected_sig = sign_webhook_payload(secret, timestamp, payload_json)
    return hmac.compare_digest(expected_sig, signature)


async def enqueue_event(
    db: AsyncSession,
    *,
    event_type: str,
    aggregate_type: str,
    aggregate_id: str,
    payload: dict[str, Any],
) -> IntegrationOutbox:
    """Enfileira atomicamente um evento de negócio na tabela integration_outbox."""
    event = IntegrationOutbox(
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        payload=payload,
        attempts=0,
        next_attempt_at=utcnow(),
    )
    db.add(event)
    return event


async def dispatch_pending_outbox(
    db: AsyncSession,
    *,
    client: httpx.AsyncClient | None = None,
    batch_size: int = 50,
) -> int:
    """Processa e entrega eventos pendentes no outbox com SKIP LOCKED e backoff exponencial."""
    is_pg = db.bind.dialect.name == "postgresql" if db.bind else False

    stmt = (
        select(IntegrationOutbox)
        .where(
            IntegrationOutbox.published_at.is_(None),
            IntegrationOutbox.dead_lettered_at.is_(None),
            IntegrationOutbox.next_attempt_at <= utcnow(),
        )
        .order_by(IntegrationOutbox.created_at.asc())
        .limit(batch_size)
    )

    if is_pg:
        stmt = stmt.with_for_update(skip_locked=True)

    result = await db.scalars(stmt)
    events = list(result.all())
    if not events:
        return 0

    # Busca endpoints ativos configurados
    sub_res = await db.scalars(
        select(WebhookSubscription).where(WebhookSubscription.is_active.is_(True))
    )
    all_subs = list(sub_res.all())

    own_client = client is None
    http = client or httpx.AsyncClient(timeout=DEFAULT_WEBHOOK_TIMEOUT_SECONDS)

    dispatched_count = 0
    try:
        for event in events:
            # Encontra assinaturas que escutam este tipo de evento ou wildcard "*"
            matching_subs = [
                s for s in all_subs
                if event.event_type in s.events or "*" in s.events
            ]

            if not matching_subs:
                # Nenhum receptor registrado: evento considerado publicado
                event.published_at = utcnow()
                dispatched_count += 1
                continue

            all_succeeded = True
            first_error: str | None = None

            body_str = canonical_json(event.payload)
            now_dt = utcnow()
            ts = int(now_dt.timestamp())

            for sub in matching_subs:
                delivery_id = uuid4()
                signature = sign_webhook_payload(sub.secret, ts, body_str)
                headers = {
                    "Content-Type": "application/json",
                    "X-LIMS-Event": event.event_type,
                    "X-LIMS-Delivery": str(delivery_id),
                    "X-LIMS-Timestamp": str(ts),
                    "X-LIMS-Signature": signature,
                }

                delivery = WebhookDelivery(
                    id=delivery_id,
                    subscription_id=sub.id,
                    event=event.event_type,
                    payload=event.payload,
                    status="PENDING",
                    attempt_count=event.attempts + 1,
                )
                db.add(delivery)

                try:
                    resp = await http.post(
                        sub.url,
                        content=body_str,
                        headers=headers,
                        timeout=DEFAULT_WEBHOOK_TIMEOUT_SECONDS,
                    )
                    delivery.status_code = resp.status_code
                    delivery.response_body = resp.text[:1000]

                    if 200 <= resp.status_code < 300:
                        delivery.status = "DELIVERED"
                        delivery.delivered_at = utcnow()
                    else:
                        delivery.status = "FAILED"
                        all_succeeded = False
                        if not first_error:
                            first_error = f"HTTP {resp.status_code} de {sub.url}"
                except Exception as exc:
                    delivery.status = "FAILED"
                    delivery.response_body = str(exc)[:1000]
                    all_succeeded = False
                    if not first_error:
                        first_error = f"Erro de conexão com {sub.url}: {exc}"

            if all_succeeded:
                event.published_at = utcnow()
                event.last_error = None
                dispatched_count += 1
            else:
                event.attempts += 1
                event.last_error = first_error

                if event.attempts >= MAX_ATTEMPTS:
                    event.dead_lettered_at = utcnow()
                    logger.error(
                        "Evento outbox %s movido para dead-letter após %s tentativas. Erro: %s",
                        event.id,
                        event.attempts,
                        first_error,
                    )
                else:
                    backoff_seconds = min(3600, 2 ** event.attempts * 5)
                    event.next_attempt_at = utcnow() + timedelta(seconds=backoff_seconds)

        await db.commit()
    finally:
        if own_client:
            await http.aclose()

    return dispatched_count


async def retry_dead_letter(
    db: AsyncSession,
    *,
    outbox_id: UUID,
) -> IntegrationOutbox:
    """Reativa um evento enviado para dead-letter após resolução do problema de rede/endpoint."""
    event = await db.get(IntegrationOutbox, outbox_id)
    if not event:
        raise NotFoundError("Evento de outbox não encontrado.")

    event.dead_lettered_at = None
    event.attempts = 0
    event.next_attempt_at = utcnow()
    event.last_error = f"Reativado manualmente para retentativa em {utcnow().isoformat()}."
    await db.commit()
    await db.refresh(event)
    return event
