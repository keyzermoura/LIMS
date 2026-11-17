"""Testes automatizados do Horizonte 3 — Sprint 8.2: Outbox Transacional e Webhooks Assinados (H3.2).

Conforme ESPECIFICACAO_CAMADA_INTEGRACAO_LIMS.md §4 e ALCOA+.
"""

from __future__ import annotations

import contextlib
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import httpx
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.context import RequestContext
from app.models.base import utcnow
from app.models.enums import DeviationType
from app.models.lab_test import LabTest
from app.models.outbox import IntegrationOutbox
from app.models.user import User
from app.models.webhook import WebhookDelivery, WebhookSubscription
from app.schemas.oos_investigation import OOSInvestigationCreate
from app.services import oos_service, outbox_service

API = "/api/v1"


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def login(client: AsyncClient, username: str, password: str) -> dict[str, Any]:
    res = await client.post(
        f"{API}/auth/login",
        data={"username": username, "password": password},
    )
    assert res.status_code == 200, res.text
    return res.json()


def test_webhook_hmac_sha256_signature_and_verification() -> None:
    """Valida assinatura criptográfica determinística, integridade e proteção anti-replay."""
    secret = "whsec_test_secret_key_123456"
    now_ts = int(datetime.now(UTC).timestamp())
    payload = {"report_number": "REL-2026-0001", "conclusion": "CONFORME"}
    body_str = outbox_service.canonical_json(payload)

    # 1. Assinatura e verificação com sucesso
    sig = outbox_service.sign_webhook_payload(secret, now_ts, body_str)
    assert sig.startswith("v1=")
    assert outbox_service.verify_webhook_signature(secret, now_ts, body_str, sig) is True

    # 2. Rejeição por segredo incorreto
    assert outbox_service.verify_webhook_signature("segredo_falso", now_ts, body_str, sig) is False

    # 3. Rejeição por payload adulterado
    tampered = outbox_service.canonical_json(
        {"report_number": "REL-2026-0001", "conclusion": "REPROVADO"}
    )
    assert outbox_service.verify_webhook_signature(secret, now_ts, tampered, sig) is False

    # 4. Rejeição anti-replay por carimbo expirado (> 300 s)
    expired_ts = now_ts - 301
    expired_sig = outbox_service.sign_webhook_payload(secret, expired_ts, body_str)
    assert (
        outbox_service.verify_webhook_signature(secret, expired_ts, body_str, expired_sig) is False
    )


