"""Rotas da API para Gestão e Monitoramento de Webhooks (Fase 5 / Sprint 5.4).

Conforme ESPECIFICACAO_CAMADA_INTEGRACAO_LIMS.md e ALCOA+.
"""

from __future__ import annotations

import time
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import CurrentUser, DbSession, require_roles
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.webhook import (
    WebhookDeliveryOut,
    WebhookPingResponse,
    WebhookSubscriptionCreateIn,
    WebhookSubscriptionOut,
)
from app.services import webhook_service

webhooks_router = APIRouter(prefix="/webhooks", tags=["Webhooks & Mensageria de Integração"])

MANAGE_ROLES = (UserRole.ADMIN, UserRole.FISCAL)


@webhooks_router.post(
    "/subscriptions",
    response_model=WebhookSubscriptionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar nova subscrição de webhook de saída",
)
async def create_webhook_subscription(
    payload: WebhookSubscriptionCreateIn,
    db: DbSession,
    current_user: User = Depends(require_roles(*MANAGE_ROLES)),
) -> WebhookSubscriptionOut:
    """Registra uma URL externa para recepção de eventos assinados via HMAC SHA-256."""
    sub = await webhook_service.create_subscription(
        db,
        url=payload.url,
        description=payload.description,
        events=payload.events,
        secret=payload.secret,
        created_by_id=current_user.id,
    )
    return WebhookSubscriptionOut.model_validate(sub)


@webhooks_router.get(
    "/subscriptions",
    response_model=list[WebhookSubscriptionOut],
    summary="Listar subscrições ativas de webhooks",
)
async def list_webhook_subscriptions(
    db: DbSession,
    _: CurrentUser,
) -> list[WebhookSubscriptionOut]:
    """Lista todos os endpoints de webhook cadastrados."""
    subs = await webhook_service.list_subscriptions(db)
    return [WebhookSubscriptionOut.model_validate(s) for s in subs]


@webhooks_router.get(
    "/subscriptions/{subscription_id}",
    response_model=WebhookSubscriptionOut,
    summary="Obter detalhes de uma subscrição de webhook",
)
async def get_webhook_subscription(
    subscription_id: UUID,
    db: DbSession,
    _: CurrentUser,
) -> WebhookSubscriptionOut:
    """Busca subscrição por identificador único."""
    sub = await webhook_service.get_subscription(db, subscription_id)
    return WebhookSubscriptionOut.model_validate(sub)


@webhooks_router.delete(
    "/subscriptions/{subscription_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover subscrição de webhook",
)
async def delete_webhook_subscription(
    subscription_id: UUID,
    db: DbSession,
    _: User = Depends(require_roles(*MANAGE_ROLES)),
) -> None:
    """Exclui a subscrição e cessa o envio de eventos para a URL associada."""
    await webhook_service.delete_subscription(db, subscription_id)


@webhooks_router.post(
    "/subscriptions/{subscription_id}/ping",
    response_model=WebhookPingResponse,
    summary="Enviar ping de teste com assinatura HMAC SHA-256",
)
async def ping_webhook_subscription(
    subscription_id: UUID,
    db: DbSession,
    _: User = Depends(require_roles(*MANAGE_ROLES)),
) -> WebhookPingResponse:
    """Dispara um evento imediato de teste ('ping') para validar conectividade e assinatura."""
    sub = await webhook_service.get_subscription(db, subscription_id)
    delivery = await webhook_service.ping_subscription(db, subscription_id)

    dummy_ts = int(time.time())
    sig = webhook_service.compute_signature(sub.secret, dummy_ts, "{}")

    return WebhookPingResponse(
        subscription_id=sub.id,
        delivery_id=delivery.id,
        event=delivery.event,
        status=delivery.status,
        status_code=delivery.status_code,
        signature_header=sig,
    )


@webhooks_router.get(
    "/deliveries",
    response_model=list[WebhookDeliveryOut],
    summary="Listar histórico de entregas de webhooks (Outbox log)",
)
async def list_webhook_deliveries(
    db: DbSession,
    _: CurrentUser,
    subscription_id: Annotated[UUID | None, Query(description="Filtrar por subscrição")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[WebhookDeliveryOut]:
    """Consulta o log transacional de tentativas de entrega de webhooks."""
    deliveries = await webhook_service.list_deliveries(
        db, subscription_id=subscription_id, limit=limit
    )
    return [WebhookDeliveryOut.model_validate(d) for d in deliveries]
