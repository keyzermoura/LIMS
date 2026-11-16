"""Serviço de Mensageria e Webhooks Assinados HMAC SHA-256 (Fase 5 / Sprint 5.4).

Conforme ESPECIFICACAO_CAMADA_INTEGRACAO_LIMS.md §4.3:
- Assinatura criptográfica obrigatória: X-LIMS-Signature: v1=<hmac_sha256(secret, timestamp + "." + body)>
- Cabeçalhos de rastreabilidade: X-LIMS-Event, X-LIMS-Delivery, X-LIMS-Timestamp
- Proteção anti-replay e entrega at-least-once com Outbox Delivery.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationDomainError
from app.core.serialization import canonical_json, jsonable
from app.models.base import utcnow
from app.models.webhook import WebhookDelivery, WebhookSubscription


def compute_signature(secret: str, timestamp: int, body: str) -> str:
    """Calcula a assinatura HMAC SHA-256 no formato 'v1=<hex>'."""
    signed_payload = f"{timestamp}.{body}".encode()
    mac = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    return f"v1={mac}"


async def create_subscription(
    db: AsyncSession,
    *,
    url: str,
    description: str | None = None,
    events: list[str] | None = None,
    secret: str | None = None,
    created_by_id: UUID,
) -> WebhookSubscription:
    """Registra uma nova subscrição de webhook para integração externa."""
    if not url.startswith("http://") and not url.startswith("https://"):
        raise ValidationDomainError("A URL do webhook deve começar com http:// ou https://")

    chosen_secret = secret or secrets.token_hex(32)
    chosen_events = events or ["*"]
    user_uuid = UUID(str(created_by_id)) if not isinstance(created_by_id, UUID) else created_by_id

    sub = WebhookSubscription(
        url=url,
        secret=chosen_secret,
        description=description,
        events=chosen_events,
        is_active=True,
        created_by_id=user_uuid,
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub


async def list_subscriptions(
    db: AsyncSession,
) -> list[WebhookSubscription]:
    """Lista todos os endpoints de webhook cadastrados."""
    stmt = select(WebhookSubscription).order_by(WebhookSubscription.created_at.desc())
    return list((await db.scalars(stmt)).all())


async def get_subscription(
    db: AsyncSession,
    subscription_id: UUID,
) -> WebhookSubscription:
    """Busca subscrição por UUID."""
    sub = await db.get(WebhookSubscription, subscription_id)
    if sub is None:
        raise NotFoundError("Subscrição de webhook não encontrada.")
    return sub


async def delete_subscription(
    db: AsyncSession,
    subscription_id: UUID,
) -> None:
    """Remove uma subscrição de webhook."""
    sub = await get_subscription(db, subscription_id)
    await db.delete(sub)
    await db.commit()


async def deliver_single_webhook(
    delivery: WebhookDelivery,
    subscription: WebhookSubscription,
    client: httpx.AsyncClient,
) -> None:
    """Dispara a requisição HTTP com os headers e assinatura HMAC SHA-256."""
    now_ts = int(time.time())
    payload_str = canonical_json(jsonable(delivery.payload))
    signature = compute_signature(subscription.secret, now_ts, payload_str)

    headers = {
        "Content-Type": "application/json",
        "X-LIMS-Event": delivery.event,
        "X-LIMS-Delivery": str(delivery.id),
        "X-LIMS-Timestamp": str(now_ts),
        "X-LIMS-Signature": signature,
    }

    delivery.attempt_count += 1
    try:
        resp = await client.post(
            subscription.url,
            content=payload_str,
            headers=headers,
            timeout=5.0,
        )
        delivery.status_code = resp.status_code
        delivery.response_body = resp.text[:1000]
        if 200 <= resp.status_code < 300:
            delivery.status = "DELIVERED"
            delivery.delivered_at = utcnow()
        else:
            delivery.status = "FAILED"
    except Exception as exc:
        delivery.status = "FAILED"
        delivery.response_body = f"Erro de conexão: {exc}"[:1000]


async def dispatch_event(
    db: AsyncSession,
    *,
    event: str,
    payload: dict[str, Any],
    client: httpx.AsyncClient | None = None,
) -> list[WebhookDelivery]:
    """Publica um evento para todos os webhooks inscritos de forma transacional."""
    stmt = select(WebhookSubscription).where(WebhookSubscription.is_active == True)  # noqa: E712
    subscriptions = (await db.scalars(stmt)).all()

    deliveries: list[WebhookDelivery] = []
    should_close_client = False
    http_client = client
    if http_client is None:
        http_client = httpx.AsyncClient()
        should_close_client = True

    try:
        for sub in subscriptions:
            # Checa se o webhook aceita este evento
            if "*" in sub.events or event in sub.events:
                delivery = WebhookDelivery(
                    subscription_id=sub.id,
                    event=event,
                    payload=payload,
                    status="PENDING",
                    attempt_count=0,
                )
                db.add(delivery)
                await db.flush()

                await deliver_single_webhook(delivery, sub, http_client)
                deliveries.append(delivery)

        await db.commit()
    finally:
        if should_close_client:
            await http_client.aclose()

    return deliveries


async def ping_subscription(
    db: AsyncSession,
    subscription_id: UUID,
    client: httpx.AsyncClient | None = None,
) -> WebhookDelivery:
    """Dispara um evento de teste 'ping' para validação imediata da conexão e assinatura."""
    sub = await get_subscription(db, subscription_id)

    delivery = WebhookDelivery(
        subscription_id=sub.id,
        event="ping",
        payload={
            "message": "Teste de conexão e assinatura HMAC SHA-256 do LIMS",
            "subscription_id": str(sub.id),
            "timestamp": int(time.time()),
        },
        status="PENDING",
        attempt_count=0,
    )
    db.add(delivery)
    await db.flush()

    should_close_client = False
    http_client = client
    if http_client is None:
        http_client = httpx.AsyncClient()
        should_close_client = True

    try:
        await deliver_single_webhook(delivery, sub, http_client)
        await db.commit()
        await db.refresh(delivery)
    finally:
        if should_close_client:
            await http_client.aclose()

    return delivery


async def list_deliveries(
    db: AsyncSession,
    *,
    subscription_id: UUID | None = None,
    limit: int = 50,
) -> list[WebhookDelivery]:
    """Lista as entregas mais recentes de webhooks."""
    stmt = select(WebhookDelivery)
    if subscription_id:
        stmt = stmt.where(WebhookDelivery.subscription_id == subscription_id)
    stmt = stmt.order_by(WebhookDelivery.created_at.desc()).limit(limit)
    return list((await db.scalars(stmt)).all())