@pytest.mark.asyncio
async def test_transactional_outbox_atomicity(
    db_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Valida atomicidade do outbox: evento só persiste se a transação for commitada."""
    event_id = uuid4()

    # 1. Transação com rollback: nada deve persistir no outbox
    async with db_factory() as db:
        await outbox_service.enqueue_event(
            db,
            event_type="test.canceled",
            aggregate_type="LabTest",
            aggregate_id=str(event_id),
            payload={"reason": "amostra degradada"},
        )
        await db.rollback()

    async with db_factory() as db:
        found = await db.scalar(
            select(IntegrationOutbox).where(IntegrationOutbox.aggregate_id == str(event_id))
        )
        assert found is None, "Evento de transação abortada não deve existir no outbox"

    # 2. Transação com commit: persiste com sucesso
    async with db_factory() as db:
        await outbox_service.enqueue_event(
            db,
            event_type="test.queued",
            aggregate_type="LabTest",
            aggregate_id=str(event_id),
            payload={"reason": "ensaio agendado"},
        )
        await db.commit()

    async with db_factory() as db:
        persisted = await db.scalar(
            select(IntegrationOutbox).where(IntegrationOutbox.aggregate_id == str(event_id))
        )
        assert persisted is not None
        assert persisted.published_at is None
        assert persisted.attempts == 0


@pytest.mark.asyncio
async def test_oos_investigation_triggers_outbox_event(
    db_factory: async_sessionmaker[AsyncSession],
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
) -> None:
    """Valida que a abertura de um desvio analítico OOS insere atomicamente o evento oos.opened no outbox."""
    login_tecnico = await login(client, "tecnico", "Tecnico@Lims2026")
    assert login_tecnico["access_token"]

    async with db_factory() as db:
        user_tecnico = await db.get(User, UUID(users["tecnico"]["id"]))
        assert user_tecnico is not None

        from app.models.device_sample import DeviceSample
        from app.models.enums import SampleStatus, TestOutcome, TestStatus

        sample = DeviceSample(
            id=uuid4(),
            accession_number=f"AMO-OOS-{uuid4().hex[:4].upper()}",
            commercial_name="Cateter Guia Hidrofílico",
            manufacturer="Inova Med Ltda",
            status=SampleStatus.EM_TESTE,
            received_at=utcnow(),
            received_by_id=user_tecnico.id,
        )
        db.add(sample)
        await db.flush()

        test = LabTest(
            id=uuid4(),
            device_sample_id=sample.id,
            name="Ensaio de pH",
            unit="pH",
            lower_limit=4.0,
            upper_limit=7.0,
            result_value=2.1,
            outcome=TestOutcome.REPROVADO,
            status=TestStatus.PENDENTE,
            tested_by_id=user_tecnico.id,
        )
        db.add(test)
        await db.commit()
        test_id = test.id

    # Cria investigação OOS via serviço
    async with db_factory() as db:
        user = await db.get(User, UUID(users["tecnico"]["id"]))
        assert user is not None
        inv = await oos_service.create_investigation(
            db,
            payload=OOSInvestigationCreate(
                lab_test_id=test_id,
                deviation_type=DeviationType.OOS,
                initial_result=2.1,
                specification_min=4.0,
                specification_max=7.0,
            ),
            actor=user,
            context=RequestContext(
                ip_address="127.0.0.1", user_agent="pytest", request_id="req-oos-test"
            ),
        )
        inv_id = str(inv.id)

    # Verifica outbox
    async with db_factory() as db:
        outbox_entry = await db.scalar(
            select(IntegrationOutbox).where(
                IntegrationOutbox.event_type == "oos.opened",
                IntegrationOutbox.aggregate_id == inv_id,
            )
        )
        assert outbox_entry is not None
        assert outbox_entry.payload["deviation_type"] == "OOS"
        assert outbox_entry.published_at is None


@pytest.mark.asyncio
async def test_outbox_dispatcher_delivers_to_subscribers(
    db_factory: async_sessionmaker[AsyncSession],
    users: dict[str, dict[str, Any]],
) -> None:
    """Valida o worker de despacho com entrega bem-sucedida, assinatura HMAC e registro de WebhookDelivery."""
    secret = "whsec_super_secret_webhook_key_2026"
    target_url = "https://erp.hospital.local/webhooks/lims"

    async with db_factory() as db:
        admin_user = await db.get(User, UUID(users["admin"]["id"]))
        assert admin_user is not None

        # Cria subscrição
        sub = WebhookSubscription(
            id=uuid4(),
            url=target_url,
            secret=secret,
            description="ERP Hospitalar Webhooks",
            events=["report.issued"],
            is_active=True,
            created_by_id=admin_user.id,
        )
        db.add(sub)

        # Cria evento no outbox
        event = await outbox_service.enqueue_event(
            db,
            event_type="report.issued",
            aggregate_type="OfficialReport",
            aggregate_id=str(uuid4()),
            payload={"report_number": "REL-2026-9999", "conclusion": "CONFORME"},
        )
        await db.commit()
        event_id = event.id

    captured_requests: list[httpx.Request] = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        return httpx.Response(200, json={"status": "received"})

    mock_transport = httpx.MockTransport(mock_handler)
    async with (
        httpx.AsyncClient(transport=mock_transport) as mock_client,
        db_factory() as db,
    ):
        dispatched = await outbox_service.dispatch_pending_outbox(db, client=mock_client)
        assert dispatched == 1

    # Validações pós-despacho
    async with db_factory() as db:
        ev = await db.get(IntegrationOutbox, event_id)
        assert ev is not None
        assert ev.published_at is not None
        assert ev.attempts == 0
        assert ev.dead_lettered_at is None

        deliveries = list(
            (
                await db.scalars(
                    select(WebhookDelivery).where(WebhookDelivery.event == "report.issued")
                )
            ).all()
        )
        assert len(deliveries) >= 1
        d = deliveries[0]
        assert d.status == "DELIVERED"
        assert d.status_code == 200

    # Valida cabeçalhos e assinatura da requisição capturada
    assert len(captured_requests) == 1
    req = captured_requests[0]
    assert req.headers["X-LIMS-Event"] == "report.issued"
    assert "X-LIMS-Delivery" in req.headers
    ts = int(req.headers["X-LIMS-Timestamp"])
    sig = req.headers["X-LIMS-Signature"]
    body_text = req.content.decode("utf-8")
    assert outbox_service.verify_webhook_signature(secret, ts, body_text, sig) is True


@pytest.mark.asyncio
async def test_outbox_exponential_backoff_and_dead_letter(
    db_factory: async_sessionmaker[AsyncSession],
    users: dict[str, dict[str, Any]],
) -> None:
    """Valida contagem de tentativas, avanço do backoff e transição para dead-letter após 12 falhas."""
    async with db_factory() as db:
        admin = await db.get(User, UUID(users["admin"]["id"]))
        assert admin is not None

        sub = WebhookSubscription(
            id=uuid4(),
            url="https://broken-qms.local/webhook",
            secret="whsec_failing_key",
            events=["report.issued"],
            is_active=True,
            created_by_id=admin.id,
        )
        db.add(sub)

        event = await outbox_service.enqueue_event(
            db,
            event_type="report.issued",
            aggregate_type="OfficialReport",
            aggregate_id=str(uuid4()),
            payload={"test": "data"},
        )
        # Simula que o evento já sofreu 11 tentativas
        event.attempts = 11
        await db.commit()
        event_id = event.id

    def failing_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="Service Unavailable")

    mock_transport = httpx.MockTransport(failing_handler)
    async with (
        httpx.AsyncClient(transport=mock_transport) as mock_client,
        db_factory() as db,
    ):
        dispatched = await outbox_service.dispatch_pending_outbox(db, client=mock_client)
        assert dispatched == 0

    # Após a 12ª falha, deve ser movido para dead-letter
    async with db_factory() as db:
        ev = await db.get(IntegrationOutbox, event_id)
        assert ev is not None
        assert ev.attempts == 12
        assert ev.dead_lettered_at is not None
        assert ev.published_at is None
        assert "HTTP 503" in (ev.last_error or "")

    # Reativação da dead-letter queue via serviço
    async with db_factory() as db:
        retried = await outbox_service.retry_dead_letter(db, outbox_id=event_id)
        assert retried.dead_lettered_at is None
        assert retried.attempts == 0
        assert retried.published_at is None


@pytest.mark.asyncio
async def test_outbox_api_endpoints(
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
    db_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Valida endpoints REST de consulta de outbox, DLQ e acionamento manual de dispatch."""
    login_admin = await login(client, "admin", "Admin@Lims2026")
    admin_headers = auth(login_admin["access_token"])

    # Cria um evento pendente e um evento em dead-letter
    async with db_factory() as db:
        await outbox_service.enqueue_event(
            db,
            event_type="test.completed",
            aggregate_type="TestExecution",
            aggregate_id=str(uuid4()),
            payload={"status": "CONCLUIDA"},
        )
        ev_dlq = await outbox_service.enqueue_event(
            db,
            event_type="test.completed",
            aggregate_type="TestExecution",
            aggregate_id=str(uuid4()),
            payload={"status": "FAILED"},
        )
        ev_dlq.dead_lettered_at = utcnow()
        ev_dlq.attempts = 12
        ev_dlq.last_error = "Timeout persistente no endpoint"
        await db.commit()
        dlq_id = str(ev_dlq.id)

    # 1. GET /api/v1/outbox/pending
    res_pending = await client.get(f"{API}/outbox/pending", headers=admin_headers)
    assert res_pending.status_code == 200
    pending_list = res_pending.json()
    assert any(e["event_type"] == "test.completed" for e in pending_list)

    # 2. GET /api/v1/outbox/dead-letter
    res_dlq = await client.get(f"{API}/outbox/dead-letter", headers=admin_headers)
    assert res_dlq.status_code == 200
    dlq_list = res_dlq.json()
    assert any(e["id"] == dlq_id for e in dlq_list)

    # 3. POST /api/v1/outbox/{id}/retry
    res_retry = await client.post(f"{API}/outbox/{dlq_id}/retry", headers=admin_headers)
    assert res_retry.status_code == 200
    retried_data = res_retry.json()
    assert retried_data["dead_lettered_at"] is None
    assert retried_data["attempts"] == 0

    # 4. POST /api/v1/outbox/dispatch
    res_dispatch = await client.post(f"{API}/outbox/dispatch", headers=admin_headers)
    assert res_dispatch.status_code == 200
    assert "dispatched_count" in res_dispatch.json()


@pytest.mark.asyncio
async def test_outbox_background_worker_lifecycle(
    db_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Valida que o worker em background processa eventos periodicamente sem intervenção humana."""
    import asyncio

    from app.core.config import settings
    from app.models.outbox import IntegrationOutbox
    from app.services.outbox_worker import start_outbox_worker

    monkeypatch.setattr(settings, "OUTBOX_POLL_INTERVAL_SECONDS", 0.05)
    monkeypatch.setattr(settings, "OUTBOX_BATCH_SIZE", 5)

    async with db_factory() as db:
        ev = await outbox_service.enqueue_event(
            db,
            event_type="sample.received",
            aggregate_type="DeviceSample",
            aggregate_id=str(uuid4()),
            payload={"action": "AUTO_WORKER_TEST"},
        )
        await db.commit()
        ev_id = ev.id

    worker_task = asyncio.create_task(start_outbox_worker(session_factory=db_factory))
    try:
        # Aguarda para o worker rodar ao menos 1 ciclo
        await asyncio.sleep(0.25)
        async with db_factory() as db:
            updated = await db.get(IntegrationOutbox, ev_id)
            assert updated is not None
            assert updated.attempts >= 1 or updated.published_at is not None
    finally:
        worker_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await worker_task
